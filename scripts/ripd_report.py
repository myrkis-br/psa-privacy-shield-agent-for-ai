"""
PSA - Privacy Shield Agent
Módulo: ripd_report.py (v6.0 — Risk Engine, Módulo 3)

Gera o Relatório de Impacto à Proteção de Dados (RIPD)
conforme Art. 38 LGPD e Resolução ANPD nº 4/2023.

Calcula:
  - Economia de tokens e custo IA
  - Multa LGPD potencial evitada (Art. 52)
  - Obrigatoriedade de RIPD (Art. 38)
  - Resumo de segurança (entidades, vazamentos, padrões)

Uso:
  from ripd_report import generate_ripd
  report = generate_ripd(doc_code, filepath, classification, anon_stats, enricher_result)
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RIPD_DIR = BASE_DIR / "docs" / "ripd"
RIPD_DIR.mkdir(parents=True, exist_ok=True)

# Custo de referência IA (R$ por 1k tokens)
CUSTO_POR_1K_TOKENS = 0.05

# Faixas de multa LGPD (Art. 52 + Resolução ANPD nº 4/2023)
_MULTA_FAIXAS = {
    "leve": ("advertência", "multa simbólica"),
    "média": ("R$ 50.000", "R$ 500.000"),
    "grave_baixo": ("R$ 500.000", "R$ 5.000.000"),
    "grave_alto": ("R$ 5.000.000", "R$ 50.000.000"),
}


# ---------------------------------------------------------------------------
# Formatação monetária BR
# ---------------------------------------------------------------------------

def _fmt_brl(valor: float) -> str:
    """Formata valor como moeda brasileira: R$ 1.234,56"""
    if valor < 0.01:
        return "R$ 0,00"
    s = f"{valor:,.2f}"
    # Troca separadores: 1,234.56 → 1.234,56
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def _fmt_int(n: int) -> str:
    """Formata inteiro com separador de milhar: 8.420"""
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Cálculos
# ---------------------------------------------------------------------------

def _calc_economia(tokens_original: int, tokens_anonimizado: int) -> Dict:
    """Calcula economia de tokens e custo."""
    if tokens_original == 0:
        return {
            "economia_pct": 0.0,
            "custo_sem_psa": 0.0,
            "custo_com_psa": 0.0,
            "economia_brl": 0.0,
        }

    economia_pct = (1 - tokens_anonimizado / tokens_original) * 100
    custo_sem = tokens_original / 1000 * CUSTO_POR_1K_TOKENS
    custo_com = tokens_anonimizado / 1000 * CUSTO_POR_1K_TOKENS
    economia_brl = custo_sem - custo_com

    return {
        "economia_pct": round(economia_pct, 1),
        "custo_sem_psa": round(custo_sem, 2),
        "custo_com_psa": round(custo_com, 2),
        "economia_brl": round(economia_brl, 2),
    }


def _calc_multa(classificacao: str, n_titulares: int) -> Dict:
    """Calcula faixa de multa potencial evitada."""
    if classificacao == "leve":
        faixa = _MULTA_FAIXAS["leve"]
        return {"min": faixa[0], "max": faixa[1], "gravidade": "leve"}
    elif classificacao == "média":
        faixa = _MULTA_FAIXAS["média"]
        return {"min": faixa[0], "max": faixa[1], "gravidade": "média"}
    else:  # grave
        if n_titulares >= 10000:
            faixa = _MULTA_FAIXAS["grave_alto"]
        else:
            faixa = _MULTA_FAIXAS["grave_baixo"]
        return {"min": faixa[0], "max": faixa[1], "gravidade": "grave"}


# ---------------------------------------------------------------------------
# Gerador de relatório visual (terminal)
# ---------------------------------------------------------------------------

_W = 58  # largura interna do box


def _box_top() -> str:
    return "╔" + "═" * _W + "╗"


def _box_mid() -> str:
    return "╠" + "═" * _W + "╣"


def _box_bot() -> str:
    return "╚" + "═" * _W + "╝"


def _box_line(text: str, align: str = "left") -> str:
    """Linha dentro do box com padding."""
    if len(text) > _W:
        content = text[:_W - 1] + "…"
    else:
        content = text
    if align == "center":
        padded = content.center(_W)
    else:
        padded = content.ljust(_W)
    return "║" + padded + "║"


def _render_report(
    doc_code: str,
    filepath: str,
    classification: Dict,
    anon_stats: Dict,
    enricher_result: Optional[Dict],
    economia: Dict,
    multa: Dict,
    mode: Optional[str] = None,
) -> str:
    """Renderiza o relatório RIPD como string formatada."""
    lines = []

    # Dados extraídos
    tipo = classification.get("tipo", "?")
    subtipo = classification.get("subtipo", "?")
    n_tit = classification.get("n_titulares_estimado", 0)
    risk_score = classification.get("risk_score", 0)
    classif = classification.get("classificacao_anpd", "?")
    categorias = classification.get("categorias_sensiveis", [])
    tem_sensivel = classification.get("tem_sensivel", False)
    ripd_obrig = risk_score >= 7

    tokens_orig = anon_stats.get("tokens_original", 0)
    tokens_anon = anon_stats.get("tokens_anonimizado", 0)
    entidades = anon_stats.get("entidades_total", 0)
    vazados = anon_stats.get("dados_vazados", 0)
    padroes_novos = anon_stats.get("padroes_novos_aprendidos", 0)

    # Cabeçalho
    lines.append(_box_top())
    lines.append(_box_line("PSA — RELATÓRIO DE PROTEÇÃO DE DADOS", "center"))
    lines.append(_box_line("Resolução ANPD nº 4/2023", "center"))

    # Documento
    lines.append(_box_mid())
    lines.append(_box_line(" DOCUMENTO"))
    lines.append(_box_line(f"  Código:        {doc_code}"))
    lines.append(_box_line(f"  Arquivo:       {filepath}"))
    lines.append(_box_line(f"  Tipo:          {tipo} / {subtipo}"))
    lines.append(_box_line(f"  Titulares:     {_fmt_int(n_tit)} pessoas"))
    if mode:
        _mode_labels = {
            "eco": "ECO (30%)", "standard": "PADRÃO (60%)", "max": "MÁXIMO (100%)",
        }
        lines.append(_box_line(
            f"  Modo:          {_mode_labels.get(mode, mode)}"
        ))

    # Risco LGPD
    lines.append(_box_mid())
    lines.append(_box_line(" RISCO LGPD"))
    lines.append(_box_line(f"  Score:         {risk_score}/10"))
    lines.append(_box_line(f"  Classificação: {classif.upper()}"))
    cats_str = ", ".join(categorias) if categorias else "nenhuma"
    lines.append(_box_line(f"  Categorias:    {cats_str}"))
    if tem_sensivel:
        lines.append(_box_line(f"  Dado sensível: SIM (Art. 11 LGPD)"))
    ripd_str = "SIM (Art. 38 LGPD)" if ripd_obrig else "Não"
    lines.append(_box_line(f"  RIPD obrig.:   {ripd_str}"))

    # Economia
    lines.append(_box_mid())
    lines.append(_box_line(" ECONOMIA"))
    eco_pct = economia["economia_pct"]
    lines.append(_box_line(
        f"  Tokens sem PSA: {_fmt_int(tokens_orig):>7}  →  "
        f"com PSA: {_fmt_int(tokens_anon):>5} (-{eco_pct:.0f}%)"
    ))
    lines.append(_box_line(
        f"  Custo sem PSA: {_fmt_brl(economia['custo_sem_psa']):>8}  →  "
        f"com PSA: {_fmt_brl(economia['custo_com_psa'])}"
    ))
    lines.append(_box_line(
        f"  Economia:      {_fmt_brl(economia['economia_brl']):>8}  por documento"
    ))

    # Segurança
    lines.append(_box_mid())
    lines.append(_box_line(" SEGURANÇA"))
    lines.append(_box_line(f"  Entidades anonimizadas:  {entidades}"))
    vaz_str = "ZERO ✓" if vazados == 0 else f"{vazados} ⚠ ATENÇÃO"
    lines.append(_box_line(f"  Dados vazados:           {vaz_str}"))
    lines.append(_box_line(f"  Padrões aprendidos:      {padroes_novos}"))

    # Enricher (se chamado)
    if enricher_result and enricher_result.get("api_chamada"):
        tokens_api = enricher_result.get("tokens_gastos", 0)
        custo_api = enricher_result.get("custo_estimado_brl", 0)
        lines.append(_box_line(
            f"  Enricher API:            {tokens_api} tokens "
            f"({_fmt_brl(custo_api)})"
        ))

    # Proteção financeira
    lines.append(_box_mid())
    lines.append(_box_line(" PROTEÇÃO FINANCEIRA"))
    if multa["gravidade"] == "leve":
        lines.append(_box_line(
            f"  Multa potencial evitada: {multa['min']} a {multa['max']}"
        ))
    else:
        lines.append(_box_line(
            f"  Multa potencial evitada: {multa['min']} – {multa['max']}"
        ))
    lines.append(_box_line(
        f"  Base legal:   Art. 52 LGPD + Res. ANPD nº 4/2023"
    ))

    lines.append(_box_bot())

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gerador de relatório texto (para salvar em arquivo)
# ---------------------------------------------------------------------------

def _render_report_txt(
    doc_code: str,
    filepath: str,
    classification: Dict,
    anon_stats: Dict,
    enricher_result: Optional[Dict],
    economia: Dict,
    multa: Dict,
    mode: Optional[str] = None,
) -> str:
    """Renderiza relatório RIPD completo para salvamento em arquivo."""
    now = datetime.now()

    tipo = classification.get("tipo", "?")
    subtipo = classification.get("subtipo", "?")
    n_tit = classification.get("n_titulares_estimado", 0)
    risk_score = classification.get("risk_score", 0)
    classif = classification.get("classificacao_anpd", "?")
    categorias = classification.get("categorias_sensiveis", [])
    tem_sensivel = classification.get("tem_sensivel", False)
    justificativa = classification.get("justificativa", "")
    cobertura = classification.get("cobertura_recomendada", "")
    ripd_obrig = risk_score >= 7

    tokens_orig = anon_stats.get("tokens_original", 0)
    tokens_anon = anon_stats.get("tokens_anonimizado", 0)
    entidades = anon_stats.get("entidades_total", 0)
    vazados = anon_stats.get("dados_vazados", 0)
    padroes_novos = anon_stats.get("padroes_novos_aprendidos", 0)

    eco_pct = economia["economia_pct"]

    lines = [
        "=" * 60,
        "RELATÓRIO DE IMPACTO À PROTEÇÃO DE DADOS PESSOAIS (RIPD)",
        "PSA — Privacy Shield Agent v6.0",
        f"Gerado em: {now.strftime('%d/%m/%Y %H:%M:%S')}",
        "Base legal: Art. 38 LGPD + Resolução ANPD nº 4/2023",
        "=" * 60,
        "",
        "1. IDENTIFICAÇÃO DO DOCUMENTO",
        "-" * 40,
        f"   Código PSA:        {doc_code}",
        f"   Arquivo:           {filepath}",
        f"   Tipo:              {tipo}",
        f"   Subtipo:           {subtipo}",
        f"   Titulares estim.:  {_fmt_int(n_tit)} pessoas",
    ]

    if mode:
        _mode_labels_txt = {
            "eco": "ECO (30%)", "standard": "PADRÃO (60%)", "max": "MÁXIMO (100%)",
        }
        lines.append(
            f"   Modo processo.:    {_mode_labels_txt.get(mode, mode)}"
        )

    lines.extend([
        "",
        "2. CLASSIFICAÇÃO DE RISCO",
        "-" * 40,
        f"   Risk Score:        {risk_score}/10",
        f"   Classificação:     {classif.upper()}",
        f"   Dado sensível:     {'SIM (Art. 11 LGPD)' if tem_sensivel else 'NÃO'}",
        f"   Categorias:        {', '.join(categorias) if categorias else 'nenhuma'}",
        f"   RIPD obrigatório:  {'SIM (Art. 38 LGPD)' if ripd_obrig else 'NÃO'}",
        f"   Cobertura:         {cobertura}",
        f"   Justificativa:     {justificativa}",
        "",
        "3. ECONOMIA E EFICIÊNCIA",
        "-" * 40,
        f"   Tokens originais:  {_fmt_int(tokens_orig)}",
        f"   Tokens anonimiz.:  {_fmt_int(tokens_anon)}",
        f"   Economia:          {eco_pct:.1f}%",
        f"   Custo sem PSA:     {_fmt_brl(economia['custo_sem_psa'])}",
        f"   Custo com PSA:     {_fmt_brl(economia['custo_com_psa'])}",
        f"   Economia por doc:  {_fmt_brl(economia['economia_brl'])}",
        "",
        "4. SEGURANÇA DA ANONIMIZAÇÃO",
        "-" * 40,
        f"   Entidades anon.:   {entidades}",
        f"   Dados vazados:     {vazados} {'✓ SEGURO' if vazados == 0 else '⚠ ATENÇÃO'}",
        f"   Padrões novos:     {padroes_novos}",
    ])

    if enricher_result and enricher_result.get("api_chamada"):
        lines.extend([
            f"   Enricher tokens:   {enricher_result.get('tokens_gastos', 0)}",
            f"   Enricher custo:    {_fmt_brl(enricher_result.get('custo_estimado_brl', 0))}",
        ])
        if enricher_result.get("padroes_novos"):
            lines.append("   Padrões aprendidos:")
            for p in enricher_result["padroes_novos"]:
                lines.append(
                    f"     - {p['padrao']}: {p.get('descricao', '')} "
                    f"(tipo_psa={p.get('tipo_psa', '?')}, "
                    f"confiança={p.get('confianca', '?')})"
                )

    multa_str = (
        f"{multa['min']} a {multa['max']}"
        if multa["gravidade"] == "leve"
        else f"{multa['min']} – {multa['max']}"
    )

    lines.extend([
        "",
        "5. PROTEÇÃO FINANCEIRA",
        "-" * 40,
        f"   Classificação:     {multa['gravidade'].upper()}",
        f"   Multa evitada:     {multa_str}",
        f"   Base legal:        Art. 52 LGPD + Res. ANPD nº 4/2023",
        "",
        "6. CONCLUSÃO",
        "-" * 40,
    ])

    if risk_score >= 7:
        lines.extend([
            "   Este documento apresenta RISCO GRAVE à proteção de dados",
            "   pessoais. A elaboração deste RIPD é OBRIGATÓRIA conforme",
            "   Art. 38 da LGPD. Recomenda-se:",
            "   - Notificar o encarregado de dados (DPO)",
            "   - Implementar anonimização completa antes de qualquer",
            "     processamento externo",
            "   - Manter registro deste relatório por 5 anos",
        ])
    elif risk_score >= 4:
        lines.extend([
            "   Este documento apresenta RISCO MÉDIO à proteção de dados",
            "   pessoais. Recomenda-se anonimização completa e a",
            "   elaboração de RIPD como boa prática.",
        ])
    else:
        lines.extend([
            "   Este documento apresenta RISCO LEVE à proteção de dados",
            "   pessoais. Anonimização padrão é suficiente.",
        ])

    lines.extend([
        "",
        "=" * 60,
        "PSA — Privacy Shield Agent v6.0",
        "Este relatório foi gerado automaticamente e não substitui",
        "a análise do encarregado de proteção de dados (DPO).",
        "=" * 60,
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Função principal: generate_ripd
# ---------------------------------------------------------------------------

def generate_ripd(
    doc_code: str,
    filepath: str,
    classification: Dict,
    anon_stats: Dict,
    enricher_result: Optional[Dict] = None,
    mode: Optional[str] = None,
) -> Dict:
    """
    Gera o Relatório de Impacto à Proteção de Dados (RIPD).

    Args:
        doc_code: código genérico (ex: "DOC_016")
        filepath: nome do arquivo original
        classification: retorno do classifier.classify_document()
        anon_stats: dict com tokens_original, tokens_anonimizado,
                    entidades_total, dados_vazados, padroes_novos_aprendidos
        enricher_result: retorno do pattern_enricher.enrich_patterns()
                         ou None se não foi chamado

    Returns:
        Dict com:
            report_terminal: str — relatório formatado para terminal
            report_txt: str — relatório completo para arquivo
            saved_path: Path — caminho do arquivo salvo
            economia: Dict — detalhes da economia calculada
            multa: Dict — faixa de multa potencial
            ripd_obrigatorio: bool
    """
    # Cálculos
    economia = _calc_economia(
        anon_stats.get("tokens_original", 0),
        anon_stats.get("tokens_anonimizado", 0),
    )
    multa = _calc_multa(
        classification.get("classificacao_anpd", "leve"),
        classification.get("n_titulares_estimado", 0),
    )
    ripd_obrig = classification.get("risk_score", 0) >= 7

    # Renderiza relatórios
    report_terminal = _render_report(
        doc_code, filepath, classification, anon_stats,
        enricher_result, economia, multa, mode=mode,
    )
    report_txt = _render_report_txt(
        doc_code, filepath, classification, anon_stats,
        enricher_result, economia, multa, mode=mode,
    )

    # Salva arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"RIPD_{doc_code}_{timestamp}.txt"
    saved_path = RIPD_DIR / filename
    with open(saved_path, "w", encoding="utf-8") as f:
        f.write(report_txt)

    return {
        "report_terminal": report_terminal,
        "report_txt": report_txt,
        "saved_path": saved_path,
        "economia": economia,
        "multa": multa,
        "ripd_obrigatorio": ripd_obrig,
    }


# ---------------------------------------------------------------------------
# CLI / Teste
# ---------------------------------------------------------------------------

def main():
    """Testa geração de RIPD com dados mock dos 3 documentos."""
    sys.path.insert(0, str(BASE_DIR / "scripts"))

    # Importa classifier para obter classificação real
    from classifier import classify_document
    from file_registry import resolve_code

    test_cases = [
        {
            "doc_code": "DOC_016",
            "anon_stats": {
                "tokens_original": 8420,
                "tokens_anonimizado": 312,
                "entidades_total": 42,
                "dados_vazados": 0,
                "padroes_novos_aprendidos": 0,
            },
        },
        {
            "doc_code": "DOC_017",
            "anon_stats": {
                "tokens_original": 95000,
                "tokens_anonimizado": 4200,
                "entidades_total": 180,
                "dados_vazados": 0,
                "padroes_novos_aprendidos": 0,
            },
        },
        {
            "doc_code": "DOC_019",
            "anon_stats": {
                "tokens_original": 6800,
                "tokens_anonimizado": 890,
                "entidades_total": 42,
                "dados_vazados": 0,
                "padroes_novos_aprendidos": 2,
            },
            "enricher_result": {
                "padroes_novos": [
                    {"padrao": "crefito", "descricao": "Registro CREFITO",
                     "tipo_psa": "id_number", "confianca": 0.95},
                    {"padrao": "rqe", "descricao": "Registro RQE",
                     "tipo_psa": "id_number", "confianca": 0.92},
                ],
                "padroes_conhecidos": [],
                "padroes_rejeitados": [],
                "tokens_gastos": 713,
                "custo_estimado_brl": 0.039,
                "api_chamada": True,
            },
        },
    ]

    for tc in test_cases:
        code = tc["doc_code"]
        real_path = resolve_code(code)

        if real_path is None:
            print(f"\n⚠ {code} não encontrado no registro. Pulando.")
            continue

        # Classificação real
        classification = classify_document(real_path)

        # Gera RIPD
        result = generate_ripd(
            doc_code=code,
            filepath=real_path.name,
            classification=classification,
            anon_stats=tc["anon_stats"],
            enricher_result=tc.get("enricher_result"),
        )

        # Mostra no terminal
        print()
        print(result["report_terminal"])
        print(f"\n  Salvo em: {result['saved_path']}")
        print()

    # Lista arquivos salvos
    print("\n" + "=" * 56)
    print("ARQUIVOS RIPD SALVOS:")
    print("=" * 56)
    for f in sorted(RIPD_DIR.iterdir()):
        if f.name.startswith("RIPD_"):
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name} ({size_kb:.1f} KB)")
    print("=" * 56)


if __name__ == "__main__":
    main()
