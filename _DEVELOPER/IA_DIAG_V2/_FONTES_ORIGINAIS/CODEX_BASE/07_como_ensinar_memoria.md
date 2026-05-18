# 07 - Como Ensinar a Memoria e o Contexto

## Resposta direta

Ensinar a memoria significa registrar conhecimento em um lugar certo, com formato claro, e testar se o modelo passa a usar aquilo nas respostas. No QDI, voce ensina em duas camadas: `Modelfile` para regras permanentes e `.ollama/context/*.md` para contexto vivo do projeto.

## Mapa de decisao

| O que voce quer ensinar | Onde registrar | Precisa recriar modelo? |
|---|---|---|
| Persona, idioma, postura fixa | `.ollama/Modelfile` ou `.ollama/Modelfile.qwen` | Sim |
| Stack obrigatoria | `.ollama/Modelfile` e `.ollama/context/coding_rules.md` | Sim se mudar o Modelfile |
| Decisao tecnica do projeto | `.ollama/context/qdi_context.md` | Nao |
| Regra de arquitetura | `.ollama/context/architecture.md` | Nao |
| Padrao de codigo | `.ollama/context/coding_rules.md` | Nao |
| Regra temporaria de sprint | Criar arquivo em `.ollama/context/sprint_current.md` | Nao, se o script passar a ler |
| Documento grande | Futuro RAG local | Nao, reindexar |

## Metodo em 5 passos

### 1. Escreva a decisao em linguagem objetiva

Ruim:

```text
Talvez usar algo de Winthor depois.
```

Bom:

```text
O primeiro conector ERP do QDI sera Winthor. O dominio nao deve depender de tabelas Winthor; a infrastructure traduz dados Winthor para o modelo canonico do QDI.
```

### 2. Coloque no arquivo correto

Exemplo: decisao sobre Winthor em `.ollama/context/qdi_context.md`.

```md
## Decisao - ERP Inicial

O primeiro ERP integrado ao QDI sera Winthor.
O dominio deve usar modelo canonico.
Tabelas e detalhes do Winthor ficam isolados em infrastructure.
```

### 3. Teste com pergunta objetiva

```bash
.ollama/scripts/ask_qdi.sh "Como devo desenhar o conector Winthor no QDI?"
```

### 4. Verifique se a resposta obedeceu

Resposta esperada deve mencionar:

- Winthor como primeiro ERP.
- Modelo canonico no dominio.
- Traducao em infrastructure.
- Domain sem dependencia de tabela do ERP.

### 5. Refine a memoria se a resposta falhar

Se a resposta vier generica, torne a memoria mais explicita.

Antes:

```text
Conector Winthor sera importante.
```

Depois:

```text
Conectores ERP devem ficar em src/infrastructure/adapters/erp. Eles implementam portas definidas em domain/application e convertem dados externos para value objects canonicos.
```

## Como ensinar uma decisao permanente

Edite:

```text
.ollama/Modelfile
```

Depois recrie:

```bash
ollama create qdi-assistant -f .ollama/Modelfile
```

Ou usando a variante de codigo:

```bash
ollama create qdi-assistant -f .ollama/Modelfile.qwen
```

## Como ensinar uma decisao viva

Edite um dos arquivos:

```text
.ollama/context/qdi_context.md
.ollama/context/architecture.md
.ollama/context/coding_rules.md
```

Depois teste diretamente:

```bash
.ollama/scripts/ask_qdi.sh "Explique a decisao que acabei de registrar"
```

## Como saber se a memoria ficou boa

Uma memoria boa e:

- Especifica.
- Curta.
- Acionavel.
- Sem contradicao com arquivos anteriores.
- Escrita como regra, nao como pensamento solto.
- Testavel por uma pergunta direta.

## Analogia Oracle

Pense assim:

- `Modelfile`: parametros de instancia.
- `.ollama/context/*.md`: tabelas de configuracao.
- `ask_qdi.sh`: procedure que monta a consulta.
- RAG: indice para buscar linhas relevantes em massa documental grande.

Se a tabela de configuracao estiver ambigua, a procedure retorna comportamento inconsistente.
