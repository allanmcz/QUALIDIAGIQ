# 01 - Conceitos Fundamentais

## Memoria fixa

Memoria fixa e aquilo que fica gravado no `SYSTEM` do `Modelfile`.

Ela serve para regras que quase nunca mudam:

- Responder em PT-BR.
- Atuar como mentor, arquiteto, pair programmer e instrutor.
- Usar Clean Architecture.
- Preferir Python 3.12, FastAPI, Pydantic v2 e Supabase.
- Nao tratar Allan como iniciante.
- Perguntar quando houver ambiguidade.

Limite: se a memoria fixa ficar grande demais, o modelo pode ficar lento e menos preciso.

## Contexto injetado

Contexto injetado e o conteudo que enviamos junto com cada pergunta.

No QDI, esta camada fica em:

```text
.ollama/context/
├── qdi_context.md
├── architecture.md
└── coding_rules.md
```

Uso tipico:

```bash
.ollama/scripts/ask_qdi.sh "Onde devo criar um novo value object?"
```

## RAG

RAG significa Retrieval-Augmented Generation, ou geracao aumentada por recuperacao.

Em vez de enviar todos os documentos para o modelo, o sistema:

1. Quebra documentos em pequenos trechos.
2. Gera embeddings desses trechos.
3. Salva os vetores em um indice.
4. Ao receber uma pergunta, busca os trechos mais relacionados.
5. Envia apenas esses trechos ao modelo.

Para o QDI, o RAG local devera indexar:

- `AGENTS.md`
- `docs/refs/*.md`
- ADRs
- decisoes tecnicas
- modelagem de dominio
- documentos normativos permitidos

## Diferenca entre memoria e RAG

| Item | Memoria fixa | Contexto injetado | RAG |
|---|---|---|---|
| Onde fica | `Modelfile` | Arquivos `.md` | Indice vetorial |
| Atualizacao | Manual | Manual | Automatizavel |
| Melhor para | Regras permanentes | Resumo do projeto | Documentos grandes |
| Risco | Ficar rigida | Prompt grande | Recuperar trecho ruim |

## Regra pratica

- Use `Modelfile` para identidade.
- Use `.ollama/context` para resumo vivo do projeto.
- Use RAG para documentos extensos.
