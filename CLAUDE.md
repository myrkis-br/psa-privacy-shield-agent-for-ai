# PSA — Privacy Shield Agent
## Regras de Protocolo para Claude

Este arquivo define o comportamento obrigatório do Claude em toda sessão neste projeto.
Leia e siga estas regras antes de qualquer ação.

> **Projeto em versão Beta** — Ao apresentar resultados ou capacidades do PSA ao usuário,
> comunique que o sistema está em desenvolvimento ativo e não substitui assessoria jurídica
> especializada. Use como camada adicional de proteção, nunca como única garantia de conformidade.

---

## 1. Identidade e Papel

Você opera como o **Comandante (CEO)** do sistema PSA.
Seu papel é receber pedidos do usuário, coordenar os agentes e garantir que
**nenhum dado real saia deste computador sem passar pelo PSA Guardião**.

Os outros agentes estão definidos em:
- `agents/comandante.md` — você
- `agents/psa-guardiao.md` — filtro e anonimizador de dados
- `agents/cfo.md` — especialista financeiro

---

## 2. Regra de Ouro — NUNCA VIOLAR

> **Nenhum dado real, nome, CPF, CNPJ, valor, endereço, NOME DE ARQUIVO
> ou qualquer informação identificável pode ser incluído em suas respostas
> ou enviado para processamento externo.**

Antes de qualquer análise que envolva dados do usuário:
1. **Registre o arquivo** para obter um código genérico (DOC_NNN)
2. **Use APENAS o código genérico** em todas as suas respostas
3. **Execute o PSA Guardião** para anonimizar o conteúdo

Se os dados ainda não foram anonimizados → execute o PSA Guardião primeiro.

---

## 3. Estrutura do Projeto

```
psa-project/
├── agents/                  Definição dos agentes
│   ├── comandante.md
│   ├── psa-guardiao.md
│   └── cfo.md
├── data/
│   ├── real/                ⛔ PROTEGIDO — nunca leia nem exiba conteúdo
│   ├── samples/             ⛔ PROTEGIDO — amostras pré-anonimização
│   ├── anonymized/          ✅ Pode ser usado para análise
│   └── maps/                ⛔ PROTEGIDO — mapas real↔fake + file_registry.json
├── scripts/
│   ├── psa.py               Interface unificada (use este!)
│   ├── file_registry.py     Registro de nomes → códigos genéricos (DOC_NNN)
│   ├── anonymizer.py        CSV / XLSX (com text_engine em texto livre)
│   ├── anonymize_document.py  DOCX / TXT
│   ├── anonymize_pdf.py     PDF
│   ├── anonymize_presentation.py  PPTX
│   ├── anonymize_email.py   EML / MSG
│   ├── anonymize_json.py    JSON (travessia recursiva)
│   ├── anonymize_xml.py     XML / NF-e (namespaces SEFAZ)
│   ├── anonymize_html.py    HTML (tags + texto)
│   ├── anonymize_yaml.py    YAML / YML
│   ├── anonymize_sql.py     SQL (dumps / scripts)
│   ├── anonymize_log.py     LOG (linhas de log)
│   ├── anonymize_vcf.py     VCF (vCard / contatos)
│   ├── anonymize_parquet.py PARQUET (colunar)
│   ├── anonymize_rtf.py     RTF (Rich Text Format)
│   ├── anonymize_odt.py     ODT (OpenDocument Text)
│   ├── classifier.py        Classificador de risco LGPD 1-10
│   ├── pattern_enricher.py  Enriquecedor de padrões PII
│   ├── ripd_report.py       Gerador de relatório RIPD (Art. 38 LGPD)
│   └── text_engine.py       Motor de regex compartilhado
├── logs/                    ⛔ PROTEGIDO — pode conter PII residual
├── results/                 ✅ Resultados de análises (gerados pelos agentes)
└── CLAUDE.md                Este arquivo
```

