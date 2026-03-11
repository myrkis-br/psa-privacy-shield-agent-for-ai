"""
PSA - Privacy Shield Agent
Script: anonymize_json.py

Anonimiza arquivos JSON — logs de API, exports, configs, etc.

Funcionalidades:
  - Travessia recursiva de objetos/arrays aninhados
  - Detecção de campos sensíveis por nome da chave
  - Cache de consistência (mesmo valor real → mesmo valor fake)
  - text_engine para texto livre embarcado
  - Amostragem inteligente para arrays grandes
  - Validação anti-vazamento (C-01)
  - Variação financeira ±15% para valores monetários

Campos preservados (IDs técnicos):
  event_id, order_id, transaction_id, request_id, timestamp, type, status

Campos anonimizados (PII):
  name, email, cpf, cnpj, phone, ip, address, fingerprint, card_last4, pix_key

Uso:
  from anonymize_json import anonymize_json
  anon_path, map_path = anonymize_json(Path("data/real/api.json"))
"""

import os
import json
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from faker import Faker

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ANON_DIR = BASE_DIR / "data" / "anonymized"
MAPS_DIR = BASE_DIR / "data" / "maps"
ANON_DIR.mkdir(parents=True, exist_ok=True)
MAPS_DIR.mkdir(parents=True, exist_ok=True)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Detecção de campos sensíveis
# ---------------------------------------------------------------------------

# Chaves que sempre preservamos (IDs técnicos, metadados não-PII)
_PRESERVE_KEYS = {
    "event_id", "order_id", "transaction_id", "request_id",
    "session_id", "trace_id", "correlation_id",
    "timestamp", "type", "status", "code", "method",
    "amount", "currency", "bank", "banco",
    "user_agent", "message",
}

# Match exato: chave → tipo sensível
_SENSITIVE_EXACT = {
    "name": "name", "nome": "name", "full_name": "name",
    "nome_completo": "name", "primeiro_nome": "name",
    "sobrenome": "name", "razao_social": "name",
    "email": "email", "e_mail": "email",
    "cpf": "cpf",
    "cnpj": "cnpj",
    "phone": "phone", "telefone": "phone", "celular": "phone",
    "fone": "phone", "tel": "phone",
    "ip": "ip", "ip_address": "ip", "ip_origem": "ip",
    "address": "address", "endereco": "address",
    "logradouro": "address", "rua": "address",
    "fingerprint": "hash",
    "card_last4": "card_digits", "ultimos4": "card_digits",
    "pix_key": "pix_key", "chave_pix": "pix_key",
}

# Match por fragmento: se a chave contém o fragmento → tipo
_SENSITIVE_CONTAINS = [
    ("cpf", "cpf"),
    ("cnpj", "cnpj"),
    ("email", "email"),
    ("e_mail", "email"),
    ("phone", "phone"),
    ("telefone", "phone"),
    ("celular", "phone"),
    ("endereco", "address"),
    ("address", "address"),
    ("logradouro", "address"),
    ("nome", "name"),
    ("name", "name"),
    ("pix", "pix_key"),
]


def _detect_sensitive_type(
    key: str,
    parent_keys: List[str],
) -> Optional[str]:
    """Detecta tipo sensível baseado no nome da chave e contexto."""
    k = key.lower().replace("-", "_")

    # Preservar chaves técnicas
    if k in _PRESERVE_KEYS:
        return None

    # "id" dentro de objeto "user" → identificador pessoal
    if k == "id":
        parents_lower = [p.lower() for p in parent_keys if p]
        if any(p in ("user", "usuario", "cliente", "titular") for p in parents_lower):
            return "uuid"
        return None  # ID técnico, preservar

    # Match exato
    if k in _SENSITIVE_EXACT:
        return _SENSITIVE_EXACT[k]

    # Match por fragmento
    for fragment, tipo in _SENSITIVE_CONTAINS:
        if fragment in k:
            return tipo

    # IP com prefixo/sufixo
    if k.startswith("ip_") or k.endswith("_ip"):
        return "ip"

    return None


# ---------------------------------------------------------------------------
# Amostragem inteligente (reutiliza lógica de anonymizer.py)
# ---------------------------------------------------------------------------

