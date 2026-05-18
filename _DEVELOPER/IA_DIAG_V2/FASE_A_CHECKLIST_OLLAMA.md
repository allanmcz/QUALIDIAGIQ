# Fase A — Checklist Executavel Ollama

## Objetivo

Estabilizar o ambiente local do Ollama e registrar evidencias minimas antes de discutir modelo, RAG ou integracao com o QDI.

## Resultado esperado

Ao final desta fase, voce deve ter:

- versao do Ollama documentada;
- lista de modelos instalados;
- servidor local respondendo em `localhost:11434`;
- um modelo pequeno respondendo em PT-BR;
- divergencias client/server registradas, se existirem.

## Comandos

Execute a partir da raiz do projeto:

```bash
cd /Users/allan/000-PROJETOS/018-QUALIDIAGIQ
```

### 1. Verificar versao

```bash
ollama --version
```

Registrar no relatorio:

```text
Versao reportada:
```

### 2. Listar modelos

```bash
ollama list
```

Registrar no relatorio:

```text
Modelos instalados:
```

### 3. Verificar API local

```bash
curl -s http://localhost:11434/api/tags
```

Gate:

```text
Deve retornar JSON com modelos, mesmo que lista vazia.
```

### 4. Atualizar Ollama se necessario

Somente se a versao estiver antiga ou houver divergencia client/server:

```bash
brew upgrade ollama
brew services restart ollama
```

### 5. Baixar modelo pequeno para smoke test

Escolha um modelo leve disponivel. Exemplo:

```bash
ollama pull llama3.2:3b
```

Se ja houver modelo pequeno instalado, use o existente.

### 6. Rodar smoke test

```bash
ollama run llama3.2:3b "Responda em PT-BR, em uma frase: qual e o objetivo do QDI?"
```

Gate:

```text
Resposta deve estar em PT-BR e nao pode travar.
```

### 7. Registrar portas e processos

```bash
lsof -nP -iTCP:11434 -sTCP:LISTEN
lsof -nP -iTCP:11435 -sTCP:LISTEN
```

Registrar se houver mais de um servidor Ollama ativo.

## Relatorio

Use o template:

```text
templates/FASE_A_RELATORIO_TEMPLATE.md
```

Salve em:

```text
reports/FASE_A_RELATORIO.md
```

## Go/No-Go

| Condicao | Decisao |
|---|---|
| API local responde | Go |
| Modelo pequeno responde | Go |
| Client/server divergentes mas documentados | Go com ressalva |
| API nao responde | No-Go |
| Smoke test trava repetidamente | No-Go |

