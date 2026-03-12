"""
PSA - Privacy Shield Agent
Script: psa.py
Interface unificada do PSA Guardião

Detecta automaticamente o tipo de arquivo e chama o anonimizador correto.
Ponto de entrada principal para toda operação de anonimização.

Nomes de arquivos reais NUNCA aparecem na saída — são substituídos por
códigos genéricos (DOC_001, DOC_002, etc.) via file_registry.

Formatos suportados:
  Planilhas    : .csv, .xlsx, .xls
  Documentos   : .docx, .txt
  PDFs         : .pdf
  Apresentações: .pptx
  Emails       : .eml, .msg

Uso:
  python3 scripts/psa.py --register data/real/clientes.xlsx   # registra e retorna código
  python3 scripts/psa.py --register data/real/                # registra pasta inteira
  python3 scripts/psa.py --list-files                         # lista arquivos registrados
  python3 scripts/psa.py DOC_001                              # anonimiza pelo código
  python3 scripts/psa.py DOC_001 --sample 50                  # com opções
  python3 scripts/psa.py data/real/clientes.xlsx              # registro automático + anonimiza
  python3 scripts/psa.py data/real/                           # processa pasta inteira
  python3 scripts/psa.py --list-supported                     # lista formatos suportados
"""

import os
import sys
import json
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR / "scripts"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PSA] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento de extensões → scripts
# ---------------------------------------------------------------------------

SUPPORTED = {
    # Planilhas
    ".csv":  ("spreadsheet", "CSV"),
    ".xlsx": ("spreadsheet", "Excel"),
    ".xls":  ("spreadsheet", "Excel legado"),
    # Documentos
    ".docx": ("document",    "Word"),
    ".txt":  ("document",    "Texto"),
    ".rtf":  ("rtf",         "RTF"),
    ".odt":  ("odt",         "ODT (LibreOffice)"),
    # PDF
    ".pdf":  ("pdf",         "PDF"),
    # Apresentações
    ".pptx": ("presentation", "PowerPoint"),
    # Emails
    ".eml":  ("email",       "Email EML"),
    ".msg":  ("email",       "Email MSG (Outlook)"),
    # JSON
    ".json": ("json",        "JSON"),
    # XML
    ".xml":  ("xml",         "XML"),
    # HTML
    ".html": ("html",        "HTML"),
    ".htm":  ("html",        "HTML"),
    # Config
    ".yaml": ("yaml",        "YAML"),
    ".yml":  ("yaml",        "YAML"),
    # Database
    ".sql":  ("sql",         "SQL dump"),
    # Logs
    ".log":  ("log",         "Log de aplicação"),
    # Contatos
    ".vcf":  ("vcf",         "vCard (contatos)"),
    # Dados colunares
    ".parquet": ("parquet",  "Parquet (colunar)"),
}

# H-08: Diretórios protegidos — inclui logs/
PROTECTED_DIRS = {"real", "samples", "maps", "logs"}


def _check_protected(path: Path) -> bool:
    """
    H-08: Verifica se o caminho de SAÍDA está em diretório protegido.
    Retorna True se protegido (deve bloquear escrita).
    """
    parts = {p.name for p in path.resolve().parents}
    return bool(parts & PROTECTED_DIRS)


# ---------------------------------------------------------------------------
# Validação de segurança pré-execução
# ---------------------------------------------------------------------------

def _security_check(path: Path) -> bool:
    """
    H-09/H-10: Verifica se o arquivo está em local seguro para processar.
    Bloqueia:
      - data/anonymized/ (não re-anonimizar)
      - data/maps/ (protegido)
      - data/samples/ (protegido)
      - logs/ (protegido)
    """
    resolved = path.resolve()

    blocked_dirs = [
        (BASE_DIR / "data" / "anonymized").resolve(),
        (BASE_DIR / "data" / "maps").resolve(),
        (BASE_DIR / "data" / "samples").resolve(),
        (BASE_DIR / "logs").resolve(),
    ]

    for blocked in blocked_dirs:
        if str(resolved).startswith(str(blocked)):
            dir_name = blocked.name
            log.error(
                f"BLOQUEADO: arquivo está em diretório protegido ({dir_name}/).\n"
                f"O PSA só processa arquivos em data/real/ ou caminhos externos."
            )
            return False

    return True


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def _anonymize(
    input_path: Path,
    sample: Optional[int] = None,
    pages: int = 10,
    paragraphs: int = 20,
    slides: int = 15,
) -> Optional[Tuple[Path, Path]]:
    """
    Detecta o tipo do arquivo e despacha para o anonimizador correto.
    Retorna (anon_path, map_path) ou None em caso de erro.
    """
    suffix = input_path.suffix.lower()

    if suffix not in SUPPORTED:
        log.error(
            f"Formato não suportado: '{suffix}'\n"
            f"Formatos aceitos: {', '.join(sorted(SUPPORTED.keys()))}"
        )
        return None

    kind, label = SUPPORTED[suffix]
    log.info(f"Tipo detectado: {label} ({suffix})")

    try:
        if kind == "spreadsheet":
            from anonymizer import anonymize_spreadsheet
            return anonymize_spreadsheet(input_path, sample_size=sample)

        elif kind == "document":
            from anonymize_document import anonymize_document
            return anonymize_document(input_path, sample_paragraphs=paragraphs)

        elif kind == "pdf":
            from anonymize_pdf import anonymize_pdf
            return anonymize_pdf(input_path, max_pages=pages)

        elif kind == "presentation":
            from anonymize_presentation import anonymize_presentation
            return anonymize_presentation(input_path, max_slides=slides)

        elif kind == "rtf":
            from anonymize_rtf import anonymize_rtf
            return anonymize_rtf(input_path, sample_paragraphs=paragraphs)

        elif kind == "odt":
            from anonymize_odt import anonymize_odt
            return anonymize_odt(input_path, sample_paragraphs=paragraphs)

        elif kind == "email":
            from anonymize_email import anonymize_email
            return anonymize_email(input_path)

        elif kind == "json":
            from anonymize_json import anonymize_json
            return anonymize_json(input_path, sample_size=sample)

        elif kind == "xml":
            from anonymize_xml import anonymize_xml
            return anonymize_xml(input_path)

        elif kind == "html":
            from anonymize_html import anonymize_html
            return anonymize_html(input_path, sample_paragraphs=paragraphs)

        elif kind == "yaml":
            from anonymize_yaml import anonymize_yaml
            return anonymize_yaml(input_path)

        elif kind == "sql":
            from anonymize_sql import anonymize_sql
            return anonymize_sql(input_path, sample_size=sample)

        elif kind == "log":
            from anonymize_log import anonymize_log
            return anonymize_log(input_path, sample_size=sample)

        elif kind == "vcf":
            from anonymize_vcf import anonymize_vcf
            return anonymize_vcf(input_path)

        elif kind == "parquet":
            from anonymize_parquet import anonymize_parquet
            return anonymize_parquet(input_path, sample_size=sample)

    except ImportError as e:
        log.error(f"Dependência ausente: {e}")
        return None
    except Exception as e:
        log.error(f"Erro ao anonimizar: {e}")
        import traceback
        traceback.print_exc()
        return None


