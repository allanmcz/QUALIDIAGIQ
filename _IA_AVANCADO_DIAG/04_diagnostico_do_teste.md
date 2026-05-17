# 04 - Diagnostico do Teste Real

## Data

2026-05-17

## O que funcionou

O Ollama esta instalado:

```text
ollama version is 0.24.0
Warning: client version is 0.20.4
```

Modelos vistos inicialmente:

```text
mxbai-embed-large:latest
llama3:latest
```

O modelo do QDI foi criado com sucesso:

```bash
ollama create qdi-assistant -f .ollama/Modelfile
```

Resultado:

```text
success
```

O endpoint `/api/tags` mostrou o modelo criado:

```text
qdi-assistant:latest
llama3:latest
mxbai-embed-large:latest
```

## O que apresentou problema

A geracao no servidor padrao `localhost:11434` ficou presa mesmo com prompt minimo.

Foram testados:

```bash
.ollama/scripts/ask_qdi.sh "..."
```

e:

```bash
curl -s --max-time 20 http://localhost:11434/api/generate ...
```

O endpoint de listagem respondia, mas a geracao nao retornava dentro do tempo esperado.

## Hipotese tecnica

Ha indicio de diferenca entre cliente e servidor:

```text
ollama version is 0.24.0
Warning: client version is 0.20.4
```

Isso pode causar comportamento estranho entre CLI, servidor e runtime de geracao.

Tambem foi observado que um servidor alternativo em `127.0.0.1:11435` listou outro conjunto de modelos, incluindo:

```text
qwen2.5-coder:7b
qwen2.5-coder:14b
llama3.2:latest
gemma3:12b
```

Nesse servidor alternativo, `qdi-assistant` ainda nao existia porque o modelo havia sido criado no servidor/model store visto pelo endpoint padrao.

## Acao tomada

Foi criado `.ollama/Modelfile.qwen` para permitir recriar o `qdi-assistant` usando `qwen2.5-coder:7b`, que tende a ser melhor para codigo.

Comando recomendado:

```bash
ollama create qdi-assistant -f .ollama/Modelfile.qwen
```

## Como validar depois

1. Reinicie o Ollama para alinhar cliente e servidor.
2. Rode:

```bash
ollama list
ollama create qdi-assistant -f .ollama/Modelfile.qwen
.ollama/scripts/ask_qdi.sh "Responda em ate 8 linhas: qual arquitetura devo usar no QDI?"
```

3. Se ainda travar, teste:

```bash
ollama run qwen2.5-coder:7b "Diga oi em PT-BR"
```

Se o modelo base tambem travar, o problema esta no runtime do Ollama, nao na memoria criada.
