# Changelog — PSA (Privacy Shield Agent)

## [6.2.0] — 2026-03-13 — Operação CISO

### Segurança — Credenciais removidas do histórico Git
- Varredura completa com **gitleaks** + **detect-secrets**: 3 leaks no histórico, 15 nos arquivos atuais
- `gerar_testes_gov.py` removido do histórico Git via **git-filter-repo**: 10 credenciais eliminadas
- `gerar_email_corporativo.py` removido do histórico Git via **git-filter-repo**: 1 token JWT eliminado
- Force push com histórico limpo: **0 leaks** em 23 commits

### Segurança — Hardening permanente
- **Pre-commit hook** gitleaks v8.18.2 instalado — bloqueia commits com credenciais
- Credenciais fictícias em scripts de teste substituídas por `os.environ.get()` + `_TEST_CREDS`
- `.env.example` criado com 10 variáveis de ambiente (sem valores)
- `.gitignore` atualizado: `*.env`, `.env.*`, `secrets.yaml`, `secrets.json`, exceção para `.env.example`

### Segurança — Política formal
- **SECURITY.md** criado: política de zero credenciais, pre-commit obrigatório, como reportar vulnerabilidades, histórico de auditorias
- 6 permissões de risco revogadas do Claude Code (`pip3 install:*`, `git push:*`, `cat logs/`, scripts inline)

### Documentação
- README.md: corrigido Python 3.9+, estrutura de diretórios, instruções de instalação com pre-commit
- CLAUDE.md: nova seção 11 (Segurança Operacional)
- PSA-Resumo-Fase02_v4.md: Dia 4 — operação CISO
- SECURITY_AUDIT_v6.0.md: seção sobre credenciais hardcoded

### Arquivos Modificados
- `scripts/gerar_testes_gov.py` — `_TEST_CREDS` dict via `os.environ.get()`
- `scripts/gerar_email_corporativo.py` — `_TEST_TOKEN` via `os.environ.get()`
- `.gitignore` — padrões de segurança adicionados
- `~/.claude/settings.local.json` — 6 permissões revogadas

### Arquivos Criados
- `SECURITY.md` — política formal de segurança
- `.env.example` — template de variáveis de ambiente
- `.pre-commit-config.yaml` — hook gitleaks

---

## [6.1.0] — 2026-03-12 — Security Hardening + 6 novos formatos

### Novos formatos (ZERO vazamentos em todos)
- **HTML**: preserva estrutura, anonimiza texto e atributos PII
- **YAML**: detecta chaves secretas (password, token, etc.) + text_engine
- **SQL**: rastreia blocos INSERT multi-linha, anonimiza string literals
- **LOG**: anonimiza IPs, tokens, sessões + text_engine por linha
- **VCF**: anonimiza campos vCard (FN, N, EMAIL, TEL, ADR, ORG, NOTE)
- **PARQUET**: classificação automática de colunas, Faker pt_BR, C-01/C-02

### Segurança — Score 82/100
- **CVE-S-01**: SHA256 + hash de integridade para cada arquivo anonimizado
- **CVE-S-02**: Audit trail append-only (`logs/audit_trail.jsonl`)
- **CVE-S-03**: `--no-map` para deletar mapa de correspondência automaticamente
- **CVE-S-04**: `--purge-maps` para limpar todos os mapas existentes
- **CVE-S-05**: Validação anti-injection em nomes de arquivo

### Novos scripts
- `anonymize_html.py`, `anonymize_yaml.py`, `anonymize_sql.py`
- `anonymize_log.py`, `anonymize_vcf.py`, `anonymize_parquet.py`
- `anonymize_rtf.py`, `anonymize_odt.py`

### Placar final
- **21 extensões / 18 formatos únicos**
- Testado com dados reais da Câmara dos Deputados (DOCs 020–036)

---

## [2.0.0] — 2026-03-10