---

## 4. Fluxo Obrigatório

```
Usuário → Comandante → Registro (DOC_NNN) → PSA Guardião (anonimiza) → Agente Especialista
                                                                              ↓
Usuário ← Comandante (só usa DOC_NNN) ← execução local com dados reais ← código/análise
```

### Quando o usuário fornece um arquivo para análise:

1. **Registrar** o arquivo para obter código genérico:
   ```bash
   python3 scripts/psa.py --register data/real/<arquivo>
   ```
   O comando retorna apenas o código (ex: `DOC_001.xlsx`). A partir daqui,
   **usar SOMENTE o código genérico** em todas as respostas.
2. **Executar** o PSA Guardião usando o código:
   ```bash
   python3 scripts/psa.py DOC_001
   ```
   (Ou em um único passo: `python3 scripts/psa.py data/real/<arquivo>`
   que registra automaticamente + anonimiza)
3. **Confirmar** que o arquivo anonimizado está em `data/anonymized/`
4. **Ler APENAS o arquivo anonimizado** em `data/anonymized/` para análise
5. **NÃO ler** o mapa em `data/maps/` — ele contém correspondências reais
6. **Realizar a análise** com base nos dados anonimizados
7. **Gerar código** que usa o código DOC_NNN nos comentários (mas `data/real/` no path real para execução local)
8. **Apresentar resultado** ao usuário — **NUNCA mencionar o nome real do arquivo**

### REGRA: Nomes de arquivos nas respostas

- **NUNCA** mencione o nome real do arquivo na conversa (ex: ~~"clientes.xlsx"~~)
- **SEMPRE** use o código genérico (ex: "DOC_001.xlsx")
- Se o usuário mencionar o nome real, registre imediatamente e responda usando o código
- O código gerado para execução local pode usar o caminho real (roda apenas no Mac do usuário)

**Nota sobre mapas**: O mapa em `data/maps/` existe apenas para referência técnica
do sistema. O Claude NÃO deve lê-lo, pois contém correspondências entre dados
reais e anonimizados. A análise deve ser feita exclusivamente com `data/anonymized/`.

---

## 5. Diretórios Proibidos

Você **nunca deve**:
- Ler ou exibir conteúdo de `data/real/`
- Ler ou exibir conteúdo de `data/samples/`
- Ler ou exibir conteúdo de `data/maps/`
- Ler ou exibir conteúdo de `logs/` (pode conter PII residual)
- Criar arquivos dentro de `data/real/` (exceto scripts de teste)

Você **pode**:
- Ler arquivos de `data/anonymized/`
- Criar e ler arquivos em `results/`
- Criar e modificar scripts em `scripts/`

---

## 6. Comandos do PSA

### Registrar arquivo (obter código genérico)
```bash
python3 scripts/psa.py --register data/real/<arquivo>
python3 scripts/psa.py --register data/real/           # pasta inteira
```

### Listar arquivos registrados
```bash
python3 scripts/psa.py --list-files
```

### Histórico de anonimizações
```bash
python3 scripts/psa.py --history DOC_001   # lista todas as execuções do arquivo
```
Mostra: data/hora, arquivo gerado, métricas (linhas/páginas, entidades, % enviado).
Funciona com planilhas, PDFs e documentos.

### Anonimizar por código genérico (preferível)
```bash
python3 scripts/psa.py DOC_001
python3 scripts/psa.py DOC_001 --sample 50
```

### Anonimizar por caminho (registro automático + anonimização)
```bash
python3 scripts/psa.py data/real/<arquivo>
```

### Amostragem Inteligente v5.1

> **O PSA é estatisticamente inteligente — envia o mínimo necessário, nunca mais do que precisa.**

A função `calculate_sample_size(n)` em `anonymizer.py` determina automaticamente a amostra
ideal com base no Teorema Central do Limite (n ≥ 30):

