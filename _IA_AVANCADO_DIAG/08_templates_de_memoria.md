# 08 - Templates de Memoria

Use estes modelos para registrar informacoes novas sem baguncar o contexto.

## Template - Decisao Tecnica

Arquivo recomendado:

```text
.ollama/context/qdi_context.md
```

Modelo:

```md
## Decisao - <titulo curto>

Data: AAAA-MM-DD
Status: proposta | aceita | substituida

Contexto:
<explique o problema em 2 a 5 linhas>

Decisao:
<declare a decisao de forma objetiva>

Consequencias:
- <consequencia 1>
- <consequencia 2>
- <consequencia 3>

Onde aplicar:
- <paths, camadas ou modulos>

Como testar:
- <pergunta que deve validar se o modelo aprendeu>
```

Exemplo:

```md
## Decisao - Winthor como primeiro ERP

Data: 2026-05-17
Status: aceita

Contexto:
O QDI precisa iniciar integracao ERP por uma base conhecida por Allan.
Winthor e o ERP com maior dominio tecnico e tributario no projeto.

Decisao:
O primeiro conector ERP do QDI sera Winthor.
O dominio deve trabalhar com modelo canonico e nao deve depender de tabelas Winthor.

Consequencias:
- Tabelas Winthor ficam isoladas em infrastructure.
- Portas de leitura fiscal devem ser definidas sem SQL especifico de ERP.
- Testes de dominio usam dados canonicos.

Onde aplicar:
- src/domain
- src/application
- src/infrastructure/adapters/erp/winthor

Como testar:
- Perguntar: "Como devo modelar o conector Winthor sem contaminar o domain?"
```

## Template - Regra Arquitetural

Arquivo recomendado:

```text
.ollama/context/architecture.md
```

Modelo:

```md
## Regra Arquitetural - <titulo>

Regra:
<declare a regra>

Motivo:
<explique o porquê>

Permitido:
- <item permitido>

Proibido:
- <item proibido>

Exemplo correto:
<exemplo curto>

Exemplo incorreto:
<exemplo curto>
```

## Template - Regra de Codigo

Arquivo recomendado:

```text
.ollama/context/coding_rules.md
```

Modelo:

```md
## Regra de Codigo - <titulo>

Quando aplicar:
<contexto>

Regra:
<regra objetiva>

Exemplo:
```python
# codigo exemplo
```

Teste esperado:
<como verificar>
```

## Template - Fora de Escopo

Arquivo recomendado:

```text
.ollama/context/qdi_context.md
```

Modelo:

```md
## Fora de Escopo - <tema>

O que esta fora:
- <item>

Produto correto:
- <QAI, QFC, QMI ou outro>

Como responder:
Quando Allan pedir <tema>, lembrar que esta fora do MVP do QDI e propor redirecionamento.
```

## Template - Fonte Normativa

Arquivo recomendado agora:

```text
.ollama/context/qdi_context.md
```

Arquivo recomendado no futuro:

```text
indice RAG local
```

Modelo:

```md
## Fonte Normativa - <nome>

Fonte:
<lei, norma, documento>

Vigencia:
<periodo ou data>

Aplicacao no QDI:
<como afeta diagnostico, score, pergunta ou relatorio>

Restricao:
Nao responder como regra definitiva sem citacao desta fonte ou de documento validado.
```

## Template - Prompt de Teste

Use apos qualquer mudanca de memoria.

```md
## Teste de Memoria - <tema>

Pergunta:
<pergunta para o modelo>

Resposta esperada deve conter:
- <criterio 1>
- <criterio 2>
- <criterio 3>

Resposta nao pode conter:
- <erro 1>
- <erro 2>
```
