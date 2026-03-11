# PSA — Changelog e Decisoes

> **Versao:** v1
> **Data:** 2026-03-11
> **Mudancas:** Documento inicial — historico completo ate marco/2026.

---

## Regras de versionamento deste diretorio

- **Nunca sobrescrever** — sempre criar _v2, _v3, etc.
- Ao atualizar, criar nova versao mantendo a anterior intacta
- Topo de cada documento: data, versao, resumo do que mudou

---

## Linha do tempo

### v0.1 — Landing page inicial
- Landing page com waitlist e Google Forms
- Design dark theme com CSS custom (Syne + DM Sans + DM Mono)
- 6 idiomas: PT, EN, ES, ZH, HI, FR

### v0.2 — Integracao Google Forms
- Waitlist via iframe oculto (sem redirecionar pagina)
- Validacao de email no frontend

### v1.0 — Core do PSA
- `anonymizer.py`: anonimizacao de CSV/XLSX
- Deteccao de 70+ keywords sensiveis
- Faker pt_BR offline com seed aleatorio
- Cache SHA-256 para consistencia
- Validacao anti-vazamento C-01 (bloqueia + deleta)
- Text engine C-02 em colunas de texto livre
- Variacao financeira ±15%
- `test_anonymizer.py`: teste ponta a ponta com 50 clientes fake

### v2.0 — Formatos expandidos
- `anonymize_document.py`: DOCX/TXT com amostragem de paragrafos
- `anonymize_pdf.py`: PDF com pdfplumber, amostragem de paginas
- `anonymize_presentation.py`: PPTX com amostragem de slides
- `anonymize_email.py`: EML/MSG campo a campo
- `text_engine.py`: motor de regex compartilhado

### v3.0 — Interface unificada (psa.py)
- `psa.py`: dispatcher por extensao
- Deteccao automatica de formato
- Validacao de seguranca pre-execucao
- Bloqueio de diretorios protegidos

### v4.0 — File Registry
- `file_registry.py`: codigos genericos DOC_NNN
- Nomes reais nunca aparecem nas respostas do Claude
- Idempotente: mesmo arquivo = mesmo codigo
- Comandos: --register, --list-files
- `psa.py` aceita tanto codigos (DOC_001) quanto caminhos reais

### v4.1 — README profissional
- README.md com badges (Audit, Version, License, Python, LGPD, GDPR)
- Tabela dos 19 passos
- Secoes de formatos, PII, agentes, instalacao

### v4.2 — Rebrand seguranca primeiro
- Hierarquia: Seguranca > Tokens > Velocidade
- 4 Medos que o PSA resolve
- Compliance: LGPD, GDPR, HIPAA, Sigilo, Segredo industrial
- Caso real: 256.013 servidores GDF
- Beneficios como consequencias da protecao
- Badge HIPAA adicionado

### v4.3 — Hebraico (HE)
- 7o idioma adicionado a landing page
- Suporte RTL completo (direction, text-align, flex reverso, bordas)
- 69 spans traduzidos (paridade com outros idiomas)

### v5.0 — Amostragem Inteligente
- `calculate_sample_size(n_rows)` em anonymizer.py
- 5 faixas de amostragem baseadas no tamanho do arquivo
- Base estatistica: Teorema Central do Limite (n >= 30)
- --sample sobrescreve logica automatica
- Log com metricas: tamanho real, amostra, % enviado, % economizado

### v5.1 — Documentacao v5.1 + Landing page
- README, index.html e CLAUDE.md atualizados para v5.1
- Nova secao "Amostragem Estatisticamente Inteligente" na landing page
- Passo 6 da tabela atualizado em todos os idiomas
- Numeros de economia ajustados (200 linhas para GDF, 99.92%)

### v5.2 — Comando --history
- `get_history(code)` em file_registry.py
- `--history DOC_NNN` em psa.py
- Mostra todas as anonimizacoes em ordem cronologica
- Metricas por formato: PDF (paginas, entidades), planilha (linhas, colunas)

---

## Decisoes arquiteturais

### D-01: Codigos DOC_NNN em vez de hashes
**Decisao:** Usar codigos sequenciais legiveis (DOC_001) em vez de hashes.
**Motivo:** Facilidade de uso na conversa com Claude. Hash seria mais seguro mas ilegivel.

### D-02: Faker offline em vez de API
**Decisao:** Usar Faker pt_BR local em vez de API de dados sinteticos.
**Motivo:** Nenhuma chamada externa. Tudo roda offline.

### D-03: Seed aleatorio (nao deterministico)
**Decisao:** `os.urandom()` em vez de seed fixo.
**Motivo:** Mais seguro — cada execucao gera valores diferentes. Impede correlacao entre execucoes.

### D-04: Validacao anti-vazamento com delecao automatica
**Decisao:** Se detectar overlap, deletar o arquivo anonimizado e levantar excecao.
**Motivo:** Fail-safe — melhor nao gerar nada do que gerar com vazamento.

### D-05: Amostragem inteligente em vez de fixa
**Decisao:** calculate_sample_size(n) com 5 faixas em vez de fixo em 100.
**Motivo:** Evita enviar 100% de arquivos pequenos sem aviso, e otimiza para arquivos grandes.

### D-06: --history em vez de versionamento com subpastas
**Decisao:** Comando --history que busca em arquivos existentes, em vez de criar subpastas v1/, v2/.
**Motivo:** Nao quebra a estrutura existente, nao muda formato de codigos DOC_NNN, nao move arquivos. Versionamento natural por timestamp ja funciona.

### D-07: Hierarquia seguranca > tokens > velocidade
**Decisao:** Seguranca como mensagem principal, economia e velocidade como consequencias.
**Motivo:** O medo de vazamento e compliance e o que vende. Produtividade e bonus.
