"""
PSA - Privacy Shield Agent
Script: anonymizer.py
Responsável: PSA Guardião

Anonimiza planilhas CSV e XLSX:
  - Detecta automaticamente colunas sensíveis
  - Substitui dados reais por dados sintéticos (Faker)
  - Aplica text_engine em colunas de texto livre (C-02)
  - Renomeia colunas para códigos genéricos (COL_A, COL_B, ...)
  - Valida e BLOQUEIA saída em caso de vazamento (C-01)
  - Salva arquivo anonimizado em data/anonymized/
  - Salva mapa de correspondência em data/maps/

Uso:
  python3 scripts/anonymizer.py <caminho_do_arquivo> [--sample <n_linhas>]

Exemplos:
  python3 scripts/anonymizer.py data/real/clientes.xlsx
  python3 scripts/anonymizer.py data/real/folha.csv --sample 50
"""

import os
import sys
import json
import re
import string
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ANONYMIZED_DIR = BASE_DIR / "data" / "anonymized"
MAPS_DIR = BASE_DIR / "data" / "maps"
LOGS_DIR = BASE_DIR / "logs"

for d in (ANONYMIZED_DIR, MAPS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PSA-Guardião] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

fake = Faker("pt_BR")
# Seed aleatório baseado em entropia do SO (não determinístico)
Faker.seed(int.from_bytes(os.urandom(8), "big"))

sys.path.insert(0, str(BASE_DIR / "scripts"))

# ---------------------------------------------------------------------------
# Detecção de colunas sensíveis
# ---------------------------------------------------------------------------

# H-02: Keywords expandidas com documentos, financeiros e familiares
SENSITIVE_KEYWORDS: Dict[str, str] = {
    "nome":          "name",
    "name":          "name",
    "nome_mae":      "name",
    "nome_pai":      "name",
    "mae":           "name",
    "pai":           "name",
    "razao":         "company",
    "empresa":       "company",
    "company":       "company",
    "fantasia":      "company",
    "cpf":           "cpf",
    "cnpj":          "cnpj",
    "rg":            "rg",
    "cnh":           "cnh",
    "titulo_eleitor":"id_number",
    "titulo":        "id_number",
    "pis":           "id_number",
    "pasep":         "id_number",
    "nis":           "id_number",
    "nit":           "id_number",
    "ctps":          "id_number",
    "sus":           "id_number",
    "passaporte":    "id_number",
    "email":         "email",
    "e-mail":        "email",
    "mail":          "email",
    "telefone":      "phone",
    "celular":       "phone",
    "fone":          "phone",
    "phone":         "phone",
    "tel":           "phone",
    "endereco":      "address",
    "endereço":      "address",
    "address":       "address",
    "logradouro":    "address",
    "rua":           "street",
    "avenida":       "street",
    "bairro":        "neighborhood",
    "cidade":        "city",
    "municipio":     "city",
    "estado":        "state",
    "uf":            "state",
    "cep":           "zipcode",
    "salario":       "salary",
    "salário":       "salary",
    "salary":        "salary",
    "remuneracao":   "salary",
    "remuneração":   "salary",
    "vencimento":    "salary",
    "bruto":         "salary",
    "liquido":       "salary",
    "líquido":       "salary",
    "valor":         "amount",
    "amount":        "amount",
    "receita":       "amount",
    "faturamento":   "amount",
    "despesa":       "amount",
    "custo":         "amount",
    "debito":        "amount",
    "credito":       "amount",
    "saldo":         "amount",
    "desconto":      "amount",
    "gratificacao":  "amount",
    "adicional":     "amount",
    "abono":         "amount",
    "auxilio":       "amount",
    "subsidio":      "amount",
    "conta":         "account",
    "agencia":       "agency",
    "agência":       "agency",
    "banco":         "bank",
    "cartao":        "card",
    "cartão":        "card",
    "pix":           "pix",
    "chave_pix":     "pix",
    "chavepix":      "pix",
    "nascimento":    "birthdate",
    "nasc":          "birthdate",
    "birthdate":     "birthdate",
    "birth":         "birthdate",
    "idade":         "age",
    "age":           "age",
    "senha":         "password",
    "password":      "password",
    "token":         "token",
    "chave":         "key",
    "processo":      "process_number",
    "matricula":     "id_number",
    "matrícula":     "id_number",
    "carteirinha":   "id_number",
    "carteira":      "id_number",
    "registro":      "id_number",
    "inscricao":     "id_number",
    "inscrição":     "id_number",
    "gestor":        "name",
    "responsavel":   "name",
    "responsável":   "name",
    "supervisor":    "name",
    "coordenador":   "name",
    "gerente":       "name",
    "diretor":       "name",
    "placa":         "id_number",
    "chassi":        "id_number",
    "renavam":       "id_number",
    "latitude":      "coordinate",
    "longitude":     "coordinate",
    "lat":           "coordinate",
    "lng":           "coordinate",
    "lon":           "coordinate",
}

