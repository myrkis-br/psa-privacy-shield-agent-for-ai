# PSA — Privacy Shield Agent for AI
## Resumo do Projeto — Fase 2 (atualizado 12/03/2026 — v4)
### Status: Beta v1.0

**Autor:** Marcos Cruz — Brasília/DF
**Tagline:** Seu guarda-costas digital. Seu guardião de dados.

> **Versao Beta** — Em desenvolvimento ativo. Use como camada adicional de protecao, nunca como unica garantia de conformidade. Nao substitui assessoria juridica especializada.

---

## Identidade do Produto

- **Nome completo:** PSA - Privacy Shield Agent for AI
- **Sigla:** PSA
- **Versão atual:** v6.1 — Security Hardening + 21 Extensões
- **Posicionamento principal:** Camada de **segurança** que protege dados sensíveis *antes* de enviá-los a qualquer IA — e como consequência, economiza até 99,96% dos tokens e torna análises 30x mais rápidas
- **Compatível com:** Claude, ChatGPT, Gemini, Llama e qualquer API de IA
- **Público-alvo prioritário:** Advocacia, contabilidade/RH, saúde, governo, PMEs

---

## A Hierarquia Correta de Mensagem

> **1º Segurança** — o maior medo de toda empresa
> **2º Economia de tokens** — consequência da proteção
> **3º Velocidade** — consequência da amostragem mínima

### A frase que resume tudo:
*"PSA não é uma ferramenta de produtividade. É uma camada de segurança que, como consequência, também economiza 99% dos tokens e torna qualquer análise 30x mais rápida."*

---

## Os 4 Medos que o PSA Resolve

| Medo | Problema real | Solução PSA |
|---|---|---|
| Vazamento de dados de clientes | CPF, salário, endereço vão para servidores externos | Dados reais nunca saem — só fictícios vão à nuvem |
| Multa LGPD/GDPR | ANPD pode multar até 2% do faturamento anual | Compliance automático + log auditável de cada operação |
| Segredo industrial | Tabela de preços, clientes VIP e estratégia vão para a nuvem | Apenas dados fictícios chegam à nuvem |
| Dados treinando concorrentes | Termos de uso de IAs podem usar dados para treinar modelos | Nenhum dado real alimenta nenhum modelo |

---

## Setup Técnico

- Mac Mini M2 8GB dedicado (sem sleep, otimizado)
- Plano Anthropic Max
- Claude Code (versão atual)
- Projeto em `~/psa-project/`
- No Claude Code: `cd ~/psa-project && claude` (CLAUDE.md carrega automaticamente)
- Homebrew instalado, GitHub CLI autenticado como `myrkis-br`

---

## Fase 1 — COMPLETA

- Auditoria: 100/100 APROVADO (28/28 vulnerabilidades corrigidas)
- 5.068 linhas Python, 12 scripts, 3 agentes, 11 formatos, 70+ keywords
- Teste real: base GDF 256k linhas → amostra 100 → **zero vazamentos**
- Fluxo: Interceptação → Registro (DOC_NNN) → Anonimização → Validação → Execução
- Agentes: Comandante (CEO), PSA Guardião (anonimiza), CFO (financeiro)
- Scripts: psa.py, file_registry.py, anonymizer.py, text_engine.py, anonymize_document/pdf/presentation/email.py
- Docs: CLAUDE.md, CHANGELOG.md, docs/SKILL-SPEC.md

---

## Como o PSA Funciona — Os 19 Passos

> **"16 de 19 passos rodam 100% local. Seus dados reais jamais saem do seu computador."**
> **"Nem o nome do seu arquivo sai do computador. Seus dados começam protegidos do primeiro ao último passo."**
> **Consequência:** economia de até 99,96% dos tokens
> **Consequência:** análises de 15 min em 30 segundos