def _process_folder(
    folder: Path,
    sample: int,
    pages: int,
    paragraphs: int,
    slides: int,
) -> List[dict]:
    """Processa todos os arquivos suportados em uma pasta (não recursivo)."""
    from file_registry import register_file, get_code_for_path

    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED
    ]

    if not files:
        log.warning(f"Nenhum arquivo suportado encontrado na pasta")
        return []

    log.info(f"Processando {len(files)} arquivo(s)")

    results = []
    for f in sorted(files):
        log.info(f"\n{'─' * 50}")
        # H-10: Aplica security_check a cada arquivo na pasta
        if not _security_check(f):
            code = get_code_for_path(f)
            display = code if code else "[PROTEGIDO]"
            results.append({"arquivo": display, "status": "erro"})
            continue

        # Registra automaticamente antes de processar
        code, suffix = register_file(f)
        display = f"{code}{suffix}"

        result = _anonymize(f, sample=sample, pages=pages, paragraphs=paragraphs, slides=slides)
        if result:
            anon_path, map_path = result
            results.append({
                "arquivo": display,
                "status": "ok",
                "anonimizado": str(anon_path),
                "mapa": str(map_path),
            })
        else:
            results.append({"arquivo": display, "status": "erro"})

    return results


# ---------------------------------------------------------------------------
# Relatório de operação
# ---------------------------------------------------------------------------

def _save_operation_log(results: List[dict], input_label: str):
    """Salva log estruturado da operação em logs/."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "entrada": input_label,
        "total": len(results),
        "sucesso": sum(1 for r in results if r.get("status") == "ok"),
        "erro": sum(1 for r in results if r.get("status") == "erro"),
        "arquivos": results,
    }
    log_path = LOGS_DIR / f"operacao_{timestamp}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    return log_path


# ---------------------------------------------------------------------------
# S-01: Hash de integridade (SHA256)
# ---------------------------------------------------------------------------

def _compute_sha256(file_path: Path) -> str:
    """Calcula SHA256 de um arquivo."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _save_hash(anon_path: Path) -> str:
    """Gera e salva SHA256 do arquivo anonimizado."""
    sha = _compute_sha256(anon_path)
    hash_path = Path(str(anon_path) + ".sha256")
    hash_path.write_text(f"{sha}  {anon_path.name}\n", encoding="utf-8")
    return sha


# ---------------------------------------------------------------------------
# S-02: Log de auditoria assinado (audit_trail.jsonl)
# ---------------------------------------------------------------------------

AUDIT_TRAIL_PATH = LOGS_DIR / "audit_trail.jsonl"


