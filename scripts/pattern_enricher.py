"""
PSA - Privacy Shield Agent
Módulo: pattern_enricher.py (v6.0 — Risk Engine, Módulo 2)

Enriquece padrões desconhecidos consultando a Claude API.
Privacy by Design: ZERO dado real é transmitido — apenas metadados
(tipo do documento e nomes de campos/padrões desconhecidos).

Fluxo:
  1. Filtra lacunas já conhecidas (docs/patterns_learned.json)
  2. Se nenhuma lacuna nova → retorna padrões conhecidos
  3. Monta prompt SEM dados reais → envia para Claude API
  4. Parseia resposta JSON
  5. Filtra: só aplica padrões com confianca >= 0.7
  6. Salva em docs/patterns_learned.json
  7. Retorna resultado com tokens gastos e custo estimado

Uso:
  from pattern_enricher import enrich_patterns
  result = enrich_patterns("medico", ["crefito", "rqe", "protocolo_atd"])
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
PATTERNS_PATH = DOCS_DIR / "patterns_learned.json"
LOGS_DIR = BASE_DIR / "logs"

DOCS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PSA-Enricher] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# Modelo e custo
MODEL = "claude-sonnet-4-20250514"
COST_PER_1K_INPUT_BRL = 0.018    # ~$3/M input  * 6 BRL/USD
COST_PER_1K_OUTPUT_BRL = 0.09    # ~$15/M output * 6 BRL/USD
CONFIDENCE_THRESHOLD = 0.7

# Tipos PSA válidos (compatíveis com anonymizer.py GENERATORS)
VALID_PSA_TYPES = {
    "name", "company", "cpf", "cnpj", "rg", "cnh", "email", "phone",
    "address", "street", "neighborhood", "city", "state", "zipcode",
    "birthdate", "age", "password", "token", "key", "process_number",
    "id_number", "account", "agency", "bank", "card", "pix",
    "salary", "amount", "coordinate", "não-sensível",
}

# ---------------------------------------------------------------------------
# Persistência: patterns_learned.json
# ---------------------------------------------------------------------------

def _load_patterns() -> Dict:
    """Carrega padrões já aprendidos do disco."""
    if PATTERNS_PATH.exists():
        try:
            with open(PATTERNS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log.warning(f"Erro ao carregar patterns_learned.json: {e}")
    return {}


def _save_patterns(patterns: Dict) -> None:
    """Salva padrões aprendidos no disco."""
    with open(PATTERNS_PATH, "w", encoding="utf-8") as f:
        json.dump(patterns, f, ensure_ascii=False, indent=2)
    log.info(f"Padrões salvos em {PATTERNS_PATH} ({len(patterns)} entradas)")


# ---------------------------------------------------------------------------
# Prompt builder — Privacy by Design
# ---------------------------------------------------------------------------

def _build_prompt(tipo_doc: str, lacunas: List[str]) -> str:
    """
    Monta o prompt para a Claude API.
    NUNCA inclui dados reais — apenas metadados (tipo + nomes de campos).
    """
    lacunas_formatted = "\n".join(f"  - {lac}" for lac in lacunas)

    return f"""Você é especialista em LGPD e proteção de dados no Brasil.
Estou processando um documento do tipo: {tipo_doc}
País: Brasil

Os seguintes padrões/campos foram encontrados mas não foram identificados pelo meu sistema local:
{lacunas_formatted}

