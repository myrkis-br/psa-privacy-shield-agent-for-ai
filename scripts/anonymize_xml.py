"""
PSA - Privacy Shield Agent
Script: anonymize_xml.py

Anonimiza arquivos XML — NF-e, NFS-e, CT-e, e outros documentos fiscais.

Funcionalidades:
  - Travessia recursiva de elementos XML (ElementTree)
  - Suporte a namespaces (nfeProc, NFe, etc.)
  - Detecção de tags sensíveis pelo nome do elemento
  - Cache de consistência (mesmo valor → mesmo valor fake)
  - text_engine para campos de texto livre (infCpl, xMotivo)
  - Preserva IDs técnicos (chNFe, nNF, nProt, cProd, NCM, CFOP)
  - Validação anti-vazamento (C-01)

Tags anonimizadas:
  CPF, CNPJ, xNome, xFant, xLgr, nro, xBairro, xMun, CEP,
  email, fone, IE, xEnder, xCpl

Tags preservadas (IDs técnicos / estrutura fiscal):
  chNFe, nNF, nProt, Id, cProd, cEAN, NCM, CFOP, cStat, nFat, nDup,
  mod, serie, cUF, cMun, cMunFG, cPais, UF, natOp, verProc, verAplic

Uso:
  from anonymize_xml import anonymize_xml
  anon_path, map_path = anonymize_xml(Path("data/real/nfe.xml"))
"""

import os
import json
import random
import logging
import xml.etree.ElementTree as ET
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
# Detecção de tags sensíveis
# ---------------------------------------------------------------------------

# Tag → tipo de dado sensível
_SENSITIVE_TAGS = {
    "CPF": "cpf",
    "CNPJ": "cnpj",
    "xNome": "name",
    "xFant": "name",
    "xLgr": "street",
    "nro": "street_number",
    "xCpl": "complement",
    "xBairro": "neighborhood",
    "xMun": "city",
    "CEP": "cep",
    "email": "email",
    "fone": "phone",
    "IE": "ie",
    "xEnder": "full_address",
}
# xPais preservado (sempre "Brasil" em NF-e doméstica, não é PII)

# Tags que são IDs técnicos / estruturais — NUNCA anonimizar
_PRESERVE_TAGS = {
    "chNFe", "nNF", "nProt", "cProd", "cEAN", "cEANTrib",
    "NCM", "CFOP", "cStat", "nFat", "nDup",
    "mod", "serie", "cUF", "cNF", "cMun", "cMunFG", "cPais",
    "UF", "natOp", "verProc", "verAplic", "tpAmb", "tpNF",
    "idDest", "tpImp", "tpEmis", "cDV", "finNFe", "indFinal",
    "indPres", "procEmi", "indIEDest", "CRT", "modFrete",
    "orig", "CST", "modBC", "indTot", "digVal",
    "dhEmi", "dhRecbto", "dVenc",
    # Produto / imposto: valores numéricos
    "qCom", "vUnCom", "vProd", "qTrib", "vUnTrib",
    "vBC", "pICMS", "vICMS", "pPIS", "vPIS", "pCOFINS", "vCOFINS",
    "vICMSDeson", "vFCPUFDest", "vICMSUFDest", "vICMSUFRemet",
    "vFCP", "vBCST", "vST", "vFrete", "vSeg", "vDesc",
    "vII", "vIPI", "vIPIDevol", "vOutro", "vNF",
    "vOrig", "vLiq", "vDup",
    # Volume
    "qVol", "esp", "marca", "pesoL", "pesoB",
    # Produto info
    "xProd", "uCom", "uTrib",
    # Motivo (será tratado pelo text_engine)
    "xMotivo",
    # Informações complementares (será tratado pelo text_engine)
    "infCpl",
}

# Tags que contêm texto livre → escanear com text_engine
_TEXT_TAGS = {"infCpl", "xMotivo", "xObs", "obsCont", "obsFisco"}