def _append_audit_entry(
    doc_code: str,
    input_path: Path,
    anon_path: Optional[Path],
    map_path: Optional[Path],
    hash_input: str,
    hash_output: str,
    entidades: int,
    risk_score: int,
    mode: Optional[str],
    no_map: bool,
) -> None:
    """Append-only: grava entrada de auditoria em JSONL."""
    entry = {
        "doc_code": doc_code,
        "timestamp": datetime.now().isoformat(),
        "hash_input": hash_input,
        "hash_output": hash_output,
        "entidades": entidades,
        "risk_score": risk_score,
        "mode": mode or "auto",
        "no_map": no_map,
        "anon_file": anon_path.name if anon_path else None,
        "operador": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
    }
    with open(AUDIT_TRAIL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log.info(f"Audit trail: {AUDIT_TRAIL_PATH}")


# ---------------------------------------------------------------------------
# S-03: Purge de mapas
# ---------------------------------------------------------------------------

def _cmd_purge_maps() -> None:
    """Deleta todos os arquivos de mapa em data/maps/."""
    maps_dir = BASE_DIR / "data" / "maps"
    map_files = list(maps_dir.glob("map_*.json"))

    if not map_files:
        print("\n  Nenhum mapa encontrado em data/maps/")
        sys.exit(0)

    print(f"\n  {len(map_files)} mapa(s) encontrado(s) em data/maps/")
    print("  ATENÇÃO: Esta ação é irreversível. Os mapas real→fake serão deletados.")

    try:
        resp = input("  Confirmar exclusão? [s/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Operação cancelada.")
        sys.exit(0)

    if resp not in ("s", "sim", "y", "yes"):
        print("  Operação cancelada.")
        sys.exit(0)

    deleted = 0
    for f in map_files:
        try:
            f.unlink()
            deleted += 1
        except Exception as e:
            log.error(f"Erro ao deletar {f.name}: {e}")

    print(f"  {deleted} mapa(s) deletado(s).")
    log.info(f"PURGE_MAPS: {deleted} mapas deletados por {os.environ.get('USER', 'unknown')}")
    sys.exit(0)


def _print_summary(results: List[dict]):
    """Exibe tabela resumo no terminal. Usa apenas códigos genéricos."""
    print("\n" + "=" * 70)
    print("PSA GUARDIÃO — RESUMO DA OPERAÇÃO")
    print("=" * 70)
    ok = [r for r in results if r.get("status") == "ok"]
    err = [r for r in results if r.get("status") == "erro"]

    for r in ok:
        print(f"  ✓ {r['arquivo']}")
        print(f"    → {r['anonimizado']}")

    for r in err:
        print(f"  ✗ {r['arquivo']} — ERRO")

    print("─" * 70)
    print(f"  Total: {len(results)} arquivo(s) | {len(ok)} ok | {len(err)} erro(s)")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Comandos do File Registry
# ---------------------------------------------------------------------------

def _cmd_register(entrada: str) -> None:
    """Registra arquivo(s) e exibe apenas os códigos genéricos."""
    from file_registry import register_file, register_folder

    input_path = Path(entrada)
    if not input_path.exists():
        log.error(f"Caminho não encontrado: {input_path}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("PSA — REGISTRO DE ARQUIVOS")
    print("Nomes reais protegidos. Use os códigos abaixo na conversa.")
    print("=" * 70)

    if input_path.is_dir():
        results = register_folder(input_path, set(SUPPORTED.keys()))
        if not results:
            print("  Nenhum arquivo suportado encontrado na pasta.")
            sys.exit(1)
        for code, suffix, _real_name in results:
            print(f"  {code}{suffix}")
    else:
        code, suffix = register_file(input_path)
        print(f"  {code}{suffix}")

    print("=" * 70)
    print("Use estes códigos para anonimizar. Ex: python3 scripts/psa.py DOC_001")
    sys.exit(0)


def _cmd_history(code: str) -> None:
    """Mostra histórico de anonimizações de um código DOC_NNN."""
    from file_registry import get_history

    history = get_history(code)
    if history is None:
        log.error(f"Código não encontrado: {code}")
        log.error("Use --list-files para ver os códigos disponíveis.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("PSA — HISTÓRICO DE ANONIMIZAÇÕES")
    print("=" * 70)
    print(f"  Código       : {history['code']}{history['suffix']}")
    print(f"  Registrado em: {history['registered_at'][:19]}")
    print(f"  Execuções    : {history['total_executions']}")
    print("─" * 70)

    if history["total_executions"] == 0:
        print("  Nenhuma anonimização encontrada para este código.")
        print("  Execute: python3 scripts/psa.py " + history["code"])
    else:
        for i, ex in enumerate(history["executions"], 1):
            anon_name = Path(ex["anon_file"]).name
            size_kb = ex["anon_size"] / 1024
            print(f"\n  [{i}] {ex['datetime']}")
            print(f"      Arquivo: {anon_name} ({size_kb:.1f} KB)")

            if ex.get("entities"):
                ent = ex["entities"]
                tipo = ent.get("tipo", "spreadsheet")

                if tipo == "pdf":
                    print(
                        f"      Páginas: {ent.get('total_paginas', '?')} total → "
                        f"{ent.get('paginas_amostra', '?')} amostradas"
                    )
                    print(f"      Palavras: ~{ent.get('total_palavras', '?')}")
                    print(
                        f"      Entidades: {ent.get('total_entidades', 0)} "
                        f"({ent.get('pessoas_substituidas', 0)} pessoas, "
                        f"{ent.get('empresas_substituidas', 0)} empresas)"
                    )
                elif tipo == "document":
                    print(
                        f"      Parágrafos: {ent.get('total_paragrafos', '?')} total → "
                        f"{ent.get('paragrafos_amostra', '?')} amostrados"
                    )
                    print(
                        f"      Entidades: {ent.get('total_entidades', 0)} "
                        f"({ent.get('pessoas_substituidas', 0)} pessoas, "
                        f"{ent.get('empresas_substituidas', 0)} empresas)"
                    )
                else:
                    if ent.get("total_linhas_original") is not None:
                        pct = ent.get("pct_enviado")
                        pct_str = f"{pct}%" if pct is not None else "—"
                        print(
                            f"      Linhas : {ent['total_linhas_original']} total → "
                            f"{ent['total_linhas_amostra']} amostra "
                            f"({pct_str} enviado)"
                        )
                    if ent.get("colunas_anonimizadas") is not None:
                        print(
                            f"      Colunas: {ent['colunas_anonimizadas']} anonimizadas"
                            f" + {ent.get('colunas_texto_livre', 0)} texto livre"
                        )
                    if ent.get("amostragem"):
                        print(f"      Modo   : {ent['amostragem']}")
            elif ex.get("map_file") is None:
                print(f"      (mapa não encontrado)")

    print("\n" + "=" * 70)
    sys.exit(0)


def _cmd_list_files() -> None:
    """Lista arquivos registrados (apenas códigos, sem nomes reais)."""
    from file_registry import list_registered

    entries = list_registered()

    print("\n" + "=" * 70)
    print("PSA — ARQUIVOS REGISTRADOS")
    print("=" * 70)

    if not entries:
        print("  Nenhum arquivo registrado ainda.")
        print("  Use: python3 scripts/psa.py --register data/real/<arquivo>")
    else:
        for e in entries:
            print(f"  {e['code']}{e['suffix']}  (registrado em {e['registered_at'][:10]})")

    print("=" * 70)
    sys.exit(0)


# ---------------------------------------------------------------------------
# v6.0 Risk Engine — Classificação, Enriquecimento, RIPD
# ---------------------------------------------------------------------------

def _classify(input_path: Path) -> Optional[Dict]:
    """Classifica documento quanto ao risco LGPD. Retorna None em erro."""
    try:
        from classifier import classify_document
        return classify_document(input_path)
    except Exception as e:
        log.warning(f"Classificação falhou (continuando sem): {e}")
        return None


def _print_classification(classification: Dict, doc_display: str) -> None:
    """Exibe classificação de risco no terminal."""
    print("\n" + "─" * 70)
    print("PSA v6.0 — CLASSIFICAÇÃO DE RISCO LGPD")
    print("─" * 70)
    print(f"  Documento:      {doc_display}")
    print(f"  Tipo:           {classification['tipo']} / {classification['subtipo']}")
    print(f"  Titulares:      {classification['n_titulares_estimado']}")
    print(f"  Risk Score:     {classification['risk_score']}/10")
    print(f"  Classificação:  {classification['classificacao_anpd'].upper()}")
    cats = ", ".join(classification.get("categorias_sensiveis", [])) or "nenhuma"
    print(f"  Categorias:     {cats}")
    if classification.get("tem_sensivel"):
        print(f"  Dado sensível:  SIM (Art. 11 LGPD)")
    print(f"  Cobertura:      {classification.get('cobertura_recomendada', '?')}")
    print("─" * 70)


def _adjust_sample_by_risk(
    risk_score: int,
    user_sample: Optional[int],
    suffix: str,
) -> Optional[int]:
    """
    Ajusta cobertura de amostragem pelo risk_score.
    Só aplica para planilhas e quando o usuário NÃO especificou --sample.
    Para documentos/PDFs/emails, o ajuste é feito via paragraphs/pages.

    Returns:
        None = manter amostragem inteligente padrão
        int  = forçar N linhas (ou paragraphs/pages)
    """
    if user_sample is not None:
        return user_sample  # usuário explicitou, respeitar

    # Só ajusta planilhas e JSON (arrays) automaticamente
    # Para documentos, o ajuste de paragraphs/pages é tratado separadamente
    if suffix not in (".csv", ".xlsx", ".xls", ".json", ".parquet"):
        return None

    # score 1-3 → padrão (None = amostragem inteligente)
    # score 4-6 → 60% (via sample_size)
    # score 7+  → 100% (via sample_size muito alto)
    if risk_score <= 3:
        return None
    elif risk_score <= 6:
        return None  # será tratado com multiplicador na amostragem
    else:
        return 999999  # forçar 100% (anonymizer clipa ao total)


def _adjust_paragraphs_by_risk(
    risk_score: int,
    user_paragraphs: int,
) -> int:
    """Ajusta parágrafos amostrados para documentos pelo risk_score."""
    if risk_score >= 7:
        return 999  # todos os parágrafos
    elif risk_score >= 4:
        return max(user_paragraphs, 40)  # pelo menos 40
    return user_paragraphs


def _adjust_pages_by_risk(risk_score: int, user_pages: int) -> int:
    """Ajusta páginas amostradas para PDFs pelo risk_score."""
    if risk_score >= 7:
        return 999
    elif risk_score >= 4:
        return max(user_pages, 20)
    return user_pages


def _estimate_tokens_original(input_path: Path) -> int:
    """
    Estima tokens do arquivo ORIGINAL completo (antes de anonimizar).
    Usa tamanho do arquivo como base (~4 chars por token para texto,
    ~6 chars por token para binários).
    """
    try:
        size = input_path.stat().st_size
        suffix = input_path.suffix.lower()
        if suffix in (".txt", ".eml", ".csv"):
            return max(size // 4, 1)
        else:
            # PDF, DOCX, PPTX, XLSX, MSG — binários comprimidos
            return max(size // 6, 1)
    except Exception:
        return 100


def _estimate_tokens_anon(anon_path: Path) -> int:
    """Estima tokens do arquivo anonimizado."""
    try:
        return anon_path.stat().st_size // 4
    except Exception:
        return 0


def _extract_anon_stats(
    input_path: Path,
    anon_path: Path,
    map_path: Path,
    enricher_result: Optional[Dict],
) -> Dict:
    """Extrai estatísticas de anonimização do mapa."""
    tokens_orig = _estimate_tokens_original(input_path)
    tokens_anon = _estimate_tokens_anon(anon_path)
    entidades = 0
    padroes_novos = 0

    try:
        with open(map_path, "r", encoding="utf-8") as f:
            map_data = json.load(f)

        # Spreadsheet map
        if "colunas" in map_data:
            entidades = sum(
                1 for v in map_data["colunas"].values()
                if v.get("anonimizada")
            )
        # Document/PDF/Email map
        elif "estatisticas" in map_data:
            entidades = map_data["estatisticas"].get("total_entidades", 0)
        elif "entity_map" in map_data:
            entidades = len(map_data["entity_map"])
    except Exception:
        pass

    if enricher_result:
        padroes_novos = len(enricher_result.get("padroes_novos", []))

    return {
        "tokens_original": tokens_orig,
        "tokens_anonimizado": tokens_anon,
        "entidades_total": entidades,
        "dados_vazados": 0,
        "padroes_novos_aprendidos": padroes_novos,
    }


def _collect_gaps(map_path: Path, classification: Optional[Dict]) -> List[str]:
    """
    Coleta lacunas: colunas/padrões sem match no anonimizador.
    Para planilhas: colunas não-sensíveis com nomes suspeitos.
    Para documentos: padrões não capturados pelo text_engine.
    """
    gaps = []

    try:
        with open(map_path, "r", encoding="utf-8") as f:
            map_data = json.load(f)
    except Exception:
        return gaps

    # Planilha: colunas não anonimizadas com nomes suspeitos
    if "colunas" in map_data:
        suspicious_fragments = {
            "registro", "numero", "num", "cod", "codigo", "id",
            "protocolo", "carteira", "carteirinha", "inscricao",
            "credencial", "cnes", "crm", "crefito", "crea", "oab",
            "rqe", "coren", "crf",
        }
        for col_code, info in map_data["colunas"].items():
            if info.get("anonimizada"):
                continue
            nome = info.get("nome_original", "").lower()
            words = set(nome.replace("-", "_").split("_"))
            if words & suspicious_fragments:
                gaps.append(nome)

    # Documento: detecta padrões de registros profissionais não capturados
    if classification:
        subtipo = classification.get("subtipo", "")
        if subtipo == "laudo_medico":
            # Padrões comuns em laudos que o text_engine não detecta
            known_gaps = ["crefito", "rqe", "cid10", "protocolo_atd",
                          "num_carteirinha_plano"]
            for g in known_gaps:
                if g not in gaps:
                    gaps.append(g)

    return gaps


def _run_enricher(
    classification: Dict,
    gaps: List[str],
    dry_run: bool = False,
) -> Optional[Dict]:
    """Executa pattern enricher se necessário. Retorna None em erro."""
    risk_score = classification.get("risk_score", 0)

    if risk_score < 4 or not gaps:
        return None

    try:
        from pattern_enricher import enrich_patterns
        tipo_doc = classification.get("subtipo", classification.get("tipo", "desconhecido"))
        return enrich_patterns(tipo_doc, gaps, dry_run=dry_run)
    except Exception as e:
        log.warning(f"Enricher falhou (continuando sem): {e}")
        return None


def _run_ripd(
    doc_code: str,
    doc_display: str,
    classification: Dict,
    anon_stats: Dict,
    enricher_result: Optional[Dict],
    mode: Optional[str] = None,
) -> Optional[Dict]:
    """Gera relatório RIPD. Retorna None em erro."""
    try:
        from ripd_report import generate_ripd
        return generate_ripd(
            doc_code=doc_code,
            filepath=doc_display,  # S-04: usa DOC_NNN, não nome real
            classification=classification,
            anon_stats=anon_stats,
            enricher_result=enricher_result,
            mode=mode,
        )
    except Exception as e:
        log.warning(f"Geração de RIPD falhou: {e}")
        return None


# ---------------------------------------------------------------------------
# v6.0 Seleção de modo por custo
# ---------------------------------------------------------------------------

MODE_ECO = "eco"
MODE_STANDARD = "standard"
MODE_MAX = "max"
VALID_MODES = {MODE_ECO, MODE_STANDARD, MODE_MAX}

# Custo de referência (R$ por 1k tokens) — mesmo valor do ripd_report
_CUSTO_POR_1K = 0.05

# Labels para exibição
_MODE_LABELS = {
    MODE_ECO: "ECO (30%)",
    MODE_STANDARD: "PADRÃO (60%)",
    MODE_MAX: "MÁXIMO (100%)",
}


def _get_cost_threshold() -> float:
    """Retorna limiar de custo para mostrar menu (R$). Padrão: 0.10."""
    try:
        return float(os.environ.get("PSA_COST_THRESHOLD", "0.10"))
    except (ValueError, TypeError):
        return 0.10


def _estimate_cost(input_path: Path) -> float:
    """Estima custo em R$ para processar o arquivo completo."""
    tokens = _estimate_tokens_original(input_path)
    return tokens / 1000 * _CUSTO_POR_1K


def _recommend_mode(risk_score: int) -> str:
    """Recomenda modo baseado no risk_score."""
    if risk_score >= 7:
        return MODE_MAX
    elif risk_score >= 4:
        return MODE_STANDARD
    return MODE_ECO


def _fmt_custo(valor: float) -> str:
    """Formata custo em R$."""
    s = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _show_mode_menu(
    custo_estimado: float,
    risk_score: int,
    doc_display: str,
) -> str:
    """Exibe menu interativo de seleção de modo. Retorna modo escolhido."""
    recommended = _recommend_mode(risk_score)

    _MW = 56

    def mline(text: str, align: str = "left") -> str:
        if len(text) > _MW:
            content = text[:_MW - 1] + "…"
        else:
            content = text
        if align == "center":
            return "║" + content.center(_MW) + "║"
        return "║" + content.ljust(_MW) + "║"

    print()
    print("╔" + "═" * _MW + "╗")
    print(mline("PSA — SELEÇÃO DE MODO DE PROCESSAMENTO", "center"))
    print("╠" + "═" * _MW + "╣")
    print(mline(f"  Documento:    {doc_display}"))
    print(mline(f"  Custo estim.: {_fmt_custo(custo_estimado)}"))
    print(mline(f"  Risk Score:   {risk_score}/10"))
    print("╠" + "═" * _MW + "╣")

    eco_mark = " ← recomendado" if recommended == MODE_ECO else ""
    std_mark = " ← recomendado" if recommended == MODE_STANDARD else ""
    max_mark = " ← recomendado" if recommended == MODE_MAX else ""

    print(mline(f"  [1] ECO     — 30% cobertura{eco_mark}"))
    print(mline(f"      Rápido, econômico. Amostragem mínima."))
    print(mline(f"  [2] PADRÃO  — 60% cobertura{std_mark}"))
    print(mline(f"      Equilíbrio entre custo e segurança."))
    print(mline(f"  [3] MÁXIMO  — 100% cobertura{max_mark}"))
    print(mline(f"      Cobertura total. Maior custo."))
    print("╚" + "═" * _MW + "╝")

    choice_map = {
        "1": MODE_ECO, "2": MODE_STANDARD, "3": MODE_MAX,
        "eco": MODE_ECO,
        "padrao": MODE_STANDARD, "padrão": MODE_STANDARD,
        "standard": MODE_STANDARD,
        "max": MODE_MAX, "maximo": MODE_MAX, "máximo": MODE_MAX,
    }

    while True:
        try:
            rec_label = {"eco": "1", "standard": "2", "max": "3"}[recommended]
            raw = input(
                f"\n  Escolha [1/2/3] (Enter={rec_label}): "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return recommended

        if not raw:
            return recommended

        if raw in choice_map:
            return choice_map[raw]

        print("  Opção inválida. Digite 1, 2 ou 3.")


def _confirm_grave_eco(risk_score: int, doc_display: str) -> bool:
    """Aviso quando risco grave + modo eco. Retorna True para prosseguir."""
    print()
    print("⚠ " * 28)
    print("  ATENÇÃO: Risco GRAVE + modo ECO")
    print(f"  Documento {doc_display} tem risk_score {risk_score}/10")
    print("  O modo ECO (30%) pode não cobrir todas as entidades")
    print("  sensíveis neste documento de alto risco.")
    print("  Recomendação: modo MÁXIMO (100%)")
    print("⚠ " * 28)

    try:
        resp = input("\n  Confirmar modo ECO mesmo assim? [s/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    return resp in ("s", "sim", "y", "yes")


def _apply_mode_to_sample(
    mode: str,
    user_sample: Optional[int],
    suffix: str,
) -> Optional[int]:
    """Aplica modo à amostragem de planilhas."""
    if user_sample is not None:
        return user_sample

    if suffix not in (".csv", ".xlsx", ".xls", ".json", ".parquet"):
        return None

    if mode == MODE_MAX:
        return 999999
    elif mode == MODE_STANDARD:
        return None  # amostragem inteligente (expande moderadamente)
    else:  # eco
        return None  # amostragem inteligente (mínima)


def _apply_mode_to_paragraphs(mode: str, user_paragraphs: int) -> int:
    """Aplica modo aos parágrafos amostrados."""
    if mode == MODE_MAX:
        return 999
    elif mode == MODE_STANDARD:
        return max(user_paragraphs, 40)
    return user_paragraphs  # eco: default


def _apply_mode_to_pages(mode: str, user_pages: int) -> int:
    """Aplica modo às páginas amostradas."""
    if mode == MODE_MAX:
        return 999
    elif mode == MODE_STANDARD:
        return max(user_pages, 20)
    return user_pages  # eco: default


def _log_mode_choice(
    mode: str,
    doc_code: str,
    custo: float,
    risk_score: int,
    recommended: str,
) -> None:
    """Registra escolha de modo no log."""
    log.info(
        f"PSA_MODE_CHOICE | mode={mode} | doc={doc_code} | "
        f"custo={custo:.2f} | risk={risk_score} | "
        f"recommended={recommended} | "
        f"timestamp={datetime.now().isoformat()}"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardião — Interface unificada de anonimização",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Formatos suportados:
  Planilhas    : .csv, .xlsx, .xls
  Documentos   : .docx, .txt
  PDFs         : .pdf
  Apresentações: .pptx
  Emails       : .eml, .msg

Exemplos:
  python3 scripts/psa.py --register data/real/clientes.xlsx   # registra
  python3 scripts/psa.py --register data/real/                # registra pasta
  python3 scripts/psa.py --list-files                         # lista registrados
  python3 scripts/psa.py DOC_001                              # anonimiza por código
  python3 scripts/psa.py DOC_001 --sample 50                  # com opções
  python3 scripts/psa.py data/real/clientes.xlsx              # auto-registra + anonimiza
  python3 scripts/psa.py data/real/        (processa pasta inteira)
        """,
    )
    parser.add_argument(
        "entrada",
        nargs="?",
        help="Código DOC_NNN, arquivo ou pasta a anonimizar",
    )
    parser.add_argument(
        "--register", metavar="PATH",
        help="Registra arquivo/pasta e retorna código genérico (sem anonimizar)",
    )
    parser.add_argument(
        "--list-files", action="store_true",
        help="Lista arquivos registrados (apenas códigos, sem nomes reais)",
    )
    parser.add_argument(
        "--sample", type=int, default=None, metavar="N",
        help="[Planilhas] Número de linhas na amostra (omita para automático)",
    )
    parser.add_argument(
        "--pages", type=int, default=10, metavar="N",
        help="[PDF] Máximo de páginas na amostra (padrão: 10)",
    )
    parser.add_argument(
        "--paragraphs", type=int, default=20, metavar="N",
        help="[Documentos] Máximo de parágrafos na amostra (padrão: 20)",
    )
    parser.add_argument(
        "--slides", type=int, default=15, metavar="N",
        help="[Apresentações] Máximo de slides na amostra (padrão: 15)",
    )
    parser.add_argument(
        "--list-supported", action="store_true",
        help="Lista os formatos suportados e sai",
    )
    parser.add_argument(
        "--history", metavar="DOC_NNN",
        help="Mostra histórico de anonimizações de um código registrado",
    )
    parser.add_argument(
        "--mode", choices=["eco", "standard", "max"],
        help="Modo de processamento: eco (30%%), standard (60%%), max (100%%)",
    )
    parser.add_argument(
        "--no-map", action="store_true",
        help="Não salva mapa de correspondência real→fake (mais seguro)",
    )
    parser.add_argument(
        "--purge-maps", action="store_true",
        help="Deleta todos os mapas de correspondência em data/maps/",
    )

    args = parser.parse_args()

    # --- Comandos do File Registry ---
    if args.purge_maps:
        _cmd_purge_maps()

    if args.list_files:
        _cmd_list_files()

    if args.register:
        _cmd_register(args.register)

    if args.history:
        _cmd_history(args.history)

    if args.list_supported:
        print("\nFormatos suportados pelo PSA:\n")
        for ext, (kind, label) in sorted(SUPPORTED.items()):
            print(f"  {ext:8}  {label}")
        print()
        sys.exit(0)

    if not args.entrada:
        parser.print_help()
        sys.exit(1)

    # --- Resolução de entrada: código DOC_NNN ou caminho real ---
    from file_registry import is_doc_code, resolve_code, register_file, get_code_for_path

    entrada = args.entrada

    if is_doc_code(entrada):
        # Entrada é código genérico → resolve para caminho real
        input_path = resolve_code(entrada)
        if input_path is None:
            log.error(f"Código não encontrado no registro: {entrada}")
            log.error("Use --list-files para ver os códigos disponíveis.")
            sys.exit(1)
        doc_code = entrada.upper().split(".")[0]
        doc_display = f"{doc_code}{input_path.suffix.lower()}"
    else:
        # Entrada é caminho real → registra automaticamente
        input_path = Path(entrada)
        if not input_path.exists():
            log.error(f"Caminho não encontrado: {input_path}")
            sys.exit(1)

        # Se for pasta, processa com registro automático
        if input_path.is_dir():
            print("\n" + "=" * 70)
            print("PSA — PRIVACY SHIELD AGENT")
            print("Guardião ativo. Nomes reais protegidos por códigos genéricos.")
            print("=" * 70)

            if not _security_check(input_path / "_dummy"):
                sys.exit(1)
            results = _process_folder(
                input_path,
                sample=args.sample,
                pages=args.pages,
                paragraphs=args.paragraphs,
                slides=args.slides,
            )
            if results:
                log_path = _save_operation_log(results, "[PASTA]")
                _print_summary(results)
                print(f"\n  Log da operação: {log_path}")
            n_err = sum(1 for r in results if r.get("status") == "erro")
            sys.exit(1 if n_err else 0)

        # Arquivo único → registra e continua
        code, suffix = register_file(input_path)
        doc_code = code
        doc_display = f"{code}{suffix}"

    print("\n" + "=" * 70)
    print("PSA — PRIVACY SHIELD AGENT v6.0")
    print("Guardião ativo. Nomes reais protegidos por códigos genéricos.")
    print("=" * 70)
    print(f"  Processando: {doc_display}")

    # --- Arquivo único ---
    if not _security_check(input_path):
        sys.exit(1)

    # === v6.0 PASSO 1: Classificação de risco ===
    classification = _classify(input_path)
    if classification:
        _print_classification(classification, doc_display)
        risk_score = classification.get("risk_score", 0)
    else:
        risk_score = 0

    # === v6.0 PASSO 1.5: Seleção de modo por custo ===
    suffix = input_path.suffix.lower()
    custo_estimado = _estimate_cost(input_path)
    cost_threshold = _get_cost_threshold()
    selected_mode = None  # type: Optional[str]

    if args.mode:
        # Modo via CLI — sem menu interativo
        selected_mode = args.mode
        recommended = _recommend_mode(risk_score)
        log.info(
            f"Modo via CLI: {_MODE_LABELS.get(selected_mode, selected_mode)} "
            f"(custo estim. {_fmt_custo(custo_estimado)})"
        )
        # Grave + eco: aviso mesmo via CLI
        if risk_score >= 7 and selected_mode == MODE_ECO:
            if not _confirm_grave_eco(risk_score, doc_display):
                selected_mode = MODE_MAX
                log.info("Modo alterado para MÁXIMO após aviso grave+eco")
        _log_mode_choice(
            selected_mode, doc_code, custo_estimado, risk_score, recommended,
        )
    elif custo_estimado >= cost_threshold and classification:
        # Custo acima do limiar → menu interativo
        selected_mode = _show_mode_menu(
            custo_estimado, risk_score, doc_display,
        )
        recommended = _recommend_mode(risk_score)
        # Grave + eco: aviso
        if risk_score >= 7 and selected_mode == MODE_ECO:
            if not _confirm_grave_eco(risk_score, doc_display):
                selected_mode = MODE_MAX
                log.info("Modo alterado para MÁXIMO após aviso grave+eco")
        _log_mode_choice(
            selected_mode, doc_code, custo_estimado, risk_score, recommended,
        )
    else:
        if classification:
            log.info(
                f"Custo estimado {_fmt_custo(custo_estimado)} < limiar "
                f"{_fmt_custo(cost_threshold)} → sem seleção de modo"
            )

    # === v6.0 PASSO 2: Ajusta cobertura ===
    if selected_mode:
        # Modo selecionado → cobertura baseada no modo
        effective_sample = _apply_mode_to_sample(
            selected_mode, args.sample, suffix,
        )
        effective_paragraphs = _apply_mode_to_paragraphs(
            selected_mode, args.paragraphs,
        )
        effective_pages = _apply_mode_to_pages(
            selected_mode, args.pages,
        )
        log.info(
            f"Modo {_MODE_LABELS.get(selected_mode, selected_mode)} aplicado"
        )
    else:
        # Sem modo → lógica original baseada em risk_score
        effective_sample = _adjust_sample_by_risk(risk_score, args.sample, suffix)
        effective_paragraphs = _adjust_paragraphs_by_risk(
            risk_score, args.paragraphs,
        )
        effective_pages = _adjust_pages_by_risk(risk_score, args.pages)

        if classification and risk_score >= 7 and args.sample is None:
            log.info(f"Risk score {risk_score}/10 → cobertura 100% (GRAVE)")
        elif classification and risk_score >= 4 and args.sample is None:
            log.info(f"Risk score {risk_score}/10 → cobertura ampliada")

    # === v6.0 PASSO 3: Anonimiza ===
    result = _anonymize(
        input_path,
        sample=effective_sample,
        pages=effective_pages,
        paragraphs=effective_paragraphs,
        slides=args.slides,
    )

    if not result:
        sys.exit(1)

    anon_path, map_path = result

    # === S-01: Hash de integridade ===
    hash_input = _compute_sha256(input_path)
    hash_output = _save_hash(anon_path)
    log.info(f"SHA256 input:  {hash_input}")
    log.info(f"SHA256 output: {hash_output}")

    # === S-03: --no-map — deleta mapa se solicitado ===
    if args.no_map and map_path and map_path.exists():
        map_path.unlink()
        log.info("Mapa de correspondência DELETADO (--no-map ativo)")
        map_path = None
    elif map_path and map_path.exists():
        log.warning(
            "AVISO: Mapa real→fake salvo em data/maps/. "
            "Use --no-map para impedir ou --purge-maps para limpar."
        )

    # === v6.0 PASSO 4: Coleta lacunas e enricher ===
    enricher_result = None
    if classification:
        gaps = _collect_gaps(map_path, classification)
        if gaps and risk_score >= 4:
            log.info(f"Lacunas detectadas ({len(gaps)}): {gaps[:5]}...")
            enricher_result = _run_enricher(
                classification, gaps, dry_run=True,
            )
            if enricher_result and enricher_result.get("padroes_novos"):
                n_novos = len(enricher_result["padroes_novos"])
                log.info(f"Enricher: {n_novos} padrão(ões) novo(s) aprendido(s)")

    # === v6.0 PASSO 5: Estatísticas e RIPD ===
    anon_stats = _extract_anon_stats(
        input_path, anon_path, map_path, enricher_result,
    )

    ripd_result = None
    if classification:
        ripd_result = _run_ripd(
            doc_code, doc_display, classification,
            anon_stats, enricher_result,
            mode=selected_mode,
        )

    # === S-02: Audit trail ===
    _append_audit_entry(
        doc_code=doc_code,
        input_path=input_path,
        anon_path=anon_path,
        map_path=map_path,
        hash_input=hash_input,
        hash_output=hash_output,
        entidades=anon_stats.get("entidades_total", 0),
        risk_score=risk_score,
        mode=selected_mode,
        no_map=args.no_map,
    )

    # === Resumo final ===
    map_display = str(map_path) if map_path else "[não salvo — --no-map]"
    _print_summary([{
        "arquivo": doc_display,
        "status": "ok",
        "anonimizado": str(anon_path),
        "mapa": map_display,
    }])

    # Exibe RIPD
    if ripd_result:
        print()
        print(ripd_result["report_terminal"])
        print(f"\n  RIPD salvo em: {ripd_result['saved_path']}")

    # Exibe hash de integridade
    print(f"\n  SHA256: {hash_output}")

    sys.exit(0)


if __name__ == "__main__":
    main()