# H-02: Keywords curtas que exigem match exato (não parcial)
_SHORT_EXACT_KEYWORDS: Set[str] = {"rg", "uf", "tel", "cpf", "cep", "pis", "nis", "nit", "mae", "pai", "lat", "lng", "lon"}

# ---------------------------------------------------------------------------
# Correção 1: Whitelist de padrões de colunas não-sensíveis
# Colunas governamentais/institucionais que NÃO devem ser anonimizadas.
# Verificada ANTES das keywords sensíveis.
# ---------------------------------------------------------------------------
_NON_SENSITIVE_PREFIXES: List[str] = [
    "cod_", "codigo_", "código_",
    "descricao_", "descrição_",
    "situacao_", "situação_",
    "regime_", "jornada_",
    "nivel_", "nível_",
    "referencia_", "referência_",
    "padrao_", "padrão_",
    "sigla_", "tipo_", "classe_",
    "diploma_", "documento_",
    "opcao_", "opção_",
    "data_ingresso", "data_nomeacao", "data_nomeação",
    "data_diploma", "data_inicio", "data_início",
    "data_termino", "data_término", "data_posse",
    "data_publicacao", "data_publicação", "data_criacao",
    "data_atualizacao", "data_cadastro", "data_registro",
    "uf_",
]

_NON_SENSITIVE_EXACT: Set[str] = {
    "ano", "mes", "mês", "dia", "semestre", "trimestre", "bimestre",
    "id", "seq", "sequencia", "orgao", "órgão", "uorg",
    "funcao", "função", "atividade",
}


def detect_sensitivity(col_name: str) -> Optional[str]:
    """
    Retorna o tipo sensível detectado, None se sem match, ou False se
    explicitamente não-sensível (whitelist). False impede a heurística
    de conteúdo de rodar para esta coluna.
    """
    normalized = str(col_name).lower().strip()
    # Ignora colunas geradas pelo pandas (Unnamed: 0, Unnamed: 1, etc.)
    if re.match(r'^unnamed\s*:\s*\d+$', normalized):
        return False
    # Ignora colunas que são apenas números (anos, períodos: 2001, 2024)
    if re.match(r'^\d+$', normalized):
        return False
    # Ignora colunas de período trimestral (1Q23, 4Q25, etc.)
    if re.match(r'^[1-4]q\d{2}$', normalized):
        return False

    # --- Correção 1: whitelist de padrões não-sensíveis (antes das keywords) ---
    # Retorna False (não None) para bloquear também a heurística de conteúdo
    for prefix in _NON_SENSITIVE_PREFIXES:
        if normalized.startswith(prefix):
            return False
    # Match exato por palavras (separadas por _ ou -)
    col_words = set(re.split(r'[-_\s]+', normalized))
    if col_words & _NON_SENSITIVE_EXACT:
        # Exceção: se a coluna é exatamente um nome sensível conhecido,
        # a keyword sensível prevalece (ex: "nome" está em SENSITIVE_KEYWORDS)
        clean = normalized.replace("-", "").replace("_", "").replace(" ", "")
        for keyword in SENSITIVE_KEYWORDS:
            kw = keyword.replace("-", "").replace("_", "").replace(" ", "")
            if kw == clean:
                break  # match exato com keyword sensível — não ignorar
        else:
            return False  # nenhum match exato com keyword sensível — é não-sensível

    clean = normalized.replace("-", "").replace("_", "").replace(" ", "")
    # Primeiro tenta match exato (prioridade)
    for keyword, kind in SENSITIVE_KEYWORDS.items():
        kw = keyword.replace("-", "").replace("_", "").replace(" ", "")
        if kw == clean:
            return kind
    # --- Correção 3: match parcial com word boundary ---
    # Usa as palavras do nome da coluna (separadas por _ - espaço)
    # para evitar substrings falsos: "atividade" não casa com "idade",
    # "nomeacao" não casa com "nome", "coordenador" não casa com "endereco"
    col_words_clean = set(re.split(r'[-_\s]+', normalized))
    for keyword, kind in SENSITIVE_KEYWORDS.items():
        kw_clean = keyword.replace("-", "").replace("_", "").replace(" ", "")
        if len(kw_clean) < 4:
            continue  # keywords curtas tratadas separadamente abaixo
        # Match: a keyword deve ser uma palavra inteira do nome da coluna,
        # OU o nome limpo (sem separadores) deve ser exatamente a keyword
        # Verifica se alguma palavra da coluna contém a keyword como palavra inteira
        for word in col_words_clean:
            if word == kw_clean:
                return kind
        # Fallback: keyword composta que coincide com junção de palavras adjacentes
        # Ex: "chave_pix" → clean="chavepix", keyword "chavepix" → match exato (já coberto acima)
    # H-02: Keywords curtas — match por word boundary no nome original
    # Ex: "num_rg" → encontra "rg"; "cargo" → não encontra "rg"
    words = set(re.split(r'[-_\s]+', normalized))
    for short_kw in _SHORT_EXACT_KEYWORDS:
        if short_kw in words:
            kw_clean = short_kw.replace("-", "").replace("_", "")
            if kw_clean in SENSITIVE_KEYWORDS:
                return SENSITIVE_KEYWORDS[kw_clean]
    return None


