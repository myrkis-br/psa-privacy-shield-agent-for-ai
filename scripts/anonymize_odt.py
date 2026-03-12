"""
PSA - Privacy Shield Agent
Script: anonymize_odt.py
Responsável: PSA Guardião

Anonimiza documentos ODT (OpenDocument Text / LibreOffice Writer):
  - Extrai texto do ODT via odfpy (lê content.xml do ZIP)
  - Aplica text_engine para detectar CPF, CNPJ, nomes, emails, etc.
  - Amostragem inteligente de parágrafos
  - Salva como TXT anonimizado em data/anonymized/
  - Salva mapa de entidades em data/maps/

Uso:
  python3 scripts/anonymize_odt.py <caminho_do_arquivo> [--sample <n_paragrafos>]

Exemplos:
  python3 scripts/anonymize_odt.py data/real/laudo.odt
  python3 scripts/anonymize_odt.py data/real/laudo.odt --sample 30
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Configuração de caminhos
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ANONYMIZED_DIR = BASE_DIR / "data" / "anonymized"
MAPS_DIR = BASE_DIR / "data" / "maps"
LOGS_DIR = BASE_DIR / "logs"

for d in (ANONYMIZED_DIR, MAPS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR / "scripts"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PSA-Guardião] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

from text_engine import TextAnonymizer

# ---------------------------------------------------------------------------
# Extração de texto do ODT
# ---------------------------------------------------------------------------

def _extract_text_from_element(element) -> str:
    """Extrai texto recursivamente de um elemento ODF, incluindo filhos."""
    parts = []
    if hasattr(element, 'childNodes'):
        for child in element.childNodes:
            if hasattr(child, 'data'):
                # Nó de texto
                parts.append(child.data)
            elif hasattr(child, 'qname'):
                tag = child.qname[1] if isinstance(child.qname, tuple) else str(child.qname)
                # <text:s/> = espaço, <text:tab/> = tab, <text:line-break/> = quebra
                if tag == 's':
                    count = int(child.getAttribute('c') or '1')
                    parts.append(' ' * count)
                elif tag == 'tab':
                    parts.append('\t')
                elif tag == 'line-break':
                    parts.append('\n')
                else:
                    # Recursa em spans, links, etc.
                    parts.append(_extract_text_from_element(child))
    return ''.join(parts)


def _extract_paragraphs_odt(path: Path) -> List[Tuple[str, str]]:
    """
    Extrai parágrafos de um arquivo ODT usando odfpy.
    Retorna lista de (estilo, texto).
    """
    try:
        from odf.opendocument import load
        from odf import text as odf_text
        from odf.namespaces import TEXTNS
    except ImportError:
        raise ImportError(
            "odfpy não instalado. Execute: pip3 install odfpy"
        )

    doc = load(str(path))
    paragraphs = []

    # Itera sobre todos os elementos do corpo do texto
    body = doc.text
    for elem in body.childNodes:
        if not hasattr(elem, 'qname'):
            continue

        tag = elem.qname[1] if isinstance(elem.qname, tuple) else str(elem.qname)

        if tag == 'h':
            # Heading
            text = _extract_text_from_element(elem).strip()
            if text:
                level = elem.getAttribute('outlinelevel') or '1'
                paragraphs.append((f"Heading {level}", text))

        elif tag == 'p':
            # Paragraph
            text = _extract_text_from_element(elem).strip()
            if text:
                style = elem.getAttribute('stylename') or 'Normal'
                paragraphs.append((str(style), text))

        elif tag == 'table':
            # Table — extrai texto de cada célula
            for row_elem in elem.childNodes:
                if not hasattr(row_elem, 'qname'):
                    continue
                row_tag = row_elem.qname[1] if isinstance(row_elem.qname, tuple) else str(row_elem.qname)
                if row_tag == 'table-row':
                    cells = []
                    for cell_elem in row_elem.childNodes:
                        if not hasattr(cell_elem, 'qname'):
                            continue
                        cell_text = _extract_text_from_element(cell_elem).strip()
                        if cell_text:
                            cells.append(cell_text)
                    if cells:
                        paragraphs.append(("Table", " | ".join(cells)))

    return paragraphs


# ---------------------------------------------------------------------------
# Amostragem (mesma lógica de anonymize_document.py)
# ---------------------------------------------------------------------------

def _sample_paragraphs(
    paragraphs: List[Tuple[str, str]],
    max_paragraphs: int,
) -> List[Tuple[str, str]]:
    """Seleciona amostra representativa de parágrafos."""
    heading_indices = {
        i for i, (s, _) in enumerate(paragraphs)
        if "heading" in s.lower() or "título" in s.lower()
    }
    content_indices = [
        i for i, (s, t) in enumerate(paragraphs)
        if len(t) >= 30 and i not in heading_indices
    ]

    if len(content_indices) <= max_paragraphs:
        return paragraphs

    n = max(max_paragraphs - len(heading_indices), 5)
    n_start = int(n * 0.4)
    n_mid = int(n * 0.4)
    n_end = n - n_start - n_mid

    mid_start = len(content_indices) // 2 - n_mid // 2
    mid_end = mid_start + n_mid

    selected_indices = set(
        content_indices[:n_start]
        + content_indices[mid_start:mid_end]
        + content_indices[-n_end:]
    )
    selected_indices |= heading_indices

    result = [paragraphs[i] for i in sorted(selected_indices)]
    return result[:max_paragraphs + len(heading_indices)]


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def anonymize_odt(
    input_path: Path,
    sample_paragraphs: int = 20,
) -> Tuple[Path, Path]:
    """
    Anonimiza um documento ODT.

    Args:
        input_path: Caminho para o arquivo .odt
        sample_paragraphs: Número máximo de parágrafos na amostra

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem

    log.info(f"Iniciando anonimização ODT: {input_path.name}")

    # --- Extração ---
    paragraphs = _extract_paragraphs_odt(input_path)
    total_paragraphs = len(paragraphs)
    log.info(f"ODT carregado: {total_paragraphs} parágrafos")

    # --- Amostragem ---
    sample = _sample_paragraphs(paragraphs, sample_paragraphs)
    log.info(f"Amostra selecionada: {len(sample)} de {total_paragraphs} parágrafos")

    # --- Anonimização ---
    engine = TextAnonymizer()
    anonymized_paragraphs = []

    for style, text in sample:
        anon_text = engine.anonymize(text)
        anonymized_paragraphs.append((style, anon_text))

    log.info(f"Entidades substituídas: {len(engine.entity_map)} ocorrências únicas")

    for i, (token, _original) in enumerate(list(engine.entity_map.items())[:5]):
        log.info(f"  Substituição #{i+1}: -> '{token}'")

    # --- Montar texto de saída ---
    lines = []
    lines.append("=" * 70)
    lines.append("PSA - DOCUMENTO ANONIMIZADO (ODT)")
    lines.append(f"Original: {input_path.name}")
    lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append(f"Parágrafos: {len(sample)} de {total_paragraphs} (amostra)")
    lines.append("=" * 70)
    lines.append("")

    for style, text in anonymized_paragraphs:
        if "heading" in style.lower():
            lines.append(f"\n## {text}\n")
        elif style == "Table":
            lines.append(f"[TABELA] {text}")
        else:
            lines.append(text)
            lines.append("")

    output_text = "\n".join(lines)

    # --- Salvar arquivo anonimizado ---
    anon_filename = f"anon_{stem}_{timestamp}.txt"
    anon_path = ANONYMIZED_DIR / anon_filename
    anon_path.write_text(output_text, encoding="utf-8")
    log.info(f"Documento ODT anonimizado salvo: {anon_path}")

    # --- Salvar mapa ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "documento",
        "formato_original": ".odt",
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "total_paragrafos_original": total_paragraphs,
        "total_paragrafos_amostra": len(sample),
        "entidades": {
            token: original
            for token, original in engine.entity_map.items()
        },
        "estatisticas": {
            "pessoas_substituidas": engine._counters["pessoa"],
            "empresas_substituidas": engine._counters["empresa"],
            "total_entidades": len(engine.entity_map),
        },
    }

    map_filename = f"map_{stem}_{timestamp}.json"
    map_path = MAPS_DIR / map_filename
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    log.info(f"Mapa salvo: {map_path}")
    log.info(
        f"Anonimização concluída: {engine._counters['pessoa']} pessoas, "
        f"{engine._counters['empresa']} empresas substituídas."
    )

    return anon_path, map_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardião — Anonimizador de documentos ODT"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo ODT a anonimizar")
    parser.add_argument(
        "--sample",
        type=int,
        default=20,
        metavar="N",
        help="Número máximo de parágrafos na amostra (padrão: 20)",
    )
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    anon_path, map_path = anonymize_odt(input_path, sample_paragraphs=args.sample)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