Para cada item, responda APENAS com JSON válido, sem texto extra:
[
  {{
    "padrao": "nome_do_campo",
    "descricao": "o que é este dado",
    "regex": "expressão regular Python válida ou null",
    "sensivel": true/false,
    "base_legal": "artigo LGPD relevante ou null",
    "tipo_psa": "name|cpf|rg|email|phone|address|date|id_number|amount|salary|pix|bank|account|zipcode|não-sensível",
    "confianca": 0.0-1.0
  }}
]
Regras:
- Se não tiver certeza, coloque sensivel: false e confianca < 0.5
- Nunca invente regex sem certeza — prefira null
- tipo_psa deve ser compatível com os tipos do PSA
- confianca deve refletir sua certeza real sobre o padrão"""


# ---------------------------------------------------------------------------
# Chamada à Claude API
# ---------------------------------------------------------------------------

def _call_claude_api(prompt: str) -> Optional[Dict]:
    """
    Chama a Claude API com o prompt de enriquecimento.
    Retorna dict com 'content', 'input_tokens', 'output_tokens' ou None em erro.
    """
    try:
        import anthropic
    except ImportError:
        log.error("SDK anthropic não instalado. Execute: pip3 install anthropic")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error(
            "ANTHROPIC_API_KEY não definida. "
            "Configure com: export ANTHROPIC_API_KEY='sua-chave'"
        )
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        content = ""
        for block in message.content:
            if block.type == "text":
                content += block.text

        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens

        return {
            "content": content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    except Exception as e:
        log.error(f"Erro na chamada Claude API: {e}")
        return None


# ---------------------------------------------------------------------------
# Parser de resposta JSON
# ---------------------------------------------------------------------------

def _parse_response(raw_content: str) -> List[Dict]:
    """
    Parseia a resposta JSON da API com tratamento robusto.
    Tenta extrair array JSON mesmo que venha com texto extra.
    """
    content = raw_content.strip()

    # Tenta parse direto
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass

    # Tenta extrair JSON de bloco markdown ```json ... ```
    import re
    json_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', content, re.DOTALL)
    if json_block:
        try:
            parsed = json.loads(json_block.group(1))
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    # Tenta encontrar primeiro [ ... ] no texto
    bracket_match = re.search(r'\[.*\]', content, re.DOTALL)
    if bracket_match:
        try:
            parsed = json.loads(bracket_match.group())
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    log.warning(f"Não foi possível parsear resposta JSON da API")
    return []


# ---------------------------------------------------------------------------
# Simulação (dry-run) — testa pipeline sem chamada real
# ---------------------------------------------------------------------------

_SIMULATED_RESPONSES = {
    "crefito": {
        "padrao": "crefito",
        "descricao": "Registro profissional no Conselho Regional de Fisioterapia e Terapia Ocupacional",
        "regex": r"CREFITO[\s-]*\d{1,2}/\d{4,8}-[A-Z]",
        "sensivel": True,
        "base_legal": "Art. 5°, I LGPD — dado pessoal identificável",
        "tipo_psa": "id_number",
        "confianca": 0.95,
    },
    "rqe": {
        "padrao": "rqe",
        "descricao": "Registro de Qualificação de Especialista — número que identifica a especialidade médica do profissional",
        "regex": r"RQE[\s:]*\d{3,6}",
        "sensivel": True,
        "base_legal": "Art. 5°, I LGPD — dado pessoal identificável",
        "tipo_psa": "id_number",
        "confianca": 0.92,
    },
    "num_carteirinha_plano": {
        "padrao": "num_carteirinha_plano",
        "descricao": "Número da carteirinha do plano de saúde — identificador único do beneficiário",
        "regex": r"\d{4}\.\d{4}\.\d{4}\.\d{4}",
        "sensivel": True,
        "base_legal": "Art. 5°, II e Art. 11 LGPD — dado sensível vinculado a saúde",
        "tipo_psa": "id_number",
        "confianca": 0.90,
    },
    "protocolo_atd": {
        "padrao": "protocolo_atd",
        "descricao": "Protocolo de atendimento médico — código sequencial da consulta",
        "regex": r"ATD-\d{4}-\d{4,8}",
        "sensivel": True,
        "base_legal": "Art. 5°, I LGPD — dado pessoal identificável",
        "tipo_psa": "id_number",
        "confianca": 0.85,
    },
    "cid10": {
        "padrao": "cid10",
        "descricao": "Código da Classificação Internacional de Doenças (CID-10) — identifica diagnóstico médico",
        "regex": r"[A-Z]\d{2}(?:\.\d{1,2})?",
        "sensivel": True,
        "base_legal": "Art. 11 LGPD — dado sensível de saúde",
        "tipo_psa": "id_number",
        "confianca": 0.98,
    },
    # Padrão genérico com baixa confiança (para testar rejeição)
    "campo_desconhecido": {
        "padrao": "campo_desconhecido",
        "descricao": "Campo não identificado com certeza",
        "regex": None,
        "sensivel": False,
        "base_legal": None,
        "tipo_psa": "não-sensível",
        "confianca": 0.3,
    },
}


def _simulate_api_call(lacunas: List[str]) -> Dict:
    """
    Simula resposta da Claude API para testes.
    Retorna estrutura idêntica à chamada real.
    """
    results = []
    for lac in lacunas:
        key = _normalize_key(lac)
        if key in _SIMULATED_RESPONSES:
            results.append(_SIMULATED_RESPONSES[key])
        else:
            # Padrão genérico para lacunas não mapeadas na simulação
            results.append({
                "padrao": key,
                "descricao": f"Padrão '{key}' — necessita análise manual",
                "regex": None,
                "sensivel": False,
                "base_legal": None,
                "tipo_psa": "não-sensível",
                "confianca": 0.4,
            })

    content = json.dumps(results, ensure_ascii=False)
    # Simula tokens: ~4 chars por token
    input_tokens = 350  # prompt típico
    output_tokens = len(content) // 4

    return {
        "content": content,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def _validate_pattern(pat: Dict) -> bool:
    """Valida se um padrão retornado pela API tem os campos obrigatórios."""
    required = {"padrao", "descricao", "sensivel", "tipo_psa", "confianca"}
    if not all(k in pat for k in required):
        return False
    if not isinstance(pat.get("confianca"), (int, float)):
        return False
    if pat.get("tipo_psa") not in VALID_PSA_TYPES:
        return False
    return True


# ---------------------------------------------------------------------------
# Função principal: enrich_patterns
# ---------------------------------------------------------------------------

def enrich_patterns(
    tipo_doc: str,
    lacunas: List[str],
    dry_run: bool = False,
) -> Dict:
    """
    Enriquece padrões desconhecidos consultando a Claude API.

    Privacy by Design: ZERO dado real é transmitido.
    Apenas metadados: tipo do documento + nomes de campos/padrões.

    Args:
        tipo_doc: tipo do documento (ex: "medico", "financeiro", "cadastro")
        lacunas: lista de padrões/campos desconhecidos
                 (ex: ["crefito", "rqe", "protocolo_atd"])

    Returns:
        Dict com:
            padroes_novos: List[Dict] — padrões novos aprendidos (confianca >= 0.7)
            padroes_conhecidos: List[Dict] — padrões já existentes no cache
            padroes_rejeitados: List[Dict] — padrões com confianca < 0.7
            tokens_gastos: int — total de tokens (input + output)
            custo_estimado_brl: float — custo estimado em R$
            api_chamada: bool — se a API foi efetivamente chamada
    """
    if not lacunas:
        return {
            "padroes_novos": [],
            "padroes_conhecidos": [],
            "padroes_rejeitados": [],
            "tokens_gastos": 0,
            "custo_estimado_brl": 0.0,
            "api_chamada": False,
        }

    # --- 1. Carrega padrões conhecidos ---
    known = _load_patterns()

    # --- 2. Separa lacunas novas vs já conhecidas ---
    lacunas_novas = []
    padroes_conhecidos = []

    for lac in lacunas:
        # Normaliza: remove prefixos descritivos ("coluna '...'", "padrão ...")
        lac_key = _normalize_key(lac)
        if lac_key in known:
            padroes_conhecidos.append({
                "padrao": lac_key,
                **known[lac_key],
            })
            log.info(f"  Padrão já conhecido: '{lac_key}' → tipo_psa='{known[lac_key].get('tipo_psa')}'")
        else:
            lacunas_novas.append(lac)

    # --- 3. Se não há lacunas novas, retorna cache ---
    if not lacunas_novas:
        log.info(f"Todas as {len(lacunas)} lacunas já são conhecidas. Sem chamada à API.")
        return {
            "padroes_novos": [],
            "padroes_conhecidos": padroes_conhecidos,
            "padroes_rejeitados": [],
            "tokens_gastos": 0,
            "custo_estimado_brl": 0.0,
            "api_chamada": False,
        }

    mode_label = "SIMULAÇÃO (dry-run)" if dry_run else "Claude API"
    log.info(
        f"Enriquecendo {len(lacunas_novas)} lacuna(s) nova(s) via {mode_label} "
        f"({len(padroes_conhecidos)} já conhecida(s))"
    )

    # --- 4. Monta prompt e chama API (ou simula) ---
    if dry_run:
        api_result = _simulate_api_call(lacunas_novas)
    else:
        prompt = _build_prompt(tipo_doc, lacunas_novas)
        api_result = _call_claude_api(prompt)

    if api_result is None:
        log.warning("Chamada à API falhou — retornando apenas padrões conhecidos")
        return {
            "padroes_novos": [],
            "padroes_conhecidos": padroes_conhecidos,
            "padroes_rejeitados": [],
            "tokens_gastos": 0,
            "custo_estimado_brl": 0.0,
            "api_chamada": False,
        }

    # --- 5. Parseia resposta ---
    total_input = api_result["input_tokens"]
    total_output = api_result["output_tokens"]
    total_tokens = total_input + total_output

    custo_brl = (
        (total_input / 1000) * COST_PER_1K_INPUT_BRL
        + (total_output / 1000) * COST_PER_1K_OUTPUT_BRL
    )

    raw_patterns = _parse_response(api_result["content"])
    log.info(f"API retornou {len(raw_patterns)} padrão(ões) | {total_tokens} tokens | R$ {custo_brl:.4f}")

    # --- 6. Valida e filtra por confiança ---
    padroes_novos = []
    padroes_rejeitados = []
    today = datetime.now().strftime("%Y-%m-%d")

    for pat in raw_patterns:
        if not _validate_pattern(pat):
            log.warning(f"  Padrão inválido ignorado: {pat.get('padrao', '???')}")
            continue

        pat_key = _normalize_key(pat["padrao"])

        if pat["confianca"] >= CONFIDENCE_THRESHOLD:
            # Aceito — salva no cache
            entry = {
                "descricao": pat["descricao"],
                "regex": pat.get("regex"),
                "sensivel": pat["sensivel"],
                "base_legal": pat.get("base_legal"),
                "tipo_psa": pat["tipo_psa"],
                "confianca": pat["confianca"],
                "aprendido_em": today,
                "tipo_documento": tipo_doc,
                "tokens_gastos": total_tokens,
            }
            known[pat_key] = entry
            padroes_novos.append({"padrao": pat_key, **entry})
            log.info(
                f"  ACEITO: '{pat_key}' → tipo_psa='{pat['tipo_psa']}' "
                f"(confiança={pat['confianca']})"
            )
        else:
            padroes_rejeitados.append(pat)
            log.info(
                f"  REJEITADO: '{pat_key}' → confiança={pat['confianca']} "
                f"< threshold {CONFIDENCE_THRESHOLD}"
            )

    # --- 7. Salva padrões atualizados ---
    if padroes_novos:
        _save_patterns(known)

    return {
        "padroes_novos": padroes_novos,
        "padroes_conhecidos": padroes_conhecidos,
        "padroes_rejeitados": padroes_rejeitados,
        "tokens_gastos": total_tokens,
        "custo_estimado_brl": round(custo_brl, 4),
        "api_chamada": True,
    }


def _normalize_key(raw: str) -> str:
    """
    Normaliza uma lacuna para chave de lookup.
    Remove prefixos descritivos: "coluna 'X'" → "x", "padrão ####" → "####"
    """
    import re
    s = raw.strip().lower()
    # Remove prefixos: "coluna '...'", "header '...'", "padrão ..."
    m = re.match(r"^(?:coluna|header|campo|padrão|padrao)\s+['\"]?(.+?)['\"]?\s*$", s)
    if m:
        s = m.group(1)
    # Remove aspas restantes
    s = s.strip("'\" ")
    return s


# ---------------------------------------------------------------------------
# CLI / Teste
# ---------------------------------------------------------------------------

def main():
    """Executa teste com lacunas fictícias (apenas metadados, sem dados reais)."""
    dry_run = "--dry-run" in sys.argv or "--simulate" in sys.argv

    print("\n" + "=" * 70)
    print("PSA — PATTERN ENRICHER (Módulo 2)")
    print("Privacy by Design: ZERO dado real transmitido")
    if dry_run:
        print("*** MODO SIMULAÇÃO (dry-run) — sem chamada real à API ***")
    print("=" * 70)

    # Lacunas de teste (metadados apenas)
    tipo_doc = "medico"
    lacunas = [
        "crefito",
        "rqe",
        "num_carteirinha_plano",
        "protocolo_atd",
        "cid10",
    ]

    print(f"\n  Tipo documento: {tipo_doc}")
    print(f"  Lacunas: {lacunas}")
    print("─" * 70)

    result = enrich_patterns(tipo_doc, lacunas, dry_run=dry_run)

    print("\n" + "─" * 70)
    print("RESULTADO:")
    print("─" * 70)
    print(f"  API chamada      : {'SIM' if result['api_chamada'] else 'NÃO'}")
    print(f"  Tokens gastos    : {result['tokens_gastos']}")
    print(f"  Custo estimado   : R$ {result['custo_estimado_brl']:.4f}")
    print(f"  Padrões novos    : {len(result['padroes_novos'])}")
    print(f"  Padrões conhecidos: {len(result['padroes_conhecidos'])}")
    print(f"  Padrões rejeitados: {len(result['padroes_rejeitados'])}")

    if result["padroes_novos"]:
        print("\n  PADRÕES NOVOS APRENDIDOS:")
        for p in result["padroes_novos"]:
            print(f"    {p['padrao']:25} → tipo_psa={p['tipo_psa']:15} "
                  f"sensível={'SIM' if p['sensivel'] else 'NÃO':3} "
                  f"confiança={p['confianca']}")

    if result["padroes_conhecidos"]:
        print("\n  PADRÕES JÁ CONHECIDOS:")
        for p in result["padroes_conhecidos"]:
            print(f"    {p['padrao']:25} → tipo_psa={p['tipo_psa']:15}")

    if result["padroes_rejeitados"]:
        print("\n  PADRÕES REJEITADOS (confiança < 0.7):")
        for p in result["padroes_rejeitados"]:
            print(f"    {p.get('padrao', '???'):25} → confiança={p.get('confianca', '?')}")

    # Mostra patterns_learned.json
    if PATTERNS_PATH.exists():
        print(f"\n{'─' * 70}")
        print(f"ARQUIVO: {PATTERNS_PATH}")
        print("─" * 70)
        with open(PATTERNS_PATH, "r", encoding="utf-8") as f:
            print(f.read())

    print("=" * 70)


if __name__ == "__main__":
    main()
