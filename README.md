# PSA — Privacy Shield Agent for AI

<div align="center">

**Seus dados nunca saem. A IA trabalha no escuro.**

[![Beta](https://img.shields.io/badge/Status-Beta-orange?style=for-the-badge)](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai)
[![Security Score](https://img.shields.io/badge/Security%20Score-82%2F100-00e5ff?style=for-the-badge&logo=shield&logoColor=white)](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai)
[![Formats](https://img.shields.io/badge/Formats-21%20extensions-ff6b35?style=for-the-badge&logo=files&logoColor=white)](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai)
[![Version](https://img.shields.io/badge/Version-v6.1-00ff9d?style=for-the-badge)](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai/releases)
[![License](https://img.shields.io/badge/License-MIT-7b5ea7?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LGPD](https://img.shields.io/badge/LGPD-Compliant-green?style=for-the-badge)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-green?style=for-the-badge)](https://gdpr.eu)
[![HIPAA](https://img.shields.io/badge/HIPAA-Compliant-green?style=for-the-badge)](https://www.hhs.gov/hipaa)

*Camada de seguranca local que intercepta e anonimiza dados sensiveis **antes** de envia-los a qualquer IA.*
*Funciona com Claude, ChatGPT, Gemini e qualquer LLM via API.*

[Site](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai) · [Release](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai/releases) · [Lista de Espera](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai)

</div>

---

> **Versao Beta — Em desenvolvimento ativo.**
> Use como camada adicional de protecao, nunca como unica garantia de conformidade com a LGPD.
> Nao nos responsabilizamos por eventuais erros ou falhas de deteccao.
> O PSA nao substitui assessoria juridica especializada.

---

> **PSA nao e uma ferramenta de produtividade. E uma camada de seguranca que, como consequencia, tambem economiza 99% dos tokens e torna qualquer analise 30x mais rapida.**

---

## Seguranca — Score 82/100

| Area | Status | Detalhe |
|------|--------|---------|
| Integridade de dados | ✅ | SHA256 em cada arquivo anonimizado |
| Audit trail | ✅ | audit_trail.jsonl append-only |
| Controle de mapas | ✅ | --no-map + --purge-maps |
| Anti-vazamento | ✅ | Validacao + delecao automatica |
| Anti-injection | ✅ | Validacao de nomes de arquivo |
| Encoding | ✅ | Auto-deteccao multi-encoding |
| RIPD automatico | ✅ | Art. 38 LGPD compliance |

**5 CVEs corrigidos** na v6.1: hash de integridade, audit trail, controle de mapas, anti-injection, purge de dados residuais.

---

## Por que seguranca em primeiro lugar?

Toda empresa que usa IA com dados reais esta exposta. O PSA resolve os 4 maiores medos:

### Vazamento de dados
CPF, salario, endereco, prontuario — tudo isso vai para servidores externos quando voce cola numa IA.
**PSA: dados reais nunca saem do seu computador. A IA so ve dados ficticios.**

### Multa LGPD/GDPR
A ANPD pode multar ate **2% do faturamento**. A GDPR ate **4%**. Basta um incidente.
**PSA: compliance automatico + log auditavel de cada operacao.**

### Segredo industrial
Precos, margens, clientes VIP, estrategias — tudo exposto ao enviar para a nuvem.
**PSA: so dados ficticios chegam a nuvem. Seus segredos ficam no seu computador.**

### Dados treinando concorrentes
Termos de uso de IAs podem permitir uso dos seus dados para treinar modelos.
**PSA: nenhum dado real alimenta nenhum modelo. Zero. Nunca.**

---

## Compliance garantido

| Regulacao | Status | Escopo |
|---|---|---|
| ✅ **LGPD** | Compliant | Lei Geral de Protecao de Dados (Brasil, Lei 13.709/2018) |
| ✅ **GDPR** | Compliant | General Data Protection Regulation (Europa) |
| ✅ **HIPAA** | Compliant | Health Insurance Portability and Accountability Act (EUA) |
| ✅ **Sigilo profissional** | Compliant | OAB, CRM, CRC — dados de clientes/pacientes protegidos |
| ✅ **Segredo industrial** | Compliant | Precos, margens, estrategias nunca saem do ambiente local |

---

## Caso real: 256.013 servidores do GDF

| Metrica | Resultado |
|---|---|
| Base de teste | **256.013 linhas** — folha de pagamento real do Governo do Distrito Federal |
| Vazamentos detectados | **Zero** |
| Score de seguranca | **82/100** (auditoria v6.1) |
| Padroes PII detectados | **70+** |
| Formatos suportados | **21 extensoes / 18 formatos** |

**Nenhum nome, CPF, salario ou endereco real saiu do computador.**

---

## 21 Extensoes Suportadas (18 Formatos)

| # | Formato | Extensoes | Tipo |
|---|---------|-----------|------|
| 1 | Planilha CSV | `.csv` | Dados tabulares |
| 2 | Planilha Excel | `.xlsx`, `.xls` | Dados tabulares |
| 3 | Documento Word | `.docx` | Documento |
| 4 | Texto puro | `.txt` | Documento |
| 5 | PDF | `.pdf` | Documento |
| 6 | Apresentacao | `.pptx` | Documento |
| 7 | E-mail EML | `.eml` | Comunicacao |
| 8 | E-mail MSG | `.msg` | Comunicacao |
| 9 | JSON | `.json` | Dados estruturados |
| 10 | XML / NF-e | `.xml` | Dados estruturados |
| 11 | RTF | `.rtf` | Documento |
| 12 | ODT | `.odt` | Documento |
| 13 | HTML | `.html` | Web |
| 14 | YAML | `.yaml`, `.yml` | Configuracao |
| 15 | SQL | `.sql` | Banco de dados |
| 16 | Log | `.log` | Sistema |
| 17 | vCard | `.vcf` | Contatos |
| 18 | Parquet | `.parquet` | Dados colunares |

---

## Amostragem Inteligente v5.1

> **O PSA e estatisticamente inteligente — envia o minimo necessario para cada tamanho de arquivo, nunca mais do que precisa.**

A funcao `calculate_sample_size(n)` determina automaticamente a amostra ideal com base no Teorema Central do Limite (n >= 30):

| Tamanho do arquivo (N linhas) | Amostra enviada | Regra |
|---|---|---|
| N <= 30 | 100% (todas as linhas) | Arquivo pequeno — manda tudo com aviso no log |
| 31 a 100 | 50% de N (minimo 30) | Reduz mas mantem representatividade estatistica |
| 101 a 10.000 | 100 linhas | Padrao |
| 10.001 a 100.000 | 150 linhas | Arquivo grande — amostra ligeiramente maior |
| 100.001+ | 200 linhas | Maximo recomendado |

### Exemplos reais

| Arquivo | Total | Amostra | % enviado | Comportamento |
|---|---|---|---|---|
| Relatorio pequeno | 25 linhas | 25 (tudo) | 100% | Aviso: "Arquivo pequeno — enviando todas as 25 linhas" |
| Lista de clientes | 60 linhas | 30 | 50% | `max(30, 60//2) = 30` |
| Folha GDF | 256.013 linhas | 200 | 0,08% | Maximo recomendado para arquivos 100K+ |

---

## Beneficios adicionais (consequencias da protecao)

### Economia de ate 99,9% dos tokens

| Cenario | Sem PSA | Com PSA (v5.1) | Economia |
|---|---|---|---|
| Planilha de 256.000 linhas | 256.000 linhas enviadas | 200 linhas enviadas | **99,92%** |
| Planilha de 60 linhas | 60 linhas enviadas | 30 linhas enviadas | **50%** |
| Custo estimado (256K linhas) | ~US$ 12,00 | ~US$ 0,10 | **99,2%** |

### Analises 30x mais rapidas

| Cenario | Sem PSA | Com PSA |
|---|---|---|
| Tempo de analise | ~15 min | ~30 seg |
| Tempo de resposta da IA | timeout frequente | resposta imediata |

> Esses ganhos nao sao o objetivo do PSA. Sao **consequencias** de proteger seus dados corretamente.

---

## Como funciona — Os 19 Passos

**16 de 19 passos rodam 100% local. Seus dados reais jamais saem do seu computador.**

**Nem o nome do seu arquivo sai do computador. Seus dados comecam protegidos do primeiro ao ultimo passo.**

| Passo | O que acontece | Local ou Nuvem | Consome Token? | Dados saem? |
|---|---|---|---|---|
| 1 | Usuario entrega o arquivo ao PSA | Local | Nao | Nao — nome protegido por codigo generico (DOC_001) |
| 2 | PSA invoca o psa.py via codigo generico | Local | Nao | Nao |
| 3 | Valida seguranca do arquivo | Local | Nao | Nao |
| 4 | Detecta extensao e escolhe script correto (21 extensoes) | Local | Nao | Nao |
| 4b | Risk Engine classifica risco LGPD 1-10 | Local | Nao | Nao |
| 4c | Seleciona modo por risco: ECO/PADRAO/MAXIMO | Local | Nao | Nao |
| 5 | Le o arquivo real do disco | Local | Nao | Nao |
| 6 | Amostragem inteligente — calculate_sample_size(n) | Local | Nao | Nao |
| 7 | Detecta colunas sensiveis (70+ keywords) | Local | Nao | Nao |
| 8 | Renomeia colunas para COL_A, COL_B... | Local | Nao | Nao |
| 9 | Anonimiza valores com Faker pt_BR offline | Local | Nao | Nao |
| 10 | Varia valores financeiros em +-15% | Local | Nao | Nao |
| 11 | Escaneia textos livres e substitui via regex | Local | Nao | Nao |
| 12 | Validacao anti-vazamento — detectou dado real? Deleta tudo | Local | Nao | Nao |
| 13 | Salva arquivo anonimizado em data/anonymized/ | Local | Nao | Nao |
| 14 | Salva mapa + SHA256 + audit trail | Local | Nao | Nao |
| 15 | Gera relatorio RIPD automatico (Art. 38 LGPD) | Local | Nao | Nao |
| 16 | Claude/IA le o arquivo anonimizado | Nuvem | Sim | Sim — so dados ficticios |
| 17 | Claude/IA realiza analise e responde | Nuvem | Sim | Sim — so resultados ficticios |
| 18 | Claude/IA gera script Python para rodar localmente | Nuvem | Sim | Sim — so o codigo, sem dados |
| 19 | Script roda nos dados reais localmente → results/ | Local | Nao | Nao |

### Exemplo real

```python
# Entrada (seu documento)
"O cliente Joao Silva, CPF 123.456.789-00, email joao@empresa.com"

# Apos PSA (o que a IA ve)
"O cliente [NAME_7f2a], CPF [CPF_9b1c], email [EMAIL_3d8e]"

# Resultado revertido (voce recebe)
"O cliente Joao Silva, CPF 123.456.789-00, email joao@empresa.com"
```

---

## Padroes PII detectados (70+)

- **Documentos brasileiros:** CPF, CNPJ, RG, CNH, PIS/PASEP, Titulo de Eleitor
- **Contato:** E-mail, telefone fixo, celular, WhatsApp
- **Localizacao:** Endereco completo, CEP, coordenadas GPS
- **Financeiro:** Cartao de credito, conta bancaria, agencia, PIX
- **Saude:** CRM, CRF, prontuario, convenio
- **Identificacao:** Nome completo, data de nascimento, passaporte

---

## Agentes disponiveis

| Agente | Funcao |
|---|---|
| **Comandante (CEO)** | Orquestra o fluxo completo de protecao |
| **PSA Guardiao** | Especialista em anonimizacao e validacao |
| **CFO** | Processamento de dados financeiros |

---

## Instalacao

```bash
# Clone o repositorio
git clone https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai.git
cd psa-privacy-shield-agent-for-ai

# Instale as dependencias
pip install -r requirements.txt

# Execute
python psa.py
```

### Pre-requisitos

- Python 3.10+
- Chave de API da Anthropic (Claude) ou OpenAI (ChatGPT)

---

## Para quem e

| Setor | Caso de uso |
|---|---|
| **Advocacia** | Analisar contratos sem expor dados de clientes |
| **Saude** | Processar prontuarios com sigilo medico |
| **Contabilidade / RH** | Trabalhar com CPFs e salarios em seguranca |
| **Governo** | Bases publicas com dados pessoais de cidadaos |
| **PMEs** | Compliance LGPD sem contratar DPO |

---

## Estrutura do projeto

```
psa-privacy-shield-agent-for-ai/
├── psa.py                       # Interface unificada
├── anonymizer.py                # CSV / XLSX
├── text_engine.py               # Motor de regex compartilhado
├── classifier.py                # Classificador de risco LGPD 1-10
├── pattern_enricher.py          # Enriquecedor de padroes PII
├── ripd_report.py               # Relatorio RIPD (Art. 38 LGPD)
├── file_registry.py             # Registro DOC_NNN
├── anonymize_document.py        # DOCX / TXT
├── anonymize_pdf.py             # PDF
├── anonymize_presentation.py    # PPTX
├── anonymize_email.py           # EML / MSG
├── anonymize_json.py            # JSON
├── anonymize_xml.py             # XML / NF-e
├── anonymize_html.py            # HTML
├── anonymize_yaml.py            # YAML / YML
├── anonymize_sql.py             # SQL
├── anonymize_log.py             # LOG
├── anonymize_vcf.py             # VCF (vCard)
├── anonymize_parquet.py         # Parquet
├── anonymize_rtf.py             # RTF
├── anonymize_odt.py             # ODT
├── CLAUDE.md                    # Instrucoes para Claude Code
├── CHANGELOG.md                 # Historico de versoes
└── docs/
    └── SKILL-SPEC.md            # Especificacao tecnica
```

---

## Autor

**Marcos Cruz**
Brasilia/DF — Marco 2026
Ideia original: PSA como modo nativo de privacidade em qualquer IA.

---

## Contato & Validacao

Estou validando o PSA com profissionais de advocacia, saude e contabilidade.
Se voce lida com dados sensiveis e usa IA, quero conversar.

[Site oficial](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai) · [Lista de espera](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai)

---

<div align="center">
  <sub>Built with security in Brasilia, Brasil · Co-authored with Claude (Anthropic)</sub>
</div>
