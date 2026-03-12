#!/usr/bin/env python3
"""Gera PSA-Arquitetura-v6.1.pdf"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "historico" / "PSA-Arquitetura-v6.1.pdf"

BLUE = HexColor("#1a73e8")
DARK = HexColor("#202124")
GRAY_BG = HexColor("#f8f9fa")
WHITE = colors.white

def build():
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("Title2", parent=styles["Title"], fontSize=22, textColor=BLUE, spaceAfter=6))
    styles.add(ParagraphStyle("Sub", parent=styles["Normal"], fontSize=13, textColor=DARK, spaceAfter=14))
    styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, textColor=BLUE, spaceBefore=18, spaceAfter=8))
    styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, textColor=BLUE, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14, textColor=DARK))
    styles.add(ParagraphStyle("BulletPSA", parent=styles["Body"], leftIndent=20, bulletIndent=10))

    story = []
    p = lambda t, s="Body": Paragraph(t, styles[s])
    sp = lambda h=0.4: Spacer(1, h*cm)

    # Title
    story.append(p("PSA — Privacy Shield Agent for AI", "Title2"))
    story.append(p("Arquitetura v6.1 — Security Hardening + 21 Extensoes", "Sub"))
    story.append(p("Marcos Cruz — Brasilia/DF — 12/03/2026", "Body"))
    story.append(sp(1))

    # 1. Visao Geral
    story.append(p("1. Visao Geral", "H1"))
    for t in [
        "PSA e uma camada de seguranca local que intercepta e anonimiza dados sensiveis <b>antes</b> de envia-los a qualquer IA.",
        "Compativel com Claude, ChatGPT, Gemini, Llama e qualquer API de IA.",
        "v6.1: <b>21 extensoes / 18 formatos unicos</b>, score de seguranca <b>82/100</b>.",
        "Dados reais <b>nunca</b> saem do computador. A IA so ve dados ficticios.",
        "Compliance automatico: LGPD, GDPR, HIPAA, sigilo profissional.",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {t}", styles["BulletPSA"]))
    story.append(sp())

    # 2. Placar de Formatos
    story.append(p("2. Placar de Formatos — 21 Extensoes / 18 Formatos", "H1"))
    fmt_data = [
        ["#", "Formato", "Extensoes", "Script"],
        ["1", "Planilha CSV", ".csv", "anonymizer.py"],
        ["2", "Planilha Excel", ".xlsx, .xls", "anonymizer.py"],
        ["3", "Documento Word", ".docx", "anonymize_document.py"],
        ["4", "Texto puro", ".txt", "anonymize_document.py"],
        ["5", "PDF", ".pdf", "anonymize_pdf.py"],
        ["6", "Apresentacao", ".pptx", "anonymize_presentation.py"],
        ["7", "E-mail EML", ".eml", "anonymize_email.py"],
        ["8", "E-mail MSG", ".msg", "anonymize_email.py"],
        ["9", "JSON", ".json", "anonymize_json.py"],
        ["10", "XML / NF-e", ".xml", "anonymize_xml.py"],
        ["11", "RTF", ".rtf", "anonymize_rtf.py"],
        ["12", "ODT", ".odt", "anonymize_odt.py"],
        ["13", "HTML", ".html", "anonymize_html.py"],
        ["14", "YAML", ".yaml, .yml", "anonymize_yaml.py"],
        ["15", "SQL", ".sql", "anonymize_sql.py"],
        ["16", "Log", ".log", "anonymize_log.py"],
        ["17", "vCard", ".vcf", "anonymize_vcf.py"],
        ["18", "Parquet", ".parquet", "anonymize_parquet.py"],
    ]
    t = Table(fmt_data, colWidths=[1.2*cm, 4*cm, 3.5*cm, 5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GRAY_BG]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(sp())

    # 3. Seguranca
    story.append(p("3. Seguranca — Score 82/100", "H1"))
    story.append(p("5 CVEs corrigidos na v6.1: hash de integridade, audit trail, controle de mapas, anti-injection, purge de dados residuais."))
    story.append(sp(0.3))
    sec_data = [
        ["Area", "Status", "Detalhe"],
        ["Integridade de dados", "OK", "SHA256 em cada arquivo anonimizado"],
        ["Audit trail", "OK", "audit_trail.jsonl append-only"],
        ["Controle de mapas", "OK", "--no-map + --purge-maps"],
        ["Anti-vazamento", "OK", "Validacao + delecao automatica"],
        ["Anti-injection", "OK", "Validacao de nomes de arquivo"],
        ["Encoding", "OK", "Auto-deteccao multi-encoding"],
        ["RIPD automatico", "OK", "Art. 38 LGPD compliance"],
    ]
    t2 = Table(sec_data, colWidths=[4*cm, 2*cm, 8*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GRAY_BG]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t2)
    story.append(sp())

    # 4. Fluxo
    story.append(p("4. Fluxo de Dados — 19 Passos", "H1"))
    for t in [
        "16 de 19 passos rodam <b>100% local</b>.",
        "Dados reais <b>jamais</b> saem do computador.",
        "Nos 3 passos em nuvem, apenas dados ficticios sao transmitidos.",
        "Nome do arquivo protegido por codigo generico (DOC_NNN) desde o passo 1.",
        "SHA256 + audit trail registram cada operacao (v6.1).",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {t}", styles["BulletPSA"]))
    story.append(sp())

    # 5. Risk Engine
    story.append(p("5. Risk Engine v6.0", "H1"))
    for t in [
        "Classificacao automatica de risco LGPD 1-10 (Resolucao ANPD no 4/2023).",
        "3 modos de operacao: ECO (risco baixo), PADRAO (medio), MAXIMO (alto).",
        "Relatorio RIPD automatico (Art. 38 LGPD) com multa potencial estimada.",
        "Amostragem ajustada pelo risk_score — quanto maior o risco, mais dados sao processados localmente.",
    ]:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {t}", styles["BulletPSA"]))
    story.append(sp())

    # 6. Roadmap
    story.append(p("6. Roadmap", "H1"))
    road_data = [
        ["Prioridade", "Item", "Status"],
        ["1", "GPT Store (ChatGPT) — GPT customizado", "Proximo"],
        ["2", "Gemini Workspace — integracao", "Planejado"],
        ["3", "LinkedIn marketing (3 versoes)", "Rascunhos prontos"],
        ["4", "Piloto com cliente real", "Em prospeccao"],
        ["5", "Enricher com API key real", "Pendente"],
    ]
    t3 = Table(road_data, colWidths=[2.5*cm, 7*cm, 4*cm])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GRAY_BG]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t3)
    story.append(sp(1))

    story.append(p("Documento gerado automaticamente — PSA v6.1 — 12/03/2026", "Body"))

    doc.build(story)
    print(f"PDF gerado: {OUTPUT}")

if __name__ == "__main__":
    build()