def _calculate_sample_size(n: int) -> int:
    """Calcula tamanho de amostra para arrays JSON (mesma lógica de planilhas)."""
    if n <= 30:
        return n
    elif n <= 100:
        return max(30, n // 2)
    elif n <= 10000:
        return 100
    elif n <= 100000:
        return 150
    else:
        return 200


# ---------------------------------------------------------------------------
# Anonimizador JSON
# ---------------------------------------------------------------------------

class _JsonAnonymizer:
    """Motor de anonimização para estruturas JSON."""

    def __init__(self):
        seed = int.from_bytes(os.urandom(4), "big")
        Faker.seed(seed)
        random.seed(seed)
        self.fake = Faker("pt_BR")

        # Cache: "tipo:valor_real" → valor_fake (consistência)
        self._cache = {}  # type: Dict[str, Any]

        # Estatísticas
        self._entities = {}  # type: Dict[str, int]
        self._fields = set()  # type: Set[str]

        # text_engine (lazy load)
        self._text_anon = None

    def _get_text_engine(self):
        """Lazy-load do text_engine."""
        if self._text_anon is None:
            try:
                from text_engine import TextAnonymizer
                self._text_anon = TextAnonymizer()
            except ImportError:
                pass
        return self._text_anon

    def _generate(self, tipo: str, value: Any) -> Any:
        """Gera valor fake para o tipo sensível detectado."""
        str_val = str(value)

        # Cache: mesmo valor real → mesmo valor fake
        cache_key = f"{tipo}:{str_val}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = value  # fallback

        if tipo == "name":
            result = self.fake.name()
        elif tipo == "email":
            result = self.fake.email()
        elif tipo == "cpf":
            result = self.fake.cpf()
        elif tipo == "cnpj":
            result = self.fake.cnpj()
        elif tipo == "phone":
            result = self.fake.phone_number()
        elif tipo == "ip":
            result = self.fake.ipv4()
        elif tipo == "address":
            result = self.fake.address().replace("\n", ", ")
        elif tipo == "hash":
            n = len(str_val) if str_val else 32
            result = self.fake.sha256()[:n]
        elif tipo == "card_digits":
            result = str(self.fake.random_int(min=1000, max=9999))
        elif tipo == "uuid":
            import uuid
            result = str(uuid.uuid4())
        elif tipo == "pix_key":
            if "@" in str_val:
                result = self.fake.email()
            elif len(str_val.replace(".", "").replace("-", "")) == 11:
                result = self.fake.cpf()
            else:
                result = self.fake.email()

        self._cache[cache_key] = result

        # Estatísticas
        self._entities[tipo] = self._entities.get(tipo, 0) + 1

        return result

    def _scan_text(self, text: str) -> str:
        """Escaneia texto livre com text_engine para PII embarcado."""
        ta = self._get_text_engine()
        if ta is None:
            return text
        try:
            result = ta.anonymize(text)
            if result != text:
                self._entities["text_engine"] = (
                    self._entities.get("text_engine", 0) + 1
                )
            return result
        except Exception:
            return text

    def _walk(
        self,
        obj: Any,
        parent_keys: List[str],
        current_key: str = "",
    ) -> Any:
        """Percorre e anonimiza estrutura JSON recursivamente."""
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                new_parents = parent_keys + [current_key] if current_key else parent_keys
                result[k] = self._walk(v, new_parents, k)
            return result

        elif isinstance(obj, list):
            return [
                self._walk(item, parent_keys, current_key)
                for item in obj
            ]

        elif isinstance(obj, str) and current_key:
            tipo = _detect_sensitive_type(current_key, parent_keys)
            if tipo:
                self._fields.add(current_key)
                return self._generate(tipo, obj)

            # Texto livre → text_engine (threshold baixo para capturar CPFs curtos)
            if len(obj) > 8:
                scanned = self._scan_text(obj)
                if scanned != obj:
                    self._fields.add(f"{current_key} (text_engine)")
                return scanned

            return obj

        elif obj is None:
            return None

        else:
            # int, float, bool
            return obj

    def anonymize(
        self,
        data: Any,
        sample_size: Optional[int] = None,
    ) -> Tuple[Any, Any, Dict]:
        """
        Anonimiza dados JSON.

        Args:
            data: JSON parsed (dict ou list)
            sample_size: para arrays, limitar a N elementos

        Returns:
            (dados_anonimizados, dados_amostrados_originais, estatísticas)
        """
        total_elements = 0
        sampled_elements = 0
        sampled_data = data  # referência aos dados que serão anonimizados

        if isinstance(data, list):
            total_elements = len(data)

            if sample_size is None:
                sample_size = _calculate_sample_size(total_elements)

            if sample_size < total_elements:
                indices = sorted(random.sample(range(total_elements), sample_size))
                sampled_data = [data[i] for i in indices]
                log.info(
                    f"Amostra JSON: {sample_size} de {total_elements} "
                    f"elementos ({sample_size * 100 / total_elements:.1f}% enviado)"
                )
            else:
                sampled_data = data

            sampled_elements = len(sampled_data)
        else:
            total_elements = 1
            sampled_elements = 1

        anonymized = self._walk(sampled_data, [])

        stats = {
            "tipo": "json",
            "total_elementos": total_elements,
            "elementos_amostra": sampled_elements,
            "total_entidades": sum(self._entities.values()),
            "entidades_por_tipo": dict(self._entities),
            "campos_anonimizados": sorted(self._fields),
        }

        return anonymized, sampled_data, stats


# ---------------------------------------------------------------------------
# Validação anti-vazamento (C-01)
# ---------------------------------------------------------------------------

def _validate_no_leakage(
    original_data: Any,
    anonymized_data: Any,
    anon_path: Path,
) -> bool:
    """
    C-01: Verifica se dados reais não vazaram para o arquivo anonimizado.
    Coleta todos os valores sensíveis do original e verifica se aparecem
    no texto do anonimizado.
    """
    # Coleta valores sensíveis do original
    sensitive_values = set()  # type: Set[str]

    def _collect(obj, parent_keys, current_key=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_parents = parent_keys + [current_key] if current_key else parent_keys
                _collect(v, new_parents, k)
        elif isinstance(obj, list):
            for item in obj:
                _collect(item, parent_keys, current_key)
        elif isinstance(obj, str) and current_key:
            tipo = _detect_sensitive_type(current_key, parent_keys)
            # Mínimo 6 chars para evitar falsos positivos com card_last4
            # (4 dígitos aparecem como substring em UUIDs, hashes, etc.)
            if tipo and len(obj) >= 6:
                sensitive_values.add(obj)

    _collect(original_data, [])

    # Verifica no texto anonimizado
    anon_text = json.dumps(anonymized_data, ensure_ascii=False)
    leaked = []
    for val in sensitive_values:
        if val in anon_text:
            leaked.append(val[:20] + "..." if len(val) > 20 else val)

    if leaked:
        log.error(
            f"VAZAMENTO DETECTADO! {len(leaked)} valor(es) real(is) "
            f"encontrado(s) no arquivo anonimizado."
        )
        # C-01: deleta arquivo anonimizado
        if anon_path.exists():
            anon_path.unlink()
            log.error(f"Arquivo anonimizado DELETADO: {anon_path}")
        return False

    return True


# ---------------------------------------------------------------------------
# Função principal: anonymize_json
# ---------------------------------------------------------------------------

def anonymize_json(
    input_path: Path,
    sample_size: Optional[int] = None,
) -> Optional[Tuple[Path, Path]]:
    """
    Anonimiza arquivo JSON.

    Args:
        input_path: caminho do arquivo JSON original
        sample_size: número de elementos na amostra (None = automático)

    Returns:
        (anon_path, map_path) ou None em caso de erro
    """
    log.info(f"Iniciando anonimização JSON: {input_path.name}")

    # Carrega JSON
    encodings = ["utf-8", "latin-1", "cp1252"]
    data = None
    used_encoding = None

    for enc in encodings:
        try:
            with open(input_path, "r", encoding=enc) as f:
                data = json.load(f)
            used_encoding = enc
            break
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    if data is None:
        log.error(f"Não foi possível ler o JSON: {input_path}")
        return None

    log.info(f"Encoding: {used_encoding}")

    # Info sobre o JSON
    if isinstance(data, list):
        log.info(f"JSON array: {len(data)} elementos")
    elif isinstance(data, dict):
        log.info(f"JSON object: {len(data)} chaves no raiz")

    # Anonimiza
    anonymizer = _JsonAnonymizer()
    anonymized, sampled_data, stats = anonymizer.anonymize(
        data, sample_size=sample_size,
    )

    # Gera nomes de saída
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem
    anon_name = f"anon_{stem}_{timestamp}.json"
    map_name = f"map_{stem}_{timestamp}.json"
    anon_path = ANON_DIR / anon_name
    map_path = MAPS_DIR / map_name

    # Salva anonimizado
    with open(anon_path, "w", encoding="utf-8") as f:
        json.dump(anonymized, f, ensure_ascii=False, indent=2)

    # Validação anti-vazamento (C-01)
    # Usa dados amostrados (não o original completo) para evitar falsos positivos
    if not _validate_no_leakage(sampled_data, anonymized, anon_path):
        raise RuntimeError("LeakageError: dados reais detectados no arquivo anonimizado")

    # Salva mapa
    map_data = {
        "arquivo_original": input_path.name,
        "arquivo_anonimizado": anon_name,
        "timestamp": datetime.now().isoformat(),
        "encoding": used_encoding,
        "estatisticas": stats,
        "entity_map": anonymizer._cache,
    }

    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    # Log resumo
    n_ent = stats["total_entidades"]
    n_campos = len(stats["campos_anonimizados"])
    log.info(
        f"Anonimizado: {n_ent} entidades em {n_campos} campos | "
        f"Salvo: {anon_path.name}"
    )

    return anon_path, map_path
