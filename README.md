# PSA — Privacy Shield Agent for AI

<div align="center">

**Seu guarda-costas digital. Seu guardião de dados.**

[![Audit Score](https://img.shields.io/badge/Audit%20Score-100%2F100-00e5ff?style=for-the-badge&logo=shield&logoColor=white)](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai)
[![Version](https://img.shields.io/badge/Version-v1.0.0-00ff9d?style=for-the-badge)](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai/releases/tag/v1.0.0)
[![License](https://img.shields.io/badge/License-MIT-7b5ea7?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LGPD](https://img.shields.io/badge/LGPD-Compliant-green?style=for-the-badge)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-green?style=for-the-badge)](https://gdpr.eu)

*Camada de proteção local que anonimiza dados sensíveis **antes** de enviá-los a qualquer IA.*  
*Funciona com Claude, ChatGPT, Gemini e qualquer LLM via API.*

[🌐 Site](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai) · [📦 Release v1.0.0](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai/releases/tag/v1.0.0) · [📋 Lista de Espera](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai)

</div>

---

## 🛡️ O que é o PSA?

O **PSA - Privacy Shield Agent for AI** é uma camada de proteção que intercepta seus documentos e dados **antes** de enviá-los à nuvem, substituindo informações sensíveis por tokens seguros. Após o processamento pela IA, os tokens são revertidos localmente.

**Nenhum dado sensível seu jamais toca servidores externos.**

```
Seu documento → [PSA: Anonimiza] → IA na nuvem → [PSA: Reverte] → Resultado seguro
     CPF real        TOKEN_001         analisa          TOKEN_001          CPF real
```

---

## ✅ Resultados comprovados

| Métrica | Resultado |
|---|---|
| 🔒 Score de auditoria de segurança | **100/100** (28/28 vulnerabilidades corrigidas) |
| 📊 Base de teste (GDF real) | **256.000 linhas** processadas |
| 🚫 Vazamentos detectados | **Zero** |
| 🔍 Padrões PII detectados | **70+** |
| 📄 Formatos suportados | **11** |

---

## 🚀 Como funciona — Os 19 Passos

**15 de 19 passos rodam 100% local. Seus dados reais jamais saem do seu computador.**

**Nem o nome do seu arquivo sai do computador. Seus dados começam protegidos do primeiro ao último passo.**

| Passo | O que acontece | Local ou Nuvem | Consome Token? | Dados saem do computador? |
|---|---|---|---|---|
| 1 | Usuário entrega o arquivo ao PSA | 💻 Local | ❌ Não | ❌ Não — nome protegido por código genérico (DOC_001) via file_registry |
| 2 | PSA invoca o psa.py via código genérico | 💻 Local | ❌ Não | ❌ Não |
| 3 | Valida segurança do arquivo | 💻 Local | ❌ Não | ❌ Não |
| 4 | Detecta extensão e escolhe script correto | 💻 Local | ❌ Não | ❌ Não |
| 5 | Lê o arquivo real do disco | 💻 Local | ❌ Não | ❌ Não |
| 6 | Faz amostragem (padrão: 100 linhas) | 💻 Local | ❌ Não | ❌ Não |
| 7 | Detecta colunas sensíveis (70+ keywords) | 💻 Local | ❌ Não | ❌ Não |
| 8 | Renomeia colunas para COL_A, COL_B... | 💻 Local | ❌ Não | ❌ Não |
| 9 | Anonimiza valores com Faker pt_BR offline | 💻 Local | ❌ Não | ❌ Não |
| 10 | Varia valores financeiros em ±15% | 💻 Local | ❌ Não | ❌ Não |
| 11 | Escaneia textos livres e substitui via regex | 💻 Local | ❌ Não | ❌ Não |
| 12 | Validação anti-vazamento — detectou dado real? Deleta tudo automaticamente | 💻 Local | ❌ Não | ❌ Não |
| 13 | Salva arquivo anonimizado em data/anonymized/ | 💻 Local | ❌ Não | ❌ Não |
| 14 | Salva mapa de correspondência em data/maps/ | 💻 Local | ❌ Não | ❌ Não |
| 15 | Salva log da operação em logs/ | 💻 Local | ❌ Não | ❌ Não |
| 16 | Claude/IA lê o arquivo anonimizado | ☁️ Nuvem | ✅ Sim | ✅ Sim — só dados fictícios |
| 17 | Claude/IA realiza análise e responde | ☁️ Nuvem | ✅ Sim | ✅ Sim — só resultados fictícios |
| 18 | Claude/IA gera script Python para rodar localmente | ☁️ Nuvem | ✅ Sim | ✅ Sim — só o código, sem dados |
| 19 | Script roda nos dados reais localmente → results/ | 💻 Local | ❌ Não | ❌ Não |

### Exemplo real

```python
# Entrada (seu documento)
"O cliente João Silva, CPF 123.456.789-00, email joao@empresa.com"

# Após PSA (o que a IA vê)
"O cliente [NAME_7f2a], CPF [CPF_9b1c], email [EMAIL_3d8e]"

# Resultado revertido (você recebe)
"O cliente João Silva, CPF 123.456.789-00, email joao@empresa.com"
```

---

## 📄 Formatos suportados

| Formato | Extensão |
|---|---|
| Documentos Word | `.docx` |
| Planilhas Excel | `.xlsx`, `.csv` |
| PDF | `.pdf` |
| Texto puro | `.txt` |
| Dados estruturados | `.json`, `.xml` |
| E-mail | `.eml`, `.msg` |
| Imagens (OCR) | `.png`, `.jpg` |

---

## 🔍 Padrões PII detectados (70+)

- **Documentos brasileiros:** CPF, CNPJ, RG, CNH, PIS/PASEP, Título de Eleitor
- **Contato:** E-mail, telefone fixo, celular, WhatsApp
- **Localização:** Endereço completo, CEP, coordenadas GPS
- **Financeiro:** Cartão de crédito, conta bancária, agência, PIX
- **Saúde:** CRM, CRF, prontuário, convênio
- **Identificação:** Nome completo, data de nascimento, passaporte

---

## 🤖 Agentes disponíveis

| Agente | Função |
|---|---|
| **Comandante (CEO)** | Orquestra o fluxo completo de proteção |
| **PSA Guardião** | Especialista em anonimização e validação |
| **CFO** | Processamento de dados financeiros |

---

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai.git
cd psa-privacy-shield-agent-for-ai

# Instale as dependências
pip install -r requirements.txt

# Execute
python psa.py
```

### Pré-requisitos

- Python 3.10+
- Chave de API da Anthropic (Claude) ou OpenAI (ChatGPT)

---

## 🎯 Para quem é

| Setor | Caso de uso |
|---|---|
| ⚖️ **Advocacia** | Analisar contratos sem expor dados de clientes |
| 🏥 **Saúde** | Processar prontuários com sigilo médico |
| 📊 **Contabilidade / RH** | Trabalhar com CPFs e salários em segurança |
| 🏛️ **Governo** | Bases públicas com dados pessoais de cidadãos |
| 🏢 **PMEs** | Compliance LGPD sem contratar DPO |

---

## ⚖️ Conformidade

- ✅ **LGPD** — Lei Geral de Proteção de Dados (Brasil, Lei 13.709/2018)
- ✅ **GDPR** — General Data Protection Regulation (Europa)
- ✅ **Processamento local** — dados originais nunca saem do seu ambiente

---

## 🗂️ Estrutura do projeto

```
psa-privacy-shield-agent-for-ai/
├── psa.py                    # Script principal
├── anonymizer.py             # Motor de anonimização
├── text_engine.py            # Processamento de texto
├── anonymize_document.py     # Suporte a DOCX/XLSX
├── anonymize_pdf.py          # Suporte a PDF
├── anonymize_presentation.py # Suporte a PPTX
├── anonymize_email.py        # Suporte a EML/MSG
├── CLAUDE.md                 # Instruções para Claude Code
├── CHANGELOG.md              # Histórico de versões
└── docs/
    └── SKILL-SPEC.md         # Especificação técnica
```

---

## 👤 Autor

**Marcos Cruz**  
Brasília/DF — Março 2026  
Ideia original: PSA como modo nativo de privacidade em qualquer IA.

---

## 📬 Contato & Validação

Estou validando o PSA com profissionais de advocacia, saúde e contabilidade.  
Se você lida com dados sensíveis e usa IA, quero conversar.

🌐 [Site oficial](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai)  
📧 [Lista de espera](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai)

---

<div align="center">
  <sub>Built with 🛡️ in Brasília, Brasil · Co-authored with Claude (Anthropic)</sub>
</div>