# ---------------------------------------------------------------------------
# Heurística de texto livre (C-02)
# ---------------------------------------------------------------------------

def _is_freetext_column(series: pd.Series) -> bool:
    """Detecta se uma coluna contém texto livre que pode ter PII."""
    sample = series.dropna().head(50)
    if sample.empty:
        return False
    avg_len = sample.astype(str).str.len().mean()
    # Texto livre tende a ter comprimento médio > 20 caracteres
    if avg_len < 20:
        return False
    # Verifica se tem espaços (indicativo de texto livre vs códigos)
    has_spaces = sample.astype(str).str.contains(r'\s').mean()
    return has_spaces > 0.5


# ---------------------------------------------------------------------------
# Geradores de dados sintéticos
# ---------------------------------------------------------------------------

# Cache para manter consistência: mesmo valor real → mesmo valor fake
_cache: Dict[str, str] = {}


def _cached(real_value: str, generator_fn) -> str:
    """Garante que o mesmo valor real sempre gere o mesmo valor fake."""
    # SHA-256 em vez de MD5 (M-07)
    key = hashlib.sha256(str(real_value).encode()).hexdigest()
    if key not in _cache:
        _cache[key] = generator_fn()
    return _cache[key]


def _fake_cpf() -> str:
    digits = [fake.random_int(0, 9) for _ in range(9)]
    for _ in range(2):
        s = sum((len(digits) + 1 - i) * v for i, v in enumerate(digits))
        d = (s * 10 % 11) % 10
        digits.append(d)
    return "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*digits)