| Passo | O que acontece | Local / Nuvem | Token? | Dados saem? |
|---|---|---|---|---|
| 1 | Nome do arquivo protegido por código genérico (DOC_001) via file_registry | Local | Nao | Nao |
| 2 | PSA invoca o psa.py via código genérico | Local | Nao | Nao |
| 3 | Valida segurança do arquivo | Local | Nao | Nao |
| 4 | Detecta extensão e escolhe script correto (21 extensões) | Local | Nao | Nao |
| 4b | **Risk Engine classifica risco LGPD 1-10 [v6.0]** | Local | Nao | Nao |
| 4c | **Seleciona modo por risco: ECO/PADRÃO/MÁXIMO [v6.0]** | Local | Nao | Nao |
| 5 | Lê o arquivo real do disco | Local | Nao | Nao |
| 6 | Faz amostragem inteligente (ajustada pelo risk_score) | Local | Nao | Nao |
| 7 | Detecta campos/tags sensíveis (70+ keywords + tag detection) | Local | Nao | Nao |
| 8 | Renomeia colunas para COL_A, COL_B... (planilhas) | Local | Nao | Nao |
| 9 | Anonimiza valores com Faker pt_BR offline | Local | Nao | Nao |
| 10 | Varia valores financeiros em ±15% | Local | Nao | Nao |
| 11 | Escaneia textos livres e substitui via regex | Local | Nao | Nao |
| 12 | Validação anti-vazamento — detectou dado real? Deleta tudo | Local | Nao | Nao |
| 13 | Salva arquivo anonimizado em data/anonymized/ | Local | Nao | Nao |
| 14 | Salva mapa de correspondência em data/maps/ (ou deleta com --no-map) | Local | Nao | Nao |
| 14b | **Gera hash SHA256 do arquivo anonimizado [NOVO v6.1]** | Local | Nao | Nao |
| 14c | **Grava entrada no audit trail (audit_trail.jsonl) [NOVO v6.1]** | Local | Nao | Nao |
| 15 | **Gera relatório RIPD automático (Art. 38 LGPD) [v6.0]** | Local | Nao | Nao |
| 16 | Claude/IA lê o arquivo anonimizado | Nuvem | Sim | Só dados fictícios |
| 17 | Claude/IA realiza análise e responde | Nuvem | Sim | Só resultados fictícios |
| 18 | Claude/IA gera script Python para rodar localmente | Nuvem | Sim | Só o código, sem dados |
| 19 | Script roda nos dados reais localmente → results/ | Local | Nao | Nao |

**Resumo:** 18 de 22 passos são 100% locais. Nos 3 passos em nuvem, nenhum dado real é transmitido.

---

## Conformidade Garantida

| Regulação | PSA |
|---|---|
| **LGPD** (Brasil) | Dados pessoais nunca saem sem anonimização |
| **GDPR** (Europa) | Anonimização antes de qualquer envio |
| **HIPAA** (Saúde EUA) | Prontuários ficam locais |
| **Sigilo profissional** | Dados de clientes nunca saem |
| **Segredo industrial** | Só fictícios vão à nuvem |

---

## Fase 2 — Em andamento

### Conquistas da Fase 2 — Dia 1 (10/03/2026)
- Repositório GitHub publicado — `github.com/myrkis-br/psa-privacy-shield-agent-for-ai`
- Release v1.0.0 publicada oficialmente
- Landing page ao vivo — `myrkis-br.github.io/psa-privacy-shield-agent-for-ai`
- Lista de espera integrada ao Google Sheets e testada
- 6 idiomas: PT, EN, ES, ZH, HI, FR
- Tabela dos 19 passos publicada no README e na landing page
- `file_registry.py` — nome do arquivo protegido desde o passo 1

### Conquistas da Fase 2 — Dia 2 (11/03/2026) — Risk Engine v6.0
- **Risk Engine v6.0 completo e testado em produção**
- 4 novos módulos: classifier.py, pattern_enricher.py, ripd_report.py, psa.py integrado
- Classificação automática de risco LGPD 1-10 (Resolução ANPD nº 4/2023)
- Relatório RIPD automático (Art. 38 LGPD) com multa potencial
- Seleção de modo ECO/PADRÃO/MÁXIMO por risco
- **JSON suporte completo:** anonymize_json.py + classifier JSON
  - DOC_020: 358 entidades anonimizadas, ZERO vazamentos
  - Classifier corrigido de 1/10 → 7/10 (GRAVE com combined PII bonus)
  - Travessia recursiva de objetos/arrays aninhados
  - Detecção por chave exata + fragmento + contexto (user.id = PII)
- **XML/NF-e suporte completo:** anonymize_xml.py + classifier XML
  - DOC_021: 28 entidades anonimizadas, ZERO vazamentos
  - Parser com suporte a namespaces SEFAZ (nfeProc, NFe, infNFe)
  - 14 tags sensíveis + 60 tags preservadas (IDs fiscais)
  - text_engine em infCpl/xMotivo (PII embarcado em texto livre)
- **9 formatos validados:** PDF, PPTX, DOCX, XLSX, EML, CSV, TXT, JSON, XML
- **7.300+ linhas Python** em 13 scripts core + 3 agentes

### Conquistas da Fase 2 — Dia 3 (12/03/2026) — Security Hardening v6.1
- **6 novos formatos com ZERO vazamentos:** HTML, YAML, SQL, LOG, VCF, PARQUET
- **Testado com dados reais da Câmara dos Deputados** (DOCs 020–036)
- **Auditoria de segurança completa: 82/100** (7 áreas avaliadas)
- **5 CVEs corrigidos:**
  - CVE-S-01: SHA256 + hash de integridade para cada arquivo anonimizado
  - CVE-S-02: Audit trail append-only (audit_trail.jsonl)
  - CVE-S-03: `--no-map` para deletar mapa de correspondência automaticamente
  - CVE-S-04: `--purge-maps` para limpar todos os mapas existentes
  - CVE-S-05: Validação anti-injection em nomes de arquivo
