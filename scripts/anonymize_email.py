"""
PSA - Privacy Shield Agent
Script: anonymize_email.py
Responsável: PSA Guardião

Anonimiza emails .eml e .msg:
  - Extrai remetente, destinatários, CC, BCC, assunto, corpo e lista de anexos
  - Anonimiza todos os campos com text_engine
  - H-07: Avisa que conteúdo de anexos não é escaneado
  - .eml: usa a biblioteca padrão `email` do Python (sem dependências extras)
  - .msg: usa `extract-msg` se disponível, caso contrário instrui instalação
  - Salva como TXT anonimizado em data/anonymized/
  - Salva mapa de entidades em data/maps/

Uso:
  python3 scripts/anonymize_email.py <caminho_do_arquivo>

Exemplos:
  python3 scripts/anonymize_email.py data/real/reuniao.eml
  python3 scripts/anonymize_email.py data/real/proposta.msg
"""

import sys
import json
import email
import email.policy
import quopri
import base64
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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
# Estrutura de email extraído
# ---------------------------------------------------------------------------

class EmailData:
    def __init__(self):
        self.message_id: str = ""
        self.date: str = ""
        self.sender: str = ""
        self.reply_to: str = ""
        self.to: List[str] = []
        self.cc: List[str] = []
        self.bcc: List[str] = []
        self.subject: str = ""
        self.body_plain: str = ""
        self.body_html: str = ""
        self.attachments: List[str] = []  # apenas nomes de arquivo

    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "date": self.date,
            "sender": self.sender,
            "reply_to": self.reply_to,
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "subject": self.subject,
            "body_plain": self.body_plain,
            "body_html": self.body_html,
            "attachments": self.attachments,
        }


# ---------------------------------------------------------------------------
# Decodificação de headers de email (RFC 2047)
# ---------------------------------------------------------------------------

def _decode_header(value: Optional[str]) -> str:
    """Decodifica header de email que pode conter encoding RFC 2047."""
    if not value:
        return ""
    try:
        decoded_parts = email.header.decode_header(value)
        parts = []
        for part, enc in decoded_parts:
            if isinstance(part, bytes):
                parts.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                parts.append(str(part))
        return " ".join(parts).strip()
    except Exception:
        return str(value).strip()


def _decode_body(part) -> str:
    """Decodifica o corpo de uma parte de email."""
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except (LookupError, TypeError):
        return payload.decode("utf-8", errors="replace")


def _strip_html(html: str) -> str:
    """Remove tags HTML de forma simples (sem dependências extras)."""
    import re
    import html as html_module
    # Remove scripts e styles completos
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    html = re.sub(r'<[^>]+>', ' ', html)
    # L-05: Decodifica TODAS as entidades HTML (não apenas um subset manual)
    html = html_module.unescape(html)
    # Colapsa espaços
    html = re.sub(r'\s+', ' ', html).strip()
    return html


# ---------------------------------------------------------------------------
# Extração de .eml
# ---------------------------------------------------------------------------

def _extract_eml(path: Path) -> EmailData:
    """Extrai conteúdo de um arquivo .eml."""
    raw = path.read_bytes()

    # Tenta com a política moderna primeiro, fallback para compat
    try:
        msg = email.message_from_bytes(raw, policy=email.policy.default)
    except Exception:
        msg = email.message_from_bytes(raw)

    data = EmailData()

    data.message_id = _decode_header(msg.get("Message-ID", ""))
    data.date = _decode_header(msg.get("Date", ""))
    data.sender = _decode_header(msg.get("From", ""))
    data.reply_to = _decode_header(msg.get("Reply-To", ""))
    data.subject = _decode_header(msg.get("Subject", ""))

    # Destinatários
    for addr in _decode_header(msg.get("To", "")).split(","):
        addr = addr.strip()
        if addr:
            data.to.append(addr)

    for addr in _decode_header(msg.get("CC", "")).split(","):
        addr = addr.strip()
        if addr:
            data.cc.append(addr)

    for addr in _decode_header(msg.get("BCC", "")).split(","):
        addr = addr.strip()
        if addr:
            data.bcc.append(addr)

    # Corpo e anexos
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in disposition:
                filename = _decode_header(part.get_filename() or "")
                if filename:
                    data.attachments.append(filename)
                continue

            if ctype == "text/plain" and not data.body_plain:
                data.body_plain = _decode_body(part)
            elif ctype == "text/html" and not data.body_html:
                data.body_html = _strip_html(_decode_body(part))
    else:
        ctype = msg.get_content_type()
        if ctype == "text/plain":
            data.body_plain = _decode_body(msg)
        elif ctype == "text/html":
            html_text = _decode_body(msg)
            data.body_plain = _strip_html(html_text)
            data.body_html = html_text

    # Se tiver HTML mas não plain, usa o HTML limpo como corpo
    if not data.body_plain and data.body_html:
        data.body_plain = data.body_html

    # H-07 / M-14: Log sem PII — não exibe remetente/assunto reais
    log.info(f"  EML extraído: {len(data.to)} destinatário(s), {len(data.attachments)} anexo(s)")

    return data


# ---------------------------------------------------------------------------
# Extração de .msg (Outlook)
# ---------------------------------------------------------------------------

