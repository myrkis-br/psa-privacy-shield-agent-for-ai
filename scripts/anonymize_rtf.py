"""
PSA - Privacy Shield Agent
Script: anonymize_rtf.py
Responsável: PSA Guardião

Anonimiza documentos RTF (Rich Text Format):
  - Extrai texto do RTF usando striprtf
  - Aplica text_engine para detectar CPF, CNPJ, nomes, emails, etc.
  - Amostragem inteligente de parágrafos (mesma lógica de anonymize_document.py)
  - Salva como TXT anonimizado em data/anonymized/
  - Salva mapa de entidades em data/maps/

Uso:
  python3 scripts/anonymize_rtf.py <caminho_do_arquivo> [--sample <n_paragrafos>]

Exemplos:
  python3 scripts/anonymize_rtf.py data/real/contrato.rtf
  python3 scripts/anonymize_rtf.py data/real/contrato.rtf --sample 30
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
# Extração de texto do RTF
# ---------------------------------------------------------------------------

def _extract_paragraphs_rtf(path: Path) -> List[Tuple[str, str]]:
    """
    Extrai parágrafos de um arquivo RTF usando striprtf.
    Fallback de encoding: utf-8 → latin-1 → cp1252.
    Retorna lista de (estilo, texto).
    """
    try:
        from striprtf.striprtf import rtf_to_text
    except ImportError:
        raise ImportError(
            "striprtf não instalado. Execute: pip3 install striprtf"
        )

    content = None
    for enc in ("utf-8", "latin-1", "cp1252", "iso-8859-1"):
        try:
            raw = path.read_text(encoding=enc)
            content = rtf_to_text(raw)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        raw = path.read_text(encoding="utf-8", errors="replace")
        content = rtf_to_text(raw)
        log.warning(f"Encoding não detectado para '{path.name}', usando UTF-8 com replace")

    # Divide em parágrafos (blocos separados por linha em branco)
    blocks = []
    current = []  # type: List[str]

    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            current.append(stripped)
        elif current:
            blocks.append(("Normal", " ".join(current)))
            current = []

    if current:
        blocks.append(("Normal", " ".join(current)))

    return blocks


# ---------------------------------------------------------------------------
# Amostragem (reutiliza lógica de anonymize_document.py)
# ---------------------------------------------------------------------------

def _sample_paragraphs(
    paragraphs: List[Tuple[str, str]],
    max_paragraphs: int,
) -> List[Tuple[str, str]]:
    """Seleciona amostra representativa de parágrafos."""
    content_indices = [
        i for i, (s, t) in enumerate(paragraphs)
        if len(t) >= 30
    ]

    if len(content_indices) <= max_paragraphs:
        return paragraphs

    n = max(max_paragraphs, 5)
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

    result = [paragraphs[i] for i in sorted(selected_indices)]
    return result[:max_paragraphs]


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def anonymize_rtf(
    input_path: Path,
    sample_paragraphs: int = 20,
) -> Tuple[Path, Path]:
    """
    Anonimiza um documento RTF.

    Args:
        input_path: Caminho para o arquivo .rtf
        sample_paragraphs: Número máximo de parágrafos na amostra

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem

    log.info(f"Iniciando anonimização RTF: {input_path.name}")

    # --- Extração ---
    paragraphs = _extract_paragraphs_rtf(input_path)
    total_paragraphs = len(paragraphs)
    log.info(f"RTF carregado: {total_paragraphs} parágrafos")

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
    lines.append("PSA - DOCUMENTO ANONIMIZADO (RTF)")
    lines.append(f"Original: {input_path.name}")
    lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append(f"Parágrafos: {len(sample)} de {total_paragraphs} (amostra)")
    lines.append("=" * 70)
    lines.append("")

    for style, text in anonymized_paragraphs:
        lines.append(text)
        lines.append("")

    output_text = "\n".join(lines)

    # --- Salvar arquivo anonimizado ---
    anon_filename = f"anon_{stem}_{timestamp}.txt"
    anon_path = ANONYMIZED_DIR / anon_filename
    anon_path.write_text(output_text, encoding="utf-8")
    log.info(f"Documento RTF anonimizado salvo: {anon_path}")

    # --- Salvar mapa ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "documento",
        "formato_original": ".rtf",
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
        description="PSA Guardião — Anonimizador de documentos RTF"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo RTF a anonimizar")
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

    anon_path, map_path = anonymize_rtf(input_path, sample_paragraphs=args.sample)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