def _strip_ns(tag: str) -> str:
    """Remove namespace de uma tag XML: {http://...}tagName → tagName."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _detect_tag_type(tag: str) -> Optional[str]:
    """Retorna tipo sensível pela tag, ou None se preservar/ignorar."""
    local = _strip_ns(tag)
    if local in _PRESERVE_TAGS:
        return None
    return _SENSITIVE_TAGS.get(local)


def _is_text_tag(tag: str) -> bool:
    """Verifica se a tag contém texto livre que precisa de text_engine."""
    return _strip_ns(tag) in _TEXT_TAGS


# ---------------------------------------------------------------------------
# Anonimizador XML
# ---------------------------------------------------------------------------

class _XmlAnonymizer:
    """Motor de anonimização para XML."""

    def __init__(self):
        seed = int.from_bytes(os.urandom(4), "big")
        Faker.seed(seed)
        random.seed(seed)
        self.fake = Faker("pt_BR")

        self._cache = {}  # type: Dict[str, str]
        self._entities = {}  # type: Dict[str, int]
        self._fields = set()  # type: Set[str]
        self._text_anon = None

    def _get_text_engine(self):
        if self._text_anon is None:
            try:
                from text_engine import TextAnonymizer
                self._text_anon = TextAnonymizer()
            except ImportError:
                pass
        return self._text_anon

    def _generate(self, tipo: str, value: str) -> str:
        """Gera valor fake para o tipo sensível."""
        cache_key = f"{tipo}:{value}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = value  # fallback

        if tipo == "cpf":
            result = self.fake.cpf()
        elif tipo == "cnpj":
            result = self.fake.cnpj()
        elif tipo == "name":
            result = self.fake.name() if len(value) > 10 else self.fake.company()
        elif tipo == "street":
            result = self.fake.street_name()
        elif tipo == "street_number":
            result = str(self.fake.random_int(min=1, max=9999))
        elif tipo == "complement":
            options = ["Sala 101", "Bloco B", "Apt 302", "Galpão 5", "Andar 8"]
            result = random.choice(options)
        elif tipo == "neighborhood":
            result = self.fake.bairro()
        elif tipo == "city":
            result = self.fake.city()
        elif tipo == "cep":
            result = self.fake.postcode()
        elif tipo == "email":
            result = self.fake.email()
        elif tipo == "phone":
            # Preserva formato numérico (sem pontuação)
            digits = self.fake.msisdn()[:len(value)] if value.isdigit() else self.fake.phone_number()
            result = digits
        elif tipo == "ie":
            # Inscrição Estadual: gera número com mesma estrutura
            result = ".".join(
                str(self.fake.random_int(min=100, max=999))
                for _ in range(3)
            ) + "." + str(self.fake.random_int(min=100, max=999))
        elif tipo == "full_address":
            result = self.fake.address().replace("\n", ", ")
        elif tipo == "country":
            result = value  # preserva "Brasil"

        self._cache[cache_key] = result
        self._entities[tipo] = self._entities.get(tipo, 0) + 1

        return result

    def _scan_text(self, text: str) -> str:
        """Escaneia texto livre com text_engine + substituição de nomes cacheados."""
        result = text

        # 1) text_engine para padrões gerais (CPF, telefone, etc.)
        ta = self._get_text_engine()
        if ta is not None:
            try:
                result = ta.anonymize(result)
            except Exception:
                pass

        # 2) Substitui nomes/valores já cacheados que aparecem no texto
        # Ordena por tamanho desc para evitar substituição parcial
        for cache_key, fake_val in sorted(
            self._cache.items(), key=lambda x: -len(x[0])
        ):
            tipo, real_val = cache_key.split(":", 1)
            if tipo in ("name", "cnpj", "cpf", "email", "phone") and real_val in result:
                result = result.replace(real_val, fake_val)

        if result != text:
            self._entities["text_engine"] = (
                self._entities.get("text_engine", 0) + 1
            )

        return result

    def walk(self, element: ET.Element) -> None:
        """Percorre e anonimiza elementos XML in-place."""
        local_tag = _strip_ns(element.tag)

        # Verifica se este elemento tem texto
        if element.text and element.text.strip():
            text = element.text.strip()

            # Tag de texto livre → text_engine
            if _is_text_tag(element.tag):
                element.text = self._scan_text(text)
                self._fields.add(f"{local_tag} (text_engine)")
            else:
                # Verifica se a tag é sensível
                tipo = _detect_tag_type(element.tag)
                if tipo:
                    element.text = self._generate(tipo, text)
                    self._fields.add(local_tag)

        # Recursão nos filhos
        for child in element:
            self.walk(child)

    def get_stats(self) -> Dict:
        """Retorna estatísticas de anonimização."""
        return {
            "tipo": "xml",
            "total_entidades": sum(self._entities.values()),
            "entidades_por_tipo": dict(self._entities),
            "campos_anonimizados": sorted(self._fields),
        }


# ---------------------------------------------------------------------------
# Validação anti-vazamento (C-01)
# ---------------------------------------------------------------------------

def _collect_sensitive_values(element: ET.Element) -> Set[str]:
    """Coleta todos os valores sensíveis do XML original."""
    values = set()  # type: Set[str]

    if element.text and element.text.strip():
        tipo = _detect_tag_type(element.tag)
        text = element.text.strip()
        if tipo and len(text) >= 6:
            values.add(text)

    for child in element:
        values |= _collect_sensitive_values(child)

    return values


def _validate_no_leakage(
    original_values: Set[str],
    anon_tree: ET.ElementTree,
    anon_path: Path,
) -> bool:
    """C-01: Verifica se dados reais não vazaram."""
    anon_text = ET.tostring(anon_tree.getroot(), encoding="unicode")
    leaked = []
    for val in original_values:
        if val in anon_text:
            leaked.append(val[:30] + "..." if len(val) > 30 else val)

    if leaked:
        log.error(
            f"VAZAMENTO DETECTADO! {len(leaked)} valor(es) real(is) "
            f"encontrado(s) no XML anonimizado."
        )
        if anon_path.exists():
            anon_path.unlink()
            log.error(f"Arquivo anonimizado DELETADO: {anon_path}")
        return False

    return True


# ---------------------------------------------------------------------------
# Função principal: anonymize_xml
# ---------------------------------------------------------------------------

def anonymize_xml(
    input_path: Path,
    sample_size: Optional[int] = None,
) -> Optional[Tuple[Path, Path]]:
    """
    Anonimiza arquivo XML.

    Args:
        input_path: caminho do arquivo XML original
        sample_size: não usado para XML (mantido para compatibilidade)

    Returns:
        (anon_path, map_path) ou None em caso de erro
    """
    log.info(f"Iniciando anonimização XML: {input_path.name}")

    # Carrega XML
    try:
        tree = ET.parse(input_path)
    except ET.ParseError as e:
        log.error(f"Erro ao parsear XML: {e}")
        return None

    root = tree.getroot()

    # Detecta namespace
    ns = ""
    if "}" in root.tag:
        ns = root.tag.split("}")[0] + "}"
        log.info(f"Namespace detectado: {ns[1:-1]}")

    # Coleta valores sensíveis ANTES de anonimizar
    sensitive_values = _collect_sensitive_values(root)

    # Anonimiza
    anonymizer = _XmlAnonymizer()
    anonymizer.walk(root)

    stats = anonymizer.get_stats()
    log.info(
        f"XML: {stats['total_entidades']} entidades em "
        f"{len(stats['campos_anonimizados'])} campos"
    )

    # Gera nomes de saída
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem
    anon_name = f"anon_{stem}_{timestamp}.xml"
    map_name = f"map_{stem}_{timestamp}.json"
    anon_path = ANON_DIR / anon_name
    map_path = MAPS_DIR / map_name

    # Salva XML anonimizado
    tree.write(str(anon_path), encoding="utf-8", xml_declaration=True)

    # Validação C-01
    if not _validate_no_leakage(sensitive_values, tree, anon_path):
        raise RuntimeError("LeakageError: dados reais detectados no XML anonimizado")

    # Salva mapa
    map_data = {
        "arquivo_original": input_path.name,
        "arquivo_anonimizado": anon_name,
        "timestamp": datetime.now().isoformat(),
        "namespace": ns[1:-1] if ns else None,
        "estatisticas": stats,
        "entity_map": anonymizer._cache,
    }
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    log.info(f"Anonimizado: {anon_path.name}")

    return anon_path, map_path