def _extract_msg(path: Path) -> EmailData:
    """Extrai conteúdo de um arquivo .msg (Outlook)."""
    try:
        import extract_msg
    except ImportError:
        raise ImportError(
            "Para arquivos .msg, instale: pip3 install extract-msg\n"
            "Alternativa: exporte o email como .eml no Outlook (Arquivo → Salvar como → .eml)"
        )

    data = EmailData()

    with extract_msg.Message(str(path)) as msg:
        data.date = str(msg.date or "")
        data.sender = str(msg.sender or "")
        data.subject = str(msg.subject or "")
        data.body_plain = str(msg.body or "")

        # Destinatários
        if msg.to:
            data.to = [addr.strip() for addr in msg.to.split(";") if addr.strip()]
        if msg.cc:
            data.cc = [addr.strip() for addr in msg.cc.split(";") if addr.strip()]

        # Anexos (apenas nomes)
        for att in (msg.attachments or []):
            name = getattr(att, "longFilename", None) or getattr(att, "shortFilename", "")
            if name:
                data.attachments.append(str(name))

    # M-14: Log sem PII
    log.info(f"  MSG extraído: {len(data.to)} destinatário(s), {len(data.attachments)} anexo(s)")
    return data


# ---------------------------------------------------------------------------
# Anonimização do email extraído
# ---------------------------------------------------------------------------

def _anonymize_email_data(data: EmailData, engine: TextAnonymizer) -> Dict:
    """Aplica anonimização a todos os campos do email."""

    def anon(text: str) -> str:
        return engine.anonymize(text) if text else ""

    def anon_list(lst: List[str]) -> List[str]:
        return [anon(item) for item in lst]

    return {
        "message_id": "[ID_ANONIMIZADO]",
        "date": anon(data.date),
        "remetente": anon(data.sender),
        "reply_to": anon(data.reply_to) if data.reply_to else "",
        "destinatarios": anon_list(data.to),
        "cc": anon_list(data.cc),
        "bcc": anon_list(data.bcc),
        "assunto": anon(data.subject),
        "corpo": anon(data.body_plain),
        "anexos": [
            f"[ANEXO_{i+1}_{Path(name).suffix or '.bin'}]"
            for i, name in enumerate(data.attachments)
        ],
        "total_anexos": len(data.attachments),
    }


def _format_output(anon_data: Dict, original_path: Path) -> str:
    """Formata o email anonimizado como texto legível."""
    lines = []
    lines.append("=" * 70)
    lines.append("PSA - EMAIL ANONIMIZADO")
    lines.append(f"Original: {original_path.name}")
    lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"De:       {anon_data['remetente']}")
    lines.append(f"Para:     {', '.join(anon_data['destinatarios'])}")
    if anon_data["cc"]:
        lines.append(f"CC:       {', '.join(anon_data['cc'])}")
    if anon_data["bcc"]:
        lines.append(f"BCC:      {', '.join(anon_data['bcc'])}")
    lines.append(f"Data:     {anon_data['date']}")
    lines.append(f"Assunto:  {anon_data['assunto']}")
    if anon_data["reply_to"]:
        lines.append(f"Reply-To: {anon_data['reply_to']}")
    if anon_data["anexos"]:
        lines.append(f"Anexos:   {', '.join(anon_data['anexos'])}")
        # H-07: Aviso sobre conteúdo de anexos
        lines.append("AVISO:    Conteúdo dos anexos NÃO foi escaneado pelo PSA.")
        lines.append("          Anexos podem conter dados sensíveis não anonimizados.")
    lines.append("")
    lines.append("─" * 70)
    lines.append("CORPO DO EMAIL:")
    lines.append("─" * 70)
    lines.append("")
    lines.append(anon_data["corpo"])
    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def anonymize_email(input_path: Path) -> Tuple[Path, Path]:
    """
    Anonimiza um arquivo de email .eml ou .msg.

    Args:
        input_path: Caminho para o email em data/real/

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem
    suffix = input_path.suffix.lower()

    log.info(f"Iniciando anonimização de email: {input_path.name}")

    # --- Extração ---
    if suffix == ".eml":
        data = _extract_eml(input_path)
    elif suffix == ".msg":
        try:
            data = _extract_msg(input_path)
        except Exception as e:
            # Fallback: .msg pode ser MIME salvo com extensão .msg
            log.warning(f"extract-msg falhou ({e}), tentando como MIME...")
            data = _extract_eml(input_path)
    else:
        raise ValueError(f"Formato não suportado: {suffix}. Use .eml ou .msg")

    # --- Anonimização ---
    engine = TextAnonymizer()
    anon_data = _anonymize_email_data(data, engine)

    log.info(f"Entidades substituídas: {len(engine.entity_map)} ocorrências únicas")
    # M-14: Log sem PII — mostra apenas tokens
    for i, (token, _original) in enumerate(list(engine.entity_map.items())[:5]):
        log.info(f"  Substituição #{i+1}: -> '{token}'")

    # H-07: Aviso sobre anexos
    if data.attachments:
        log.warning(
            f"  AVISO: {len(data.attachments)} anexo(s) detectado(s). "
            "O conteúdo dos anexos NÃO foi escaneado — podem conter PII."
        )

    # --- Salvar arquivo anonimizado ---
    output_text = _format_output(anon_data, input_path)
    anon_filename = f"anon_{stem}_{timestamp}.txt"
    anon_path = ANONYMIZED_DIR / anon_filename
    anon_path.write_text(output_text, encoding="utf-8")
    log.info(f"Email anonimizado salvo: {anon_path}")

    # --- Salvar mapa ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "email",
        "formato_original": suffix,
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "campos_originais": {
            "total_destinatarios": len(data.to),
            "total_cc": len(data.cc),
            "total_anexos": len(data.attachments),
            # M-14: Não salva remetente/assunto/nomes de anexo reais no mapa
        },
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
        description="PSA Guardião — Anonimizador de emails EML/MSG"
    )
    parser.add_argument("arquivo", help="Caminho para o email a anonimizar")
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() not in (".eml", ".msg"):
        log.error(f"Formato não suportado: {input_path.suffix}. Use .eml ou .msg")
        sys.exit(1)

    anon_path, map_path = anonymize_email(input_path)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