### Auditoria de Segurança
- **v1**: Score 62/100 — REPROVADO CONDICIONAL (28 vulnerabilidades abertas)
- **v2**: Score 100/100 — APROVADO (28/28 corrigidas)

### Correções CRÍTICAS
- **C-01**: `_validate_no_leakage` agora BLOQUEIA saída, DELETA arquivo e levanta `LeakageError`
- **C-02**: `text_engine` aplicado em colunas de texto livre de planilhas (detecção automática)
- **C-03**: Regex de nomes reescrito — ALL-CAPS, honoríficos (Dr./Dra./Sr./Prof./Des./Min.), sufixos (Filho/Junior/Neto)

### Correções ALTAS (10)
- Seed aleatório via `os.urandom(8)` (não mais `Faker.seed(42)`)
- 30+ keywords sensíveis adicionadas (pis, pasep, ctps, bruto, líquido, lat/lng, etc.)
- Word-boundary match para keywords curtas (rg, uf, tel)
- Type hints corrigidos para Python 3.9
- Regex para RG, PIS/PASEP/NIS, CTPS, endereços
- DOCX: extração de headers/footers
- TXT: fallback de encoding (utf-8 → latin-1 → cp1252)
- Email: aviso sobre conteúdo de anexos não escaneado
- `_security_check` expandido (bloqueia maps/, samples/, logs/, anonymized/)
- Security check aplicado em processamento de pastas

### Correções MÉDIAS (14) e BAIXAS (1)
- `_NOT_A_NAME` expandido (26 estados, instituições, termos financeiros)
- Datas ISO (2024-01-31) detectadas
- MD5 → SHA-256 para cache keys
- PII removida de logs (tokens apenas, nunca originais)
- PDF: default 10 páginas, erros de tabela logados, aviso para PDFs escaneados
- HTML entities: `html.unescape()` em vez de subset manual
- CLAUDE.md: contradição Seção 4 vs 5 resolvida, logs/ protegido, seção técnica adicionada
- Coordenadas lat/lng anonimizadas (±0.05 graus)

### Arquivos Modificados
- `scripts/text_engine.py` — motor de regex reescrito
- `scripts/anonymizer.py` — bloqueio de vazamento, text_engine em texto livre, keywords expandidas
- `scripts/psa.py` — security check expandido, default PDF 10 páginas
- `scripts/anonymize_document.py` — headers/footers, encoding fallback, logs sem PII
- `scripts/anonymize_email.py` — aviso anexos, logs sem PII, html.unescape()
- `scripts/anonymize_pdf.py` — default 10 pags, erros logados, aviso OCR
- `CLAUDE.md` — contradições resolvidas, logs/ protegido, seção técnica

### Arquivos Criados
- `results/auditoria_psa.html` — relatório v1 (62/100)
- `results/auditoria_psa_v2.html` — relatório v2 (100/100)
- `scripts/gerar_auditoria_v2.py` — gerador do relatório v2

---

## [1.0.0] — 2026-03-10

### Criação do Projeto
- Estrutura de diretórios (data/real, anonymized, maps, samples)
- `scripts/anonymizer.py` — anonimizador de CSV/XLSX
- `scripts/text_engine.py` — motor de regex para texto livre
- `scripts/anonymize_document.py` — DOCX/TXT
- `scripts/anonymize_pdf.py` — PDF via pdfplumber
- `scripts/anonymize_presentation.py` — PPTX
- `scripts/anonymize_email.py` — EML/MSG
- `scripts/psa.py` — interface unificada
- `scripts/test_anonymizer.py` — teste ponta a ponta
- `CLAUDE.md` — regras de protocolo
- `agents/` — definições de agentes (comandante, psa-guardião, cfo)

### Análises GDF
- `scripts/analise_completa_gdf.py` — análise de remuneração com teto STF, acúmulo de cargos, classificação legal
- `scripts/analise_folha_por_orgao.py` — top 5 órgãos por folha de pagamento
- `results/analise_remuneracao_gdf.html` — relatório completo
