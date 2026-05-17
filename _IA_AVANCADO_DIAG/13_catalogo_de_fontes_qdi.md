# 13 - Catalogo de Fontes do QDI

Este documento define como catalogar fontes para memoria e RAG.

## Por que catalogar

Sem catalogo, o agente pode tratar uma anotacao pessoal como se fosse lei. Para diagnostico tributario, isso e perigoso.

O catalogo deve responder:

- De onde veio?
- Quando foi acessado?
- Esta vigente?
- Qual a confiabilidade?
- Pode ser usado em resposta final?
- Exige verificacao?

## Modelo de catalogo em Markdown

```md
## Fonte 001 - <titulo>

ID: FONTE-001
Tipo: legislacao | norma | aula | artigo | jurisprudencia | interno | anotacao
Confiabilidade: A | B | C | D
Status: ativa | substituir | obsoleta | verificar
Origem:
URL:
Arquivo local:
Autor/Orgao:
Data de publicacao:
Data de acesso:
Vigencia:

Resumo:
<resumo em 3 a 8 linhas>

Aplicacao no QDI:
- <uso 1>
- <uso 2>

Restricoes:
- <restricao 1>

Perguntas que esta fonte ajuda a responder:
- <pergunta 1>
- <pergunta 2>
```

## Modelo de catalogo em YAML

Arquivo sugerido no futuro:

```text
fontes/catalogo_fontes.yml
```

Exemplo:

```yaml
fontes:
  - id: FONTE-001
    titulo: "Emenda Constitucional 132/2023"
    tipo: "legislacao"
    confiabilidade: "A"
    status: "ativa"
    origem: "Planalto"
    url: "<URL oficial>"
    arquivo_local: "fontes/extraido/FONTE-001_ec_132_2023.md"
    data_publicacao: "2023-12-20"
    data_acesso: "2026-05-17"
    vigencia: "verificar por dispositivo"
    resumo: "Base constitucional da Reforma Tributaria do Consumo."
    aplicacao_qdi:
      - "Contextualizar diagnostico"
      - "Fundamentar eixos de impacto"
    restricoes:
      - "Nao usar sem verificar regulamentacao infraconstitucional aplicavel"

  - id: FONTE-002
    titulo: "Aula sobre IBS e CBS"
    tipo: "aula"
    confiabilidade: "C"
    status: "verificar"
    origem: "Curso"
    url: "<URL da aula>"
    arquivo_local: "fontes/extraido/FONTE-002_aula_ibs_cbs.md"
    data_publicacao: "2026-05-10"
    data_acesso: "2026-05-17"
    vigencia: "nao aplicavel"
    resumo: "Aula interpretativa sobre impactos de IBS/CBS."
    aplicacao_qdi:
      - "Gerar hipoteses de perguntas"
      - "Apoiar explicacoes didaticas"
    restricoes:
      - "Nao usar como fonte primaria"
      - "Validar contra legislacao oficial"
```

## Classificacao de confiabilidade

| Nivel | Descricao | Exemplo |
|---|---|---|
| A | Fonte primaria oficial | lei, EC, LC, DOU, Receita Federal |
| B | Norma ou instituicao reconhecida | ABNT, ISO, manuais oficiais |
| C | Interpretacao qualificada | aula, livro, consultoria, artigo |
| D | Anotacao ou hipotese | anotacoes pessoais, rascunhos |

## Regra de precedencia

1. Fonte A prevalece sobre todas.
2. Fonte B orienta metodologia quando aplicavel.
3. Fonte C apoia interpretacao, mas nao substitui fonte A.
4. Fonte D gera hipoteses e perguntas, nao conclusoes.

## Campos minimos obrigatorios

Para qualquer fonte:

- ID
- titulo
- tipo
- confiabilidade
- status
- origem
- data de acesso
- resumo
- restricoes

Para fonte legal:

- orgao
- URL oficial
- vigencia
- status normativo

## Como nomear arquivos

Padrao:

```text
FONTE-<numero>_<tipo>_<slug>.<extensao>
```

Exemplos:

```text
FONTE-001_legislacao_ec_132_2023.md
FONTE-002_legislacao_lc_214_2025.md
FONTE-003_aula_ibs_cbs_transicao.md
FONTE-004_artigo_benchmark_reforma.md
```

## Como usar no RAG

Cada chunk deve carregar metadados:

```yaml
source_id: FONTE-001
source_type: legislacao
reliability: A
title: Emenda Constitucional 132/2023
section: Artigo X
accessed_at: 2026-05-17
validity: verificar por dispositivo
```

## Frase padrao para respostas com fonte fraca

```text
Com base apenas nas fontes locais disponiveis, isso aparece como interpretacao de aula, nao como conclusao normativa. Para aplicar no QDI, e necessario validar contra fonte primaria oficial e vigencia do dispositivo.
```