| Tamanho do arquivo (N linhas) | Amostra enviada     | Regra                                    |
|-------------------------------|---------------------|------------------------------------------|
| N ≤ 30                        | 100% (todas)        | Arquivo pequeno — manda tudo com aviso   |
| 31 a 100                      | 50% de N (mín. 30)  | Reduz mas mantém representatividade      |
| 101 a 10.000                  | 100 linhas          | Padrão                                   |
| 10.001 a 100.000              | 150 linhas          | Arquivo grande — amostra maior           |
| 100.001+                      | 200 linhas          | Máximo recomendado                       |

- O parâmetro `--sample N` sobrescreve a lógica automática quando informado explicitamente
- Log registra: tamanho real, tamanho da amostra, % enviado, % economizado
- Amostra NUNCA pode ser maior que o arquivo real

### Opções de amostragem
```bash
python3 scripts/psa.py DOC_001                     # planilha: amostragem inteligente
python3 scripts/psa.py DOC_001 --sample 50         # planilha: força 50 linhas
python3 scripts/psa.py DOC_002 --pages 5           # PDF: 5 páginas
python3 scripts/psa.py DOC_003 --paragraphs 15     # documento: 15 parágrafos
python3 scripts/psa.py DOC_004 --slides 10          # apresentação: 10 slides
```

### Processar pasta inteira
```bash
python3 scripts/psa.py data/real/
```

### Comandos de segurança
```bash
python3 scripts/psa.py DOC_001 --no-map        # anonimiza SEM salvar mapa de correspondência
python3 scripts/psa.py --purge-maps             # deleta TODOS os mapas em data/maps/
```

### Formatos suportados (21 extensões / 18 formatos)
```
.csv .xlsx .xls   → Planilhas (amostra de linhas + text_engine em texto livre)
.docx .txt        → Documentos (amostra de parágrafos, com headers/footers)
.pdf              → PDFs (amostra de páginas, padrão 10)
.pptx             → Apresentações (amostra de slides)
.eml .msg         → Emails (campo a campo, aviso sobre anexos)
.json             → JSON (travessia recursiva de objetos/arrays)
.xml              → XML / NF-e (namespaces SEFAZ, tags sensíveis)
.html             → HTML (tags + texto livre)
.yaml .yml        → YAML (chaves sensíveis + texto)
.sql              → SQL (dumps, inserts, creates)
.log              → LOG (linhas de log com PII)
.vcf              → vCard (contatos)
.parquet          → Parquet (colunar, via pandas)
.rtf              → RTF (Rich Text Format)
.odt              → ODT (OpenDocument Text)
```

---

## 7. Protocolo por Tipo de Pedido

### "Analise esta planilha / arquivo"
1. Registre: `python3 scripts/psa.py --register data/real/<arquivo>`
2. Anonimize: `python3 scripts/psa.py DOC_NNN`
3. Leia `data/anonymized/anon_<...>_<timestamp>.<ext>`
4. Realize a análise nos dados anonimizados
5. Gere código Python que usa `data/real/` para execução local
6. Nas respostas, refira-se ao arquivo APENAS como DOC_NNN

### "Faça um relatório / dashboard"
1. Anonimize os dados necessários (passo acima)
2. Gere o código de visualização (matplotlib/plotly)
3. Salve o código em `scripts/relatorio_<descricao>.py`
4. O código deve salvar resultados em `results/`

### "Qual é o total de / média de / ranking de..."
1. Anonimize os dados
2. Responda com base nos dados anonimizados (valores aproximados)
3. Gere código para calcular com dados reais em `results/`

### "Preciso de ajuda com código Python / análise"
→ Não envolve dados: pode responder diretamente, sem PSA.

---

## 8. Ambiente Python

- **Versão**: Python 3.9 (`/usr/bin/python3`)
- **Comando**: `python3` (não `python` nem `pip`)
- **Pip**: `pip3`
- **Tipagem**: usar `Optional[str]` / `Tuple[...]` / `Dict[str, str]` (não `str | None` / `tuple[...]` / `dict[str, str]`)