def _fake_cnpj() -> str:
    def calc(digits, weights):
        s = sum(d * w for d, w in zip(digits, weights))
        r = s % 11
        return 0 if r < 2 else 11 - r
    base = [fake.random_int(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    d1 = calc(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = calc(base + [d1], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    n = base + [d1, d2]
    return "{}{}.{}{}{}.{}{}{}/{}{}{}{}-{}{}".format(*n)


def _anonymize_amount(value) -> str:
    """Mantém a ordem de grandeza mas troca o valor exato."""
    try:
        s = str(value).strip()
        if s.lower() in ("nan", "none", ""):
            return value
        # Tenta parse direto (formato inglês: 1234.56)
        try:
            num = float(s)
            if num != num:  # NaN check
                return value
        except ValueError:
            # Formato brasileiro: R$ 1.234,56 ou 1.234.567,89
            clean = re.sub(r"[R$\s]", "", s)
            # Se tem vírgula como último separador decimal
            if "," in clean:
                clean = clean.replace(".", "").replace(",", ".")
            num = float(clean)
        if num == 0:
            return "0"
        original_str = s
        # Para valores muito pequenos, variação percentual não muda 2 casas decimais
        # Usa offset aditivo em vez de multiplicativo
        if abs(num) < 0.1:
            offset = fake.random.uniform(0.01, 0.05)
            new_val = num + (offset if num >= 0 else -offset)
            return f"{new_val:.2f}"
        # Garante que o resultado nunca seja igual ao original (evita C-01)
        for _ in range(10):
            variation = fake.random.uniform(0.85, 1.15)
            new_val = num * variation
            if f"{new_val:.2f}" != original_str:
                return f"{new_val:.2f}"
        # Fallback: offset aditivo
        new_val = num + (abs(num) * 0.20)
        return f"{new_val:.2f}"
    except (ValueError, TypeError):
        # Texto em coluna numérica → anonimiza como label genérico
        return _cached(str(value), lambda: f"Item_{fake.random_number(digits=4)}")


def _anonymize_coordinate(value) -> str:
    """Desloca coordenada geográfica aleatoriamente (±0.05 graus ~5km)."""
    try:
        num = float(str(value).replace(",", "."))
        offset = fake.random.uniform(-0.05, 0.05)
        return f"{num + offset:.6f}"
    except (ValueError, TypeError):
        return str(value)


# ---------------------------------------------------------------------------
# Amostragem inteligente
# ---------------------------------------------------------------------------

def calculate_sample_size(n_rows: int) -> int:
    """
    Calcula o tamanho ideal da amostra com base no total de linhas.

    | N linhas        | Amostra           | Regra                           |
    |-----------------|-------------------|---------------------------------|
    | N <= 30         | 100% (N)          | Arquivo pequeno, manda tudo     |
    | 31 a 100        | 50% de N (min 30) | Reduz mas mantém representativ. |
    | 101 a 1.000     | 100               | Padrão                          |
    | 1.001 a 10.000  | 100               | Idem                            |
    | 10.001 a 100.000| 150               | Arquivo grande                  |
    | 100.001+        | 200               | Máximo recomendado              |
    """
    if n_rows <= 30:
        return n_rows
    elif n_rows <= 100:
        return max(30, n_rows // 2)
    elif n_rows <= 10000:
        return 100
    elif n_rows <= 100000:
        return 150
    else:
        return 200


def _fake_pix(real_value) -> str:
    """Gera chave PIX fake do mesmo tipo da original (CPF, email, telefone ou aleatória)."""
    v = str(real_value).strip()
    # Detecta tipo pela estrutura
    if re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', v):
        return _fake_cpf()
    if "@" in v:
        return fake.email()
    if re.match(r'^[\(\+\d][\d\s\(\)\-\+]+$', v) and len(re.sub(r'\D', '', v)) >= 10:
        return fake.phone_number()
    # Chave aleatória (EVP)
    return fake.uuid4()


GENERATORS: Dict[str, object] = {
    "name":           lambda v: _cached(v, fake.name),
    "company":        lambda v: _cached(v, fake.company),
    "cpf":            lambda v: _cached(v, _fake_cpf),
    "cnpj":           lambda v: _cached(v, _fake_cnpj),
    "rg":             lambda v: _cached(v, lambda: str(fake.random_number(digits=9))),
    "cnh":            lambda v: _cached(v, lambda: str(fake.random_number(digits=11))),
    "email":          lambda v: _cached(v, fake.email),
    "phone":          lambda v: _cached(v, fake.phone_number),
    "address":        lambda v: _cached(v, fake.address),
    "street":         lambda v: _cached(v, fake.street_name),
    "neighborhood":   lambda v: _cached(v, fake.bairro),
    "city":           lambda v: _cached(v, fake.city),
    "state":          lambda v: _cached(v, fake.estado_sigla),
    "zipcode":        lambda v: _cached(v, fake.postcode),
    "birthdate":      lambda v: _cached(v, lambda: str(fake.date_of_birth(minimum_age=18, maximum_age=70))),
    "age":            lambda v: str(fake.random_int(18, 70)),
    "password":       lambda v: _cached(v, lambda: fake.password(length=12)),
    "token":          lambda v: _cached(v, lambda: fake.sha256()),
    "key":            lambda v: _cached(v, lambda: fake.sha1()),
    "process_number": lambda v: _cached(v, lambda: f"{fake.random_number(7)}-{fake.random_number(2)}.{fake.random_number(4)}.{fake.random_int(1,9)}.{fake.random_int(1000,9999)}.{fake.random_number(4)}"),
    "id_number":      lambda v: _cached(v, lambda: str(fake.random_number(digits=max(len(re.sub(r'\D', '', str(v))), 6)))),
    "account":        lambda v: _cached(v, lambda: str(fake.random_number(digits=6))),
    "agency":         lambda v: _cached(v, lambda: str(fake.random_number(digits=4))),
    "bank":           lambda v: _cached(v, lambda: f"Banco {fake.last_name()} ({fake.random_number(digits=3):03d})"),
    "card":           lambda v: _cached(v, lambda: fake.credit_card_number()),
    "pix":            lambda v: _cached(v, lambda: _fake_pix(v)),
    "salary":         _anonymize_amount,
    "amount":         _anonymize_amount,
    "coordinate":     _anonymize_coordinate,
}


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _col_code(index: int) -> str:
    """Converte índice numérico em código de coluna: 0→COL_A, 25→COL_Z, 26→COL_AA."""
    result = ""
    n = index
    while True:
        result = string.ascii_uppercase[n % 26] + result
        n = n // 26 - 1
        if n < 0:
            break
    return f"COL_{result}"


def _anonymize_cell(value, kind: str) -> str:
    """Anonimiza um valor de célula conforme o tipo sensível."""
    if pd.isna(value) or str(value).strip() == "":
        return value
    generator = GENERATORS.get(kind)
    if generator:
        return generator(value)
    return str(value)


# ---------------------------------------------------------------------------
# Exceção de vazamento (C-01)
# ---------------------------------------------------------------------------

class LeakageError(Exception):
    """Exceção levantada quando dados reais vazam para o arquivo anonimizado."""
    pass


# ---------------------------------------------------------------------------
# Leitura inteligente de XLSX (multi-aba + detecção de header)
# ---------------------------------------------------------------------------

def _read_best_sheet(path: Path) -> pd.DataFrame:
    """
    Lê o XLSX escolhendo a aba com mais dados e detectando a linha de header.
    Resolve o problema de planilhas financeiras com abas vazias e headers
    que não estão na primeira linha.
    """
    xls = pd.ExcelFile(path)
    best_df = None
    best_score = -1
    best_sheet = None

    for sheet_name in xls.sheet_names:
        # Lê sem header para inspecionar todas as linhas como dados
        raw = pd.read_excel(xls, sheet_name=sheet_name, header=None, dtype=str)
        if raw.empty:
            continue

        # Score = linhas não-vazias * colunas não-vazias
        non_null_rows = raw.dropna(how="all").shape[0]
        non_null_cols = raw.dropna(axis=1, how="all").shape[1]
        score = non_null_rows * non_null_cols

        if score > best_score:
            best_score = score
            best_sheet = sheet_name

    if best_sheet is None:
        raise ValueError("Nenhuma aba com dados encontrada no arquivo XLSX.")

    log.info(f"Aba selecionada: '{best_sheet}' (score={best_score})")

    # Agora lê a melhor aba e detecta a linha de header
    raw = pd.read_excel(xls, sheet_name=best_sheet, header=None, dtype=str)

    # Encontra a primeira linha com >= 50% de células preenchidas
    header_row = 0
    for i in range(min(10, len(raw))):
        row_values = raw.iloc[i]
        filled = row_values.notna().sum()
        total = len(row_values)
        if total > 0 and filled / total >= 0.5:
            header_row = i
            break

    # Relê com o header correto
    df = pd.read_excel(xls, sheet_name=best_sheet, header=header_row, dtype=str)

    # Remove colunas completamente vazias
    df = df.dropna(axis=1, how="all")
    # Remove linhas completamente vazias
    df = df.dropna(how="all").reset_index(drop=True)

    log.info(
        f"Header detectado na linha {header_row} | "
        f"{len(df)} linhas x {len(df.columns)} colunas"
    )

    # Verifica se há excesso de colunas "Unnamed:" (header errado)
    unnamed_count = sum(1 for c in df.columns if str(c).lower().startswith("unnamed"))
    total_cols = len(df.columns)
    if total_cols > 0 and unnamed_count / total_cols > 0.5:
        log.warning(
            f"⚠ {unnamed_count}/{total_cols} colunas sem nome — "
            f"possível header mal detectado"
        )

    return df


def detect_column_type(series: pd.Series) -> str:
    """
    Analisa o conteúdo de uma coluna para determinar seu tipo real.

    Returns:
        "id_number"      - IDs numéricos únicos (sem decimais, alta cardinalidade)
        "amount"         - valores financeiros (decimais, muitos zeros, baixa cardinalidade relativa)
        "financial_text" - texto com indicadores financeiros (R$, %, milhões)
        "date"           - datas ou períodos (1Q23, 4Q25, 2024, etc.)
        "name"           - nomes próprios (Mixed Case, alta cardinalidade)
        "enum"           - categorias/enums (poucos valores únicos, texto repetitivo)
        "mixed"          - mistura de tipos
        "empty"          - coluna vazia ou quase vazia
    """
    sample = series.dropna().head(100)
    if len(sample) < 2:
        return "empty"

    n = len(sample)
    numeric_count = 0
    has_decimal = 0
    zero_count = 0
    financial_text_count = 0
    date_count = 0
    name_count = 0

    for val in sample.astype(str):
        val_clean = val.strip()
        if not val_clean:
            continue

        # Numérico: inteiros, decimais, negativos, notação científica
        if re.match(r'^-?[\d.,]+(?:[eE][+-]?\d+)?$', val_clean.replace(" ", "")):
            numeric_count += 1
            # Correção 4: rastrear decimais e zeros para separar id_number de amount
            normalized_num = val_clean.replace(".", "").replace(",", ".")
            if "," in val_clean or (val_clean.count(".") > 0 and not val_clean.replace(".", "").replace("-", "").isdigit()):
                has_decimal += 1
            try:
                if float(normalized_num) == 0:
                    zero_count += 1
            except ValueError:
                pass
            continue

        # Financeiro em texto: R$, US$, %, milhões, bilhões
        if re.search(r'R\$|US\$|%|milh[õo]|bilh[õo]|thousand|million|billion', val_clean, re.IGNORECASE):
            financial_text_count += 1
            continue

        # Período/data: 1Q23, 4Q25, 2024, Jan/2023, etc.
        if re.match(r'^[1-4]Q\d{2}$', val_clean) or re.match(r'^\d{4}$', val_clean):
            date_count += 1
            continue

        # Nome próprio: 2+ palavras capitalizadas
        words = val_clean.split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if w.isalpha()):
            name_count += 1
            continue

    # Classifica pelo tipo predominante
    if n == 0:
        return "empty"

    # --- Correção 2: detectar enums/categorias ---
    # Texto com poucos valores únicos (<10 ou <10% da amostra) = enum, não name
    unique_values = series.dropna().head(100).nunique()
    unique_ratio = unique_values / n if n > 0 else 1

    if numeric_count / n >= 0.5:
        # --- Correção 4: separar id_number de amount ---
        # id_number: sem decimais, valores únicos altos, poucos zeros
        # amount: tem decimais ou muitos zeros (ex: 0.00 em colunas financeiras)
        is_integer_like = has_decimal < numeric_count * 0.1  # <10% tem decimal
        has_many_zeros = zero_count > numeric_count * 0.3    # >30% são zero
        is_high_cardinality = unique_values > n * 0.5         # >50% valores únicos

        if is_integer_like and is_high_cardinality and not has_many_zeros:
            return "id_number"
        return "amount"
    if financial_text_count / n >= 0.3:
        return "financial_text"
    if date_count / n >= 0.5:
        return "date"
    if name_count / n >= 0.5:
        # Correção 2: se há poucos valores únicos, é enum/categoria, não nome
        if unique_values < 10 or unique_ratio < 0.1:
            return "enum"
        return "name"
    if (numeric_count + financial_text_count) / n >= 0.5:
        return "amount"
    return "mixed"


# ---------------------------------------------------------------------------
# Função principal de anonimização
# ---------------------------------------------------------------------------

def anonymize_spreadsheet(
    input_path: Path,
    sample_size: Optional[int] = None,
) -> Tuple[Path, Path]:
    """
    Anonimiza uma planilha CSV ou XLSX.

    Args:
        input_path: Caminho para o arquivo real (em data/real/)
        sample_size: Número de linhas na amostra.
                     None = amostragem inteligente automática.
                     Valor explícito = sobrescreve a lógica automática.

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)

    Raises:
        LeakageError: Se dados reais vazarem para o arquivo anonimizado
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem
    suffix = input_path.suffix.lower()

    log.info(f"Iniciando anonimização: {input_path.name}")

    # --- Leitura ---
    if suffix == ".csv":
        df = None
        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"):
            for sep in (",", ";", "\t", "|"):
                try:
                    candidate = pd.read_csv(input_path, dtype=str, encoding=enc, sep=sep)
                    # Descarta se resultou em coluna única (separador errado)
                    if len(candidate.columns) > 1:
                        df = candidate
                        log.info(f"Encoding: {enc} | Separador: '{sep}'")
                        break
                except Exception:
                    continue
            if df is not None:
                break
        if df is None:
            raise ValueError("Não foi possível ler o CSV. Verifique encoding e separador.")
    elif suffix in (".xlsx", ".xls"):
        df = _read_best_sheet(input_path)
    else:
        raise ValueError(f"Formato não suportado: {suffix}. Use CSV ou XLSX.")

    total_rows = len(df)
    log.info(f"Arquivo carregado: {total_rows} linhas, {len(df.columns)} colunas")

    # --- Amostragem inteligente ---
    if sample_size is not None:
        # Usuário informou --sample explicitamente: usa o valor dele
        effective_sample = min(sample_size, total_rows)
        log.info(f"Amostragem manual: --sample {sample_size} (usuário)")
    else:
        # Amostragem automática baseada no tamanho do arquivo
        effective_sample = calculate_sample_size(total_rows)
        log.info(f"Amostragem inteligente: {effective_sample} linhas calculadas para N={total_rows}")

    pct_sent = (effective_sample / total_rows * 100) if total_rows > 0 else 100
    pct_saved = 100 - pct_sent

    if effective_sample >= total_rows:
        df_sample = df.copy()
        log.warning(
            f"⚠ Arquivo pequeno — enviando todas as {total_rows} linhas "
            f"(100% do arquivo)"
        )
    else:
        df_sample = df.sample(n=effective_sample, random_state=42).reset_index(drop=True)
        log.info(
            f"Amostra selecionada: {effective_sample} de {total_rows} linhas "
            f"({pct_sent:.2f}% enviado, {pct_saved:.2f}% economizado)"
        )

    # --- Detecção de colunas sensíveis ---
    col_types: Dict[str, Optional[str]] = {}
    for col in df_sample.columns:
        kind = detect_sensitivity(col)
        source = "header"
        # False = explicitamente não-sensível (whitelist) — não roda heurística
        # None = sem match por header — tenta heurística de conteúdo
        if kind is False:
            kind = None  # normaliza para None no dict final
        elif kind is None:
            col_type = detect_column_type(df_sample[col])
            source = "conteúdo"
            if col_type == "id_number":
                kind = "id_number"
            elif col_type == "amount":
                kind = "amount"
            elif col_type == "name":
                kind = "name"
            elif col_type == "financial_text":
                kind = "amount"
            # "enum" e "mixed" ficam como None (não-sensível)
        col_types[col] = kind
        if kind:
            log.info(f"  Coluna sensível ({source}): '{col}' -> tipo '{kind}'")
        else:
            log.info(f"  Coluna não-sensível: '{col}'")

    # --- Renomeação de colunas ---
    col_rename_map: Dict[str, str] = {}
    for i, col in enumerate(df_sample.columns):
        col_rename_map[col] = _col_code(i)

    df_anon = df_sample.rename(columns=col_rename_map)

    # --- Anonimização dos valores sensíveis ---
    for original_col, kind in col_types.items():
        if kind is None:
            continue
        new_col = col_rename_map[original_col]
        log.info(f"  Anonimizando coluna: {new_col} (tipo={kind})")
        df_anon[new_col] = df_sample[original_col].apply(
            lambda v: _anonymize_cell(v, kind)
        )

    # --- C-02: Aplica text_engine em colunas de texto livre não-sensíveis ---
    from text_engine import TextAnonymizer
    text_eng = TextAnonymizer()
    freetext_cols: List[str] = []

    for original_col, kind in col_types.items():
        if kind is not None:
            continue  # já anonimizada
        new_col = col_rename_map[original_col]
        if _is_freetext_column(df_sample[original_col]):
            freetext_cols.append(original_col)
            log.info(f"  Texto livre detectado em '{original_col}' -> aplicando text_engine")
            df_anon[new_col] = df_sample[original_col].apply(
                lambda v: text_eng.anonymize(str(v)) if pd.notna(v) and str(v).strip() else v
            )

    if freetext_cols:
        log.info(f"  text_engine aplicado em {len(freetext_cols)} coluna(s) de texto livre")

    # --- Validação de segurança (C-01: BLOQUEIA em caso de vazamento) ---
    anon_filename = f"anon_{stem}_{timestamp}{suffix}"
    anon_path = ANONYMIZED_DIR / anon_filename

    _validate_no_leakage(df_sample, df_anon, col_types, col_rename_map, anon_path)

    # --- Salvar arquivo anonimizado ---
    if suffix == ".csv":
        df_anon.to_csv(anon_path, index=False)
    else:
        df_anon.to_excel(anon_path, index=False)

    log.info(f"Arquivo anonimizado salvo: {anon_path}")

    # --- Salvar mapa de correspondência ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "total_linhas_original": total_rows,
        "total_linhas_amostra": len(df_anon),
        "pct_enviado": round(pct_sent, 2),
        "pct_economizado": round(pct_saved, 2),
        "amostragem": "manual" if sample_size is not None else "automatica",
        "colunas": {
            col_rename_map[col]: {
                "nome_original": col,
                "tipo_sensivel": kind,
                "anonimizada": kind is not None,
                "texto_livre": col in freetext_cols,
            }
            for col, kind in col_types.items()
        },
    }

    map_filename = f"map_{stem}_{timestamp}.json"
    map_path = MAPS_DIR / map_filename

    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    log.info(f"Mapa de correspondência salvo: {map_path}")

    # --- Resumo ---
    sensitive_count = sum(1 for k in col_types.values() if k is not None)
    log.info(
        f"Anonimização concluída: {sensitive_count}/{len(df_sample.columns)} colunas "
        f"sensíveis + {len(freetext_cols)} texto livre | "
        f"Tamanho real: {total_rows} | Amostra: {len(df_anon)} | "
        f"Enviado: {pct_sent:.2f}% | Economizado: {pct_saved:.2f}%"
    )

    return anon_path, map_path


def _validate_no_leakage(
    df_original: pd.DataFrame,
    df_anon: pd.DataFrame,
    col_types: Dict[str, Optional[str]],
    col_rename_map: Dict[str, str],
    anon_path: Path,
):
    """
    C-01: Verificação de segurança que BLOQUEIA a saída em caso de vazamento.
    Se dados reais de colunas sensíveis aparecerem no arquivo anonimizado,
    deleta o arquivo (se existir) e levanta LeakageError.
    """
    leaks: List[Tuple[str, str, List[str]]] = []
    for original_col, kind in col_types.items():
        if kind is None:
            continue
        new_col = col_rename_map[original_col]
        # Comparação LINHA-A-LINHA: detecta se o mesmo índice manteve o valor
        col_leaks = []
        for idx in df_original.index:
            if idx not in df_anon.index:
                continue
            orig_val = str(df_original.at[idx, original_col]) if pd.notna(df_original.at[idx, original_col]) else ""
            anon_val = str(df_anon.at[idx, new_col]) if pd.notna(df_anon.at[idx, new_col]) else ""
            if orig_val == anon_val and len(orig_val.strip()) > 3:
                col_leaks.append(orig_val)
        if col_leaks:
            leaks.append((original_col, kind, col_leaks[:5]))

    if leaks:
        # C-01: BLOQUEIA — deleta arquivo se existir e levanta exceção
        if anon_path.exists():
            anon_path.unlink()
            log.error(f"ARQUIVO DELETADO por vazamento: {anon_path}")

        leak_summary = []
        for col, kind, examples in leaks:
            # Log sem expor os valores reais — apenas contagem
            leak_summary.append(f"Coluna '{col}' (tipo={kind}): {len(examples)} valor(es) vazado(s)")

        msg = (
            "VAZAMENTO DETECTADO — SAÍDA BLOQUEADA.\n"
            + "\n".join(f"  - {s}" for s in leak_summary)
            + "\nNenhum arquivo foi gerado. Corrija o gerador antes de prosseguir."
        )
        log.error(msg)
        raise LeakageError(msg)
    else:
        log.info("Validação de segurança: PASSOU — nenhum vazamento detectado.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardião — Anonimizador de planilhas CSV/XLSX"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo a anonimizar")
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="Número de linhas na amostra (omita para amostragem inteligente automática)",
    )
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    try:
        anon_path, map_path = anonymize_spreadsheet(input_path, sample_size=args.sample)
    except LeakageError:
        log.error("Operação abortada por vazamento de dados.")
        sys.exit(2)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