- **Novos scripts:** anonymize_html.py, anonymize_yaml.py, anonymize_sql.py, anonymize_log.py, anonymize_vcf.py, anonymize_parquet.py
- **Novos comandos CLI:**
  - `--no-map` — não salva mapa de correspondência (modo paranóico)
  - `--purge-maps` — deleta todos os mapas existentes em data/maps/
- **Placar final: 21 extensões / 18 formatos únicos**
- **Decisão estratégica: GPT Store (ChatGPT) primeiro, depois Gemini Workspace**
- **RTF e ODT já suportados** (anonymize_rtf.py, anonymize_odt.py)

### Placar completo de formatos v6.1

| # | Formato | Extensões | Script |
|---|---------|-----------|--------|
| 1 | Planilha CSV | .csv | anonymizer.py |
| 2 | Planilha Excel | .xlsx, .xls | anonymizer.py |
| 3 | Documento Word | .docx | anonymize_document.py |
| 4 | Texto puro | .txt | anonymize_document.py |
| 5 | PDF | .pdf | anonymize_pdf.py |
| 6 | Apresentação | .pptx | anonymize_presentation.py |
| 7 | E-mail EML | .eml | anonymize_email.py |
| 8 | E-mail MSG | .msg | anonymize_email.py |
| 9 | JSON | .json | anonymize_json.py |
| 10 | XML/NF-e | .xml | anonymize_xml.py |
| 11 | RTF | .rtf | anonymize_rtf.py |
| 12 | ODT | .odt | anonymize_odt.py |
| 13 | HTML | .html | anonymize_html.py |
| 14 | YAML | .yaml, .yml | anonymize_yaml.py |
| 15 | SQL | .sql | anonymize_sql.py |
| 16 | Log | .log | anonymize_log.py |
| 17 | vCard | .vcf | anonymize_vcf.py |
| 18 | Parquet | .parquet | anonymize_parquet.py |

**Total: 21 extensões / 18 formatos únicos**

### Placar completo de testes v6.1

| DOC | Tipo | Score | Entidades | Vazamentos | Multa evitada |
|-----|------|-------|-----------|------------|---------------|
| DOC_016 | RH CSV (50 func.) | 7/10 GRAVE | 15 | ZERO | R$ 500k–5M |
| DOC_017 | BACEN CSV (4.560 serv.) | 5/10 MÉDIA | 3 | ZERO | R$ 50k–500k |
| DOC_019 | Laudo médico DOCX | 9/10 GRAVE | 85 | ZERO | R$ 500k–5M |
| DOC_020 | API payments JSON | 7/10 GRAVE | 358 | ZERO | R$ 500k–5M |
| DOC_021 | NF-e XML | 6/10 MÉDIA | 28 | ZERO | R$ 50k–500k |
| DOC_022–036 | Câmara dos Deputados (HTML, YAML, SQL, LOG, VCF, PARQUET) | 5-8/10 | Variado | ZERO | R$ 50k–5M |

**Dados vazados em todos os testes: ZERO**

### Auditoria de Segurança v6.1 — Score 82/100

| Área | Score | Detalhe |
|------|-------|---------|
| Integridade de dados | ✅ | SHA256 em cada arquivo anonimizado |
| Audit trail | ✅ | audit_trail.jsonl append-only |
| Controle de mapas | ✅ | --no-map + --purge-maps |
| Anti-vazamento | ✅ | Validação + deleção automática |
| Anti-injection | ✅ | Validação de nomes de arquivo |
| Encoding | ✅ | Auto-detecção multi-encoding |
| RIPD automático | ✅ | Art. 38 LGPD compliance |

### Próximos passos
- [ ] Criar GPT customizado para o ChatGPT (GPT Store)
- [ ] Configurar integração Gemini Workspace
- [ ] Postar no LinkedIn (3 versões prontas — storytelling, direto, provocativo)
- [ ] Atualizar README e landing page com v6.1 + 21 extensões
- [ ] Adicionar calculadora de impacto na landing page
- [ ] Configurar Google Analytics na landing page
- [ ] Prospectar primeiros clientes (advocacia prioritária)
- [ ] Ativar enricher com API key real
- [ ] Piloto com cliente real

---

## Links importantes

| Recurso | URL |
|---|---|
| GitHub | github.com/myrkis-br/psa-privacy-shield-agent-for-ai |
| Site | myrkis-br.github.io/psa-privacy-shield-agent-for-ai |
| Release | github.com/myrkis-br/psa-privacy-shield-agent-for-ai/releases/tag/v1.0.0 |
| Google Forms (lista espera) | docs.google.com/forms/d/e/1FAIpQLSdTG9WkJVGGzTLUq7qFLTLJjzX9J9YMY5BnhWu0kXTmsunH6w/viewform |

---

## Conceito original
*PSA como opção nativa nas configurações de qualquer IA: "Modo PSA ativo — dados anonimizados antes do envio". Ideia original de Marcos Cruz, março 2026.*
