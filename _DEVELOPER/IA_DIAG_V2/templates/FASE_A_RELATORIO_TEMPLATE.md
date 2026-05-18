# FASE_A_RELATORIO — Estabilizacao Ollama

> **Data:**  
> **Executor:**  
> **Status:** Go / Go com ressalva / No-Go

## 1. Versao

Comando:

```bash
ollama --version
```

Resultado:

```text

```

## 2. Modelos instalados

Comando:

```bash
ollama list
```

Resultado:

```text

```

## 3. API local

Comando:

```bash
curl -s http://localhost:11434/api/tags
```

Resultado:

```text

```

## 4. Smoke test

Modelo usado:

```text

```

Pergunta:

```text
Responda em PT-BR, em uma frase: qual e o objetivo do QDI?
```

Resposta:

```text

```

## 5. Portas e processos

Comandos:

```bash
lsof -nP -iTCP:11434 -sTCP:LISTEN
lsof -nP -iTCP:11435 -sTCP:LISTEN
```

Resultado:

```text

```

## 6. Problemas encontrados

- 

## 7. Decisao

| Criterio | Resultado |
|---|---|
| API respondeu |  |
| Modelo respondeu |  |
| Sem servidor duplicado critico |  |
| Sem travamento recorrente |  |

Decisao final:

```text

```

