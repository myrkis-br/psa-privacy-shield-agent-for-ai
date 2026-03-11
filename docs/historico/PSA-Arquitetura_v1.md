# PSA — Arquitetura Tecnica

> **Versao:** v1
> **Data:** 2026-03-11
> **Mudancas:** Documento inicial — arquitetura completa do projeto em marco/2026.

---

## Visao geral

```
Usuario → Comandante → Registro (DOC_NNN) → PSA Guardiao (anonimiza) → Agente Especialista
                                                                              |
Usuario ← Comandante (so usa DOC_NNN) ← execucao local com dados reais ← codigo/analise
```

O PSA opera em 19 passos, dos quais 15 sao 100% locais. Dados reais nunca saem do computador.

## Estrutura de pastas

```
psa-project/
├── agents/                    Definicao dos agentes
│   ├── comandante.md          CEO — recebe pedidos, delega
│   ├── psa-guardiao.md        Guardiao — unica porta de saida
│   └── cfo.md                 CFO — analise financeira
├── data/
│   ├── real/                  PROTEGIDO — arquivos originais
│   ├── samples/               PROTEGIDO — amostras pre-anonimizacao
│   ├── anonymized/            Pode ir pra nuvem — dados ficticios
│   └── maps/                  PROTEGIDO — mapas real<->fake + file_registry.json
├── scripts/
│   ├── psa.py                 Interface unificada (ponto de entrada)
│   ├── file_registry.py       Registro de nomes → codigos (DOC_NNN) + --history
│   ├── anonymizer.py          CSV/XLSX (com text_engine + amostragem inteligente v5.1)
│   ├── anonymize_document.py  DOCX/TXT
│   ├── anonymize_pdf.py       PDF
│   ├── anonymize_presentation.py  PPTX
│   ├── anonymize_email.py     EML/MSG
│   └── text_engine.py         Motor de regex compartilhado
├── docs/
│   ├── SKILL-SPEC.md          Especificacao tecnica
│   └── historico/             Documentos de referencia versionados
├── logs/                      PROTEGIDO — pode conter PII residual
├── results/                   Resultados de analises
├── CLAUDE.md                  Regras de protocolo para Claude
├── README.md                  README publico
└── index.html                 Landing page (7 idiomas)
```

## Diretorios e permissoes

| Diretorio | Claude pode ler? | Claude pode escrever? | Sai do computador? |
|---|---|---|---|
| data/real/ | NAO | NAO (exceto scripts teste) | NAO |
| data/samples/ | NAO | NAO | NAO |
| data/maps/ | NAO | NAO | NAO |
| data/anonymized/ | SIM | SIM | SIM (so ficticios) |
| logs/ | NAO | NAO | NAO |
| results/ | SIM | SIM | NAO |
| scripts/ | SIM | SIM | NAO |

## Scripts — responsabilidades

### psa.py (Interface unificada)
- Ponto de entrada para toda operacao
- Detecta tipo de arquivo e despacha para script correto
- Comandos: --register, --list-files, --history, --list-supported
- Validacao de seguranca pre-execucao (bloqueia diretorios protegidos)
- Registro automatico ao processar por caminho real

### file_registry.py (Registro de arquivos)
- Substitui nomes reais por codigos genericos (DOC_001, DOC_002...)
- Registro salvo em data/maps/file_registry.json
- Idempotente: mesmo arquivo = mesmo codigo
- Funcoes: register_file, resolve_code, is_doc_code, list_registered, get_history

### anonymizer.py (Planilhas CSV/XLSX)
- Detecta colunas sensiveis (70+ keywords)
- Renomeia colunas para COL_A, COL_B...
- Anonimiza com Faker pt_BR offline (seed aleatorio)
- Amostragem inteligente v5.1: calculate_sample_size(n)
- Text engine em colunas de texto livre (C-02)
- Validacao anti-vazamento C-01 (bloqueia + deleta em caso de leak)
- Variacao financeira ±15%
- Cache: mesmo valor real → mesmo valor fake

### anonymize_pdf.py (PDFs)
- Extrai texto com pdfplumber
- Amostra paginas (padrao: 10)
- Detecta e substitui nomes, CNPJs, enderecos, telefones
- Salva como TXT anonimizado

### anonymize_document.py (DOCX/TXT)
- Processa paragrafos com amostragem
- Preserva headers/footers
- Aplica text_engine

### anonymize_presentation.py (PPTX)
- Processa slides com amostragem
- Aplica text_engine em text frames

### anonymize_email.py (EML/MSG)
- Processa campo a campo
- Aviso sobre anexos

### text_engine.py (Motor de regex)
- Detecta CPF, CNPJ, nomes (Mixed Case + ALL-CAPS), emails, telefones
- Suporta honorificos (Dr., Dra., Sr., Sra., Prof., Des., Min.)
- Suporta sufixos (Filho, Junior, Neto, Sobrinho)

## Amostragem Inteligente v5.1

Funcao `calculate_sample_size(n_rows)` em anonymizer.py:

| N linhas | Amostra | Regra |
|---|---|---|
| <= 30 | 100% (N) | Arquivo pequeno — manda tudo + aviso no log |
| 31 a 100 | 50% (min 30) | Representatividade estatistica (TCL) |
| 101 a 10.000 | 100 | Padrao |
| 10.001 a 100.000 | 150 | Arquivo grande |
| 100.001+ | 200 | Maximo recomendado |

- --sample N sobrescreve a logica automatica
- Log registra: tamanho real, amostra, % enviado, % economizado
- Amostra nunca pode ser maior que o arquivo real

## Seguranca

### Validacao anti-vazamento (C-01)
- Compara valores originais vs anonimizados
- Se detecta overlap > 3 chars → deleta arquivo + levanta LeakageError

### Text engine em texto livre (C-02)
- Colunas nao-sensiveis com texto livre sao escaneadas
- Detecta PII em campos de observacao, descricao, etc.

### Encoding
- CSV: auto-detecta (utf-8, latin-1, cp1252) + separador (, ; tab |)
- TXT: fallback (utf-8 → latin-1 → cp1252)

### Faker
- Seed aleatorio via os.urandom() — nao deterministico
- Cache SHA-256 para consistencia

## Ambiente

- Python 3.9 (/usr/bin/python3)
- Dependencias: pandas, faker, pdfplumber, python-docx, python-pptx, openpyxl
- Tipagem: Optional[str], Tuple[...], Dict[str, str] (Python 3.9)

## Landing page

- 7 idiomas: PT, EN, ES, ZH, HI, FR, HE
- HE com suporte RTL completo
- Secoes: Hero (seguranca), 4 Medos, Compliance, Caso real, Beneficios, Amostragem v5.1, 19 Passos
- Waitlist via Google Forms (iframe oculto)
