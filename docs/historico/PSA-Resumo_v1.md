# PSA — Resumo Executivo

> **Versao:** v1
> **Data:** 2026-03-11
> **Mudancas:** Documento inicial — estado do projeto em marco/2026.

---

## O que e o PSA

**PSA — Privacy Shield Agent for AI** e uma camada de seguranca local que intercepta, anonimiza e protege dados sensiveis **antes** de envia-los a qualquer IA (Claude, ChatGPT, Gemini ou qualquer LLM via API).

Nenhum dado real jamais sai do computador do usuario. A IA trabalha exclusivamente com dados ficticios.

## Frase principal

> PSA nao e uma ferramenta de produtividade. E uma camada de seguranca que, como consequencia, tambem economiza 99% dos tokens e torna qualquer analise 30x mais rapida.

## Os 4 medos que o PSA resolve

| Medo | Risco | Solucao PSA |
|---|---|---|
| Vazamento de dados | CPF, salario, endereco vao para servidores externos | Dados reais nunca saem do computador |
| Multa LGPD/GDPR | ANPD pode multar ate 2% do faturamento | Compliance automatico + log auditavel |
| Segredo industrial | Precos, margens, clientes VIP vao a nuvem | So ficticios chegam a nuvem |
| Dados treinando concorrentes | Termos de uso podem usar dados para treinar modelos | Nenhum dado real alimenta nenhum modelo |

## Conformidade

LGPD, GDPR, HIPAA, Sigilo profissional, Segredo industrial.

## Caso real

Testado com 256.013 servidores do GDF — zero vazamentos — auditoria 100/100.

## Metricas atuais

| Metrica | Valor |
|---|---|
| Score de auditoria | 100/100 |
| Padroes PII detectados | 70+ |
| Formatos suportados | 11 (.csv, .xlsx, .xls, .docx, .txt, .pdf, .pptx, .eml, .msg, .png, .jpg) |
| Vazamentos em producao | Zero |
| Idiomas do site | 7 (PT, EN, ES, ZH, HI, FR, HE) |

## Amostragem Inteligente v5.1

| Tamanho (N linhas) | Amostra | Regra |
|---|---|---|
| N <= 30 | 100% | Arquivo pequeno — manda tudo com aviso |
| 31 a 100 | 50% (min 30) | Representatividade estatistica |
| 101 a 10.000 | 100 | Padrao |
| 10.001 a 100.000 | 150 | Arquivo grande |
| 100.001+ | 200 | Maximo recomendado |

Base estatistica: Teorema Central do Limite (n >= 30).

## Agentes

| Agente | Papel |
|---|---|
| Comandante (CEO) | Orquestra o fluxo, nunca envia dados sem PSA |
| PSA Guardiao | Anonimiza, valida, bloqueia vazamentos |
| CFO | Analise financeira com dados anonimizados |

## Publico-alvo

Advocacia, Saude, Contabilidade/RH, Governo, PMEs.

## Autor

Marcos Cruz — Brasilia/DF — Marco 2026.
