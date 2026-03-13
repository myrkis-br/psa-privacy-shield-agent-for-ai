# Política de Segurança — PSA (Privacy Shield Agent)

**Versão**: 1.0
**Data**: 2026-03-13
**Autor**: Marcos Cruz (Myrkis BR)
**Aprovação**: CISO Mode — Auditoria completa v6.1

---

## 1. Regra Zero — Nenhuma Credencial no Código

> **É terminantemente proibido incluir credenciais, tokens, senhas,
> chaves de API ou qualquer segredo diretamente no código-fonte.**

Isso inclui:
- Senhas de banco de dados, Redis, SMTP
- Tokens JWT, API keys, webhooks secrets
- Chaves AWS (Access Key / Secret Key)
- Certificados e chaves privadas
- DSNs com credenciais embutidas
- Credenciais "fictícias" que pareçam reais

### Como fazer corretamente

```python
# ERRADO — nunca faça isso
password = "M1nh@S3nh@Pr0d#2025"

# CORRETO — use variável de ambiente
import os
password = os.environ.get("PSA_TEST_DB_PASS", "PLACEHOLDER")
```

Consulte o arquivo `.env.example` para a lista completa de variáveis.

---

## 2. Pre-commit Obrigatório — Gitleaks

Todo commit neste repositório passa automaticamente pelo **gitleaks**,
que escaneia o código em busca de credenciais antes de permitir o commit.

### Configuração (já instalada)

```yaml
# .pre-commit-config.yaml
repos:
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.18.2
  hooks:
  - id: gitleaks
```

### Regras

- **Nenhum desenvolvedor pode desabilitar o hook** (`--no-verify` é proibido)
- Se o gitleaks bloquear um commit, **corrija o código** — nunca ignore o alerta
- Novos colaboradores devem rodar `pre-commit install` antes do primeiro commit

---

## 3. Uso de Variáveis de Ambiente (.env)

### Regras

1. Credenciais devem ser armazenadas em arquivos `.env` (nunca commitados)
2. O `.gitignore` já protege: `.env`, `*.env`, `.env.*`, `secrets.yaml`, `secrets.json`
3. O arquivo `.env.example` lista todas as variáveis necessárias (sem valores)
4. Cada desenvolvedor mantém seu próprio `.env` local

### Fluxo para novos desenvolvedores

```bash
cp .env.example .env
# Preencher os valores no .env local
pre-commit install
```

---

## 4. Diretórios Protegidos

Os seguintes diretórios contêm dados sensíveis e são protegidos pelo `.gitignore`:

| Diretório | Conteúdo | Status |
|-----------|----------|--------|
| `data/real/` | Arquivos originais com PII | Nunca commitado |
| `data/maps/` | Mapas real ↔ fake | Nunca commitado |
| `data/samples/` | Amostras pré-anonimização | Nunca commitado |
| `data/anonymized/` | Dados anonimizados | Nunca commitado |
| `logs/` | Logs com possível PII residual | Nunca commitado |

---

## 5. Responsabilidades do Desenvolvedor

Antes de cada commit, o desenvolvedor deve verificar:

- [ ] Não há senhas, tokens ou chaves no código
- [ ] Variáveis sensíveis usam `os.environ.get()`
- [ ] O pre-commit hook está instalado e ativo
- [ ] Arquivos `.env` não estão sendo commitados
- [ ] Dados de `data/real/` não estão sendo expostos
- [ ] Nomes de arquivos reais não aparecem em mensagens de commit

---

## 6. Como Reportar Vulnerabilidades

Se você encontrar uma vulnerabilidade de segurança neste projeto:

1. **Não abra uma issue pública** — vulnerabilidades devem ser tratadas em privado
2. Envie um email para: **myrkis@gmail.com**
3. Inclua:
   - Descrição da vulnerabilidade
   - Passos para reproduzir
   - Impacto potencial
   - Sugestão de correção (se houver)
4. Prazo de resposta: **48 horas**

---

## 7. Permissões do Claude Code

Em 13/03/2026, foi realizada uma revisão completa das permissões do Claude Code.

### Permissões revogadas (risco)

| Permissão | Motivo |
|-----------|--------|
| `pip3 install:*` | Wildcard — permitia instalar qualquer pacote sem confirmar |
| `git push:*` | Wildcard — permitia push para qualquer branch sem confirmar |
| `cat logs/audit_trail.jsonl` | Logs podem conter PII residual |
| 3x `python3 -c` / `python3 << PYEOF` | Scripts inline longos — impossíveis de revisar no prompt |

### Permissões mantidas (56)

- Execuções específicas do PSA (`python3 scripts/psa.py DOC_NNN ...`)
- `git add:*` (risco baixo — staging não publica nada)
- WebSearch e WebFetch para domínios governamentais
- Ferramentas de segurança (gitleaks, detect-secrets)

### Política

- Nenhuma permissão wildcard deve ser concedida permanentemente
- Cada push deve ser aprovado individualmente
- Instalação de pacotes deve ser aprovada individualmente

---

## 8. Histórico de Auditorias

| Data | Ação | Resultado |
|------|------|-----------|
| 2026-03-13 | Varredura completa com gitleaks + detect-secrets | 3 leaks encontrados no histórico Git |
| 2026-03-13 | Remoção de `gerar_testes_gov.py` do histórico (filter-repo) | 10 credenciais eliminadas |
| 2026-03-13 | Remoção de `gerar_email_corporativo.py` do histórico (filter-repo) | 1 token JWT eliminado |
| 2026-03-13 | Force push com histórico limpo | 0 leaks confirmado |
| 2026-03-13 | Hardening: pre-commit gitleaks + os.environ.get() | Proteção permanente ativada |
| 2026-03-13 | Política formal SECURITY.md | Este documento |

---

## 9. Ferramentas de Segurança Instaladas

| Ferramenta | Versão | Função |
|------------|--------|--------|
| gitleaks | v8.18.2 | Detecção de segredos no código e histórico Git |
| detect-secrets | 1.5.0 | Varredura complementar de segredos em arquivos |
| pre-commit | instalado | Framework de hooks pré-commit |
| git-filter-repo | instalado | Reescrita segura do histórico Git |

---

*Este documento deve ser revisado a cada nova auditoria de segurança.*
