# 03 - Comandos Ollama

## Verificar instalacao

```bash
ollama --version
ollama list
```

## Criar o modelo do QDI

Modelo com `llama3:latest`:

```bash
ollama create qdi-assistant -f .ollama/Modelfile
```

Modelo alternativo para codigo, se `qwen2.5-coder:7b` estiver disponivel:

```bash
ollama create qdi-assistant -f .ollama/Modelfile.qwen
```

## Executar conversa direta

```bash
ollama run qdi-assistant
```

## Executar com memoria do projeto

```bash
.ollama/scripts/ask_qdi.sh "Onde devo colocar a entidade DiagnosticoTributario?"
```

## Executar com contexto completo

```bash
.ollama/scripts/ask_qdi.sh --full "Quais features MUST do QDI impactam o dominio?"
```

## Teste via API HTTP

```bash
curl -s http://localhost:11434/api/generate \
  -d '{
    "model": "qdi-assistant",
    "prompt": "Responda em PT-BR: onde fica uma entidade de dominio no QDI?",
    "stream": false,
    "options": {
      "num_predict": 80,
      "temperature": 0.2
    }
  }'
```

## Testar servidor Ollama

```bash
curl -s http://localhost:11434/api/tags
```

## Subir servidor em porta alternativa

Use apenas para diagnostico:

```bash
OLLAMA_HOST=127.0.0.1:11435 ollama serve
```

Depois teste:

```bash
curl -s http://127.0.0.1:11435/api/tags
```

## Encerrar processos de teste

```bash
pkill -f "ollama run qdi-assistant"
pkill -f "ask_qdi.sh"
```

Nao use `pkill` em ambiente compartilhado sem conferir processos antes:

```bash
ps -axo pid,ppid,etime,command | rg "ollama|qdi-assistant|ask_qdi"
```
