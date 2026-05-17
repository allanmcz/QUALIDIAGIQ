# 10 - Checklist de Qualidade da Memoria

Use este checklist antes de considerar que uma memoria foi bem ensinada.

## Clareza

- [ ] A regra esta escrita em frases diretas.
- [ ] O texto evita "talvez", "pode ser", "ver depois" quando for decisao aceita.
- [ ] A memoria diz onde aplicar.
- [ ] A memoria diz o que evitar.

## Local correto

- [ ] Regras permanentes estao no `Modelfile`.
- [ ] Decisoes vivas estao em `.ollama/context`.
- [ ] Documentos grandes nao foram copiados inteiros para memoria fixa.
- [ ] Conteudo temporario de sprint nao foi misturado com regra permanente.

## Consistencia

- [ ] Nao contradiz `AGENTS.md`.
- [ ] Nao contradiz PRD, MoSCoW ou ADRs.
- [ ] Nao viola Clean Architecture.
- [ ] Nao cria dependencia externa no domain.
- [ ] Nao coloca regra tributaria sem fonte ou vigencia.

## Testabilidade

- [ ] Existe uma pergunta de teste.
- [ ] Existe uma resposta esperada.
- [ ] Existe uma lista do que a resposta nao pode conter.
- [ ] O teste foi executado depois da mudanca.

## Tamanho

- [ ] A memoria e curta o suficiente para ser lida com rapidez.
- [ ] O texto nao repete o mesmo conceito em tres lugares.
- [ ] O `Modelfile` contem apenas regras duradouras.
- [ ] O restante foi para contexto ou futuro RAG.

## Sinais de memoria ruim

Se o modelo responder de forma inconsistente, procure:

- Regra duplicada com nomes diferentes.
- Regra antiga nao marcada como substituida.
- Decisao temporaria registrada como permanente.
- Texto longo demais e pouco acionavel.
- Falta de exemplo correto/incorreto.

## Perguntas de auditoria

Rode periodicamente:

```bash
.ollama/scripts/ask_qdi.sh "Quais sao as regras arquiteturais mais importantes do QDI?"
.ollama/scripts/ask_qdi.sh "O que esta fora do MVP do QDI?"
.ollama/scripts/ask_qdi.sh "Onde devo colocar um schema Pydantic de request HTTP?"
.ollama/scripts/ask_qdi.sh "Como evitar dependencia do Winthor no dominio?"
```

Uma memoria saudavel deve responder alinhada ao AGENTS.md.
