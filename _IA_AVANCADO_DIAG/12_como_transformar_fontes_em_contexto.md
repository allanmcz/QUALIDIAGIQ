# 12 - Como Transformar Aulas, Legislacao e Outros Conteudos em Fonte

## Resposta direta

Para usar aulas, legislacao, PDFs, artigos e anotacoes como fonte, voce precisa transformar cada material em uma fonte controlada: com origem, data, confiabilidade, resumo, trechos citaveis e regra de uso. No QDI, isso e essencial porque conhecimento tributario sem fonte e vigencia pode induzir erro.

## Tipos de fonte

| Tipo | Exemplo | Pode virar memoria? | Pode virar RAG? | Cuidado principal |
|---|---|---:|---:|---|
| Legislacao | EC, LC, lei, decreto, IN, NT | Sim, em resumo | Sim | Vigencia e versao |
| Norma tecnica | ABNT, ISO | Sim, em resumo | Sim, se uso permitido | Direitos autorais e citacao limitada |
| Aula | Curso, mentoria, live | Sim, como aprendizado | Sim, se transcrita | Distinguir opiniao de regra |
| Artigo tecnico | Blog, whitepaper, consultoria | Sim, com baixa autoridade | Sim | Verificar fonte primaria |
| Jurisprudencia | Solucao de consulta, decisao | Sim, com cautela | Sim | Escopo e aplicabilidade |
| Documentacao interna | ADR, PRD, runbook | Sim | Sim | Status atualizado |
| Anotacao pessoal | Insights de estudo | Sim | Sim | Marcar como interpretacao |

## Regra de ouro

Nunca misture no mesmo nivel:

- texto legal oficial;
- interpretacao de aula;
- opiniao de consultoria;
- anotacao pessoal.

Cada fonte deve carregar seu tipo e nivel de confiabilidade.

## Camadas de confiabilidade

| Nivel | Tipo | Como usar |
|---|---|---|
| A | Fonte primaria oficial | Pode fundamentar regra, citando origem |
| B | Norma tecnica ou orgao reconhecido | Pode orientar metodologia, respeitando licenca |
| C | Doutrina, curso, aula, consultoria | Pode apoiar interpretacao |
| D | Anotacao pessoal | Pode gerar hipotese, nunca regra final sozinha |

## Como transformar uma aula em fonte

### 1. Capturar

Opcoes:

- baixar material PDF da aula;
- salvar slides;
- transcrever audio/video;
- registrar anotacoes estruturadas.

### 2. Separar fato, interpretacao e acao

Use este formato:

```md
# Aula - <titulo>

Fonte:
- Professor:
- Curso:
- Data:
- Link:
- Tipo: aula
- Confiabilidade: C

## Fatos apresentados

- <ponto objetivo>

## Interpretacoes do professor

- <opiniao ou leitura juridica>

## Aplicacao possivel no QDI

- <como isso pode virar pergunta, score, regra ou explicacao>

## Pendencias de verificacao

- <qual lei, artigo ou fonte primaria precisa conferir>
```

### 3. Converter em contexto ou RAG

Se for uma decisao curta:

```text
.ollama/context/qdi_context.md
```

Se for material grande:

```text
futuro indice RAG
```

## Como transformar legislacao em fonte

### 1. Usar fonte primaria

Preferir:

- Portal do Planalto.
- Receita Federal.
- Senado/Camara quando aplicavel.
- Diario Oficial.
- CONFAZ quando aplicavel.
- SEFAZ estadual quando a regra for estadual.

### 2. Registrar metadados

```md
# Fonte Legal - <nome>

Tipo: legislacao
Confiabilidade: A
Orgao:
URL:
Data de acesso:
Data de publicacao:
Vigencia:
Status: vigente | revogada | alterada | verificar

## Trechos relevantes

- Art. X: <resumo proprio, sem copiar texto longo>

## Aplicacao no QDI

- <impacto em diagnostico, pergunta, score ou relatorio>

## Restricoes

- Nao aplicar fora do periodo de vigencia.
- Verificar alteracoes posteriores antes de usar em producao.
```

### 3. Evitar copiar texto legal extenso

Para estudo interno, prefira resumo com referencia ao artigo. Para resposta do agente, exigir citacao da fonte.

## Como transformar PDF em fonte

Fluxo recomendado:

1. Salvar PDF em pasta de fontes.
2. Extrair texto.
3. Conferir se a extracao nao quebrou tabelas.
4. Criar resumo estruturado.
5. Registrar metadados.
6. Indexar no RAG.

Formato sugerido:

```text
fontes/
├── bruto/
│   └── 2026-05-17_abnt_17301_anotacoes.pdf
├── extraido/
│   └── 2026-05-17_abnt_17301_anotacoes.md
└── catalogo_fontes.yml
```

## Como transformar video em fonte

Fluxo:

1. Gerar transcricao.
2. Revisar nomes de leis, artigos e siglas.
3. Separar fala literal de resumo.
4. Marcar como aula/opiniao, nao como fonte primaria.
5. Vincular com fonte legal oficial quando houver regra tributaria.

Modelo:

```md
# Transcricao - <aula>

Tipo: aula transcrita
Confiabilidade: C
Data:
Professor:
Curso:
Link:

## Resumo executivo

- <principais pontos>

## Trechos de interesse

- Tempo 00:12:30: <resumo do trecho>

## Fontes primarias citadas

- <lei, artigo, norma>

## Pendencias

- Confirmar <ponto> em fonte oficial.
```

## O que entra na memoria fixa

Pouca coisa.

Exemplos que podem entrar no `Modelfile`:

- "Respostas tributarias devem considerar vigencia."
- "Se nao houver fonte, declarar insuficiencia."
- "Diferenciar lei, interpretacao e anotacao pessoal."

## O que entra no contexto

Resumos curtos e decisoes.

Exemplo:

```md
## Regra de Uso de Fontes

No QDI, fonte primaria oficial prevalece sobre aula, artigo ou anotacao.
Conteudo de aula deve ser tratado como interpretacao ate ser validado contra legislacao vigente.
```

## O que entra no RAG

Conteudos maiores:

- PDFs de aula.
- Transcricoes.
- PRDs.
- Leis.
- Normas.
- Solucoes de consulta.
- Artigos tecnicos.

## Exemplo pratico

Pergunta:

```text
Como usar uma aula sobre CBS/IBS no QDI?
```

Resposta operacional:

1. Transcreva a aula.
2. Marque como fonte tipo `aula`, confiabilidade `C`.
3. Extraia pontos objetivos.
4. Liste leis/artigos citados.
5. Verifique leis em fonte primaria.
6. Registre apenas a conclusao validada no contexto.
7. Indexe a transcricao no RAG com metadados.

## Regra para o agente

Quando responder sobre materia tributaria:

- Se houver fonte primaria recuperada, cite.
- Se houver apenas aula, diga que e interpretacao de aula.
- Se houver divergencia entre aula e legislacao, prevalece legislacao.
- Se nao houver fonte suficiente, responder que a base local nao sustenta conclusao.