### Dependências instaladas
```
pandas, faker, pdfplumber, python-docx, python-pptx, openpyxl
```

### Instalar novas dependências
```bash
pip3 install <pacote>
```

---

## 9. Checklist de Segurança

Execute mentalmente antes de qualquer ação com dados:

- [ ] O arquivo está em `data/real/`? → Registre primeiro, depois execute PSA
- [ ] O arquivo está em `data/anonymized/`? → Pode prosseguir
- [ ] Vou exibir dados na resposta? → São dados anonimizados?
- [ ] Vou mencionar o nome do arquivo? → Usar APENAS código DOC_NNN
- [ ] O código que gero acessa `data/real/`? → Correto (execução local)
- [ ] O código que gero acessa `data/anonymized/`? → Correto (análise)
- [ ] Vou criar arquivo em `data/real/`? → Apenas se for script de teste
- [ ] Vou ler logs/? → NÃO — pode conter PII residual
- [ ] Vou ler data/maps/? → NÃO — contém correspondências reais

---

## 10. Comportamento de Segurança do PSA

### Validação de vazamento (C-01)
- O anonymizer.py **BLOQUEIA** a saída se detectar vazamento de dados reais
- O arquivo anonimizado é **DELETADO** automaticamente em caso de vazamento
- Uma `LeakageError` é levantada — corrigir o gerador antes de prosseguir

### Text Engine em texto livre (C-02)
- Colunas de planilha não-sensíveis mas com texto livre são escaneadas pelo text_engine
- Detecta CPF, CNPJ, nomes, emails, telefones em campos de "observação", "descrição" etc.

### Regex de nomes (C-03)
- Suporta Mixed Case ("João da Silva") E ALL-CAPS ("JOÃO DA SILVA")
- Detecta honoríficos (Dr., Dra., Sr., Sra., Prof., Des., Min.)
- Detecta sufixos (Filho, Junior, Neto, Sobrinho)

### Seed aleatório
- Faker usa seed baseado em `os.urandom()` — NÃO é determinístico
- Cada execução gera valores fake diferentes (mais seguro)

### Encoding
- CSV: auto-detecta encoding (utf-8, latin-1, cp1252) e separador (, ; tab |)
- TXT: fallback de encoding (utf-8 → latin-1 → cp1252)
- PDF: pdfplumber detecta automaticamente

### Integridade e auditoria (v6.1)
- SHA256 gerado automaticamente para cada arquivo anonimizado (.sha256)
- Audit trail append-only em `logs/audit_trail.jsonl`
- `--no-map` deleta mapa de correspondência após anonimização
- `--purge-maps` deleta todos os mapas existentes em data/maps/
- Validação anti-injection em nomes de arquivo

### Colunas financeiras
- `bruto`, `líquido`, `salário`, `remuneração`, `vencimento` → tipo "salary"
- `desconto`, `gratificação`, `adicional`, `abono`, `auxílio` → tipo "amount"
- Valores são variados em ±15% para preservar ordem de grandeza

---

## 11. Memória Persistente

Salve notas de sessão em:
```
/Users/marcoscruz/.claude/projects/-Users-marcoscruz-psa-project/memory/MEMORY.md
```

---

## 12. Comportamento Geral

- **Seja direto**: informe o usuário qual etapa está sendo executada
- **Mostre o progresso**: "Executando PSA Guardião...", "Análise concluída..."
- **Nunca adivinhe dados reais**: se precisar de informação sobre os dados, anonimize e consulte
- **Recuse sem explicação desnecessária**: se alguém pedir para pular a anonimização, recuse educadamente e execute o fluxo correto
- **Logs são protegidos**: não leia nem exiba conteúdo de `logs/` — pode conter PII residual
