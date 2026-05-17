# 16 - Caderno de Treino Supervisionado

Use este arquivo para registrar perguntas, respostas esperadas, avaliacao e correcao. Ele funciona como uma suite manual de testes da memoria.

## Como usar

1. Copie o template de caso.
2. Preencha pergunta e resposta esperada.
3. Rode o agente.
4. Cole ou resuma a resposta obtida.
5. Atribua notas.
6. Registre correcao.
7. Se a correcao for duradoura, promova para `.ollama/context`.

## Template de caso supervisionado

```md
## Caso SUP-XXX - <titulo>

Tema:

Objetivo de ensino:

Pergunta:

Resposta esperada:

Fontes esperadas:

Criterios obrigatorios:
- 

Erros proibidos:
- 

Resposta obtida:

Avaliacao:
| Criterio | Nota 0-3 | Observacao |
|---|---:|---|
| Arquitetura | | |
| Stack | | |
| Fonte | | |
| Escopo | | |
| Acionabilidade | | |
| Tom | | |

Nota media:

Correcao de Allan:

Promover para memoria?
- [ ] Nao
- [ ] Sim, em `.ollama/context/qdi_context.md`
- [ ] Sim, em `.ollama/context/architecture.md`
- [ ] Sim, em `.ollama/context/coding_rules.md`
- [ ] Sim, em outro arquivo:

Status:
- [ ] Aberto
- [ ] Corrigido
- [ ] Aprovado
- [ ] Substituido
```

---

## Caso SUP-001 - Entidade de dominio

Tema:
Clean Architecture

Objetivo de ensino:
Ensinar que entidade de dominio fica no domain e nao depende de framework, banco ou schema HTTP.

Pergunta:
Onde fica a entidade DiagnosticoTributario no QDI?

Resposta esperada:
A entidade `DiagnosticoTributario` deve ficar em `src/domain`, porque representa regra central do negocio. Ela nao deve depender de FastAPI, Supabase, SQLAlchemy ou Pydantic de API. Casos de uso que criam ou avaliam diagnosticos ficam em `src/application`; persistencia concreta fica em `src/infrastructure`; schemas HTTP ficam em `src/presentation`.

Fontes esperadas:
- `AGENTS.md`
- `.ollama/context/architecture.md`

Criterios obrigatorios:
- Citar `src/domain`.
- Separar as quatro camadas.
- Proibir dependencia externa na entidade.

Erros proibidos:
- Colocar entidade em `presentation`.
- Usar schema Pydantic HTTP como entidade.
- Colocar SQL dentro da entidade.

Resposta obtida:
Pendente.

Avaliacao:
| Criterio | Nota 0-3 | Observacao |
|---|---:|---|
| Arquitetura | | |
| Stack | | |
| Fonte | | |
| Escopo | | |
| Acionabilidade | | |
| Tom | | |

Nota media:
Pendente.

Correcao de Allan:
Pendente.

Promover para memoria?
- [ ] Nao
- [ ] Sim, em `.ollama/context/qdi_context.md`
- [ ] Sim, em `.ollama/context/architecture.md`
- [ ] Sim, em `.ollama/context/coding_rules.md`
- [ ] Sim, em outro arquivo:

Status:
- [x] Aberto
- [ ] Corrigido
- [ ] Aprovado
- [ ] Substituido

---

## Caso SUP-002 - Fonte tributaria insuficiente

Tema:
RAG com guardrails

Objetivo de ensino:
Ensinar que resposta tributaria sem fonte primaria deve declarar insuficiencia.

Pergunta:
Posso afirmar que determinada operacao tera aumento de carga com IBS/CBS?

Resposta esperada:
Nao de forma definitiva sem fonte e dados. O agente deve pedir base legal, periodo de vigencia, dados da operacao e fonte primaria aplicavel. Se houver apenas aula ou anotacao, deve tratar como interpretacao e declarar que a base e insuficiente para conclusao normativa.

Fontes esperadas:
- `.ollama/context/qdi_context.md`
- `.ollama/context/coding_rules.md`
- futura base RAG de legislacao

Criterios obrigatorios:
- Distinguir fonte primaria de interpretacao.
- Mencionar vigencia.
- Declarar insuficiencia quando faltar fonte.

Erros proibidos:
- Dar conclusao tributaria definitiva sem fonte.
- Usar aula como se fosse lei.
- Ignorar vigencia.

Resposta obtida:
Pendente.

Avaliacao:
| Criterio | Nota 0-3 | Observacao |
|---|---:|---|
| Arquitetura | | |
| Stack | | |
| Fonte | | |
| Escopo | | |
| Acionabilidade | | |
| Tom | | |

Nota media:
Pendente.

Correcao de Allan:
Pendente.

Promover para memoria?
- [ ] Nao
- [ ] Sim, em `.ollama/context/qdi_context.md`
- [ ] Sim, em `.ollama/context/architecture.md`
- [ ] Sim, em `.ollama/context/coding_rules.md`
- [ ] Sim, em outro arquivo:

Status:
- [x] Aberto
- [ ] Corrigido
- [ ] Aprovado
- [ ] Substituido

---

## Caso SUP-003 - Fora de escopo do QDI

Tema:
Escopo MVP

Objetivo de ensino:
Ensinar que apuracao CBS/IBS continua e split payment nao pertencem ao MVP do QDI.

Pergunta:
Vamos implementar apuracao continua de CBS/IBS e split payment no QDI?

Resposta esperada:
Nao como escopo do MVP do QDI. Apuracao CBS/IBS continua pertence ao QAI; split payment orquestrador pertence ao QFC. O QDI pode diagnosticar prontidao, riscos, gaps e recomendar proximos passos, mas nao deve virar motor de apuracao ou orquestrador financeiro no MVP.

Fontes esperadas:
- `AGENTS.md`
- `.ollama/context/qdi_context.md`

Criterios obrigatorios:
- Dizer que esta fora do MVP.
- Redirecionar para QAI e QFC.
- Propor alternativa dentro do QDI.

Erros proibidos:
- Aceitar implementar no QDI sem ressalva.
- Misturar diagnostico com motor fiscal.

Resposta obtida:
Pendente.

Avaliacao:
| Criterio | Nota 0-3 | Observacao |
|---|---:|---|
| Arquitetura | | |
| Stack | | |
| Fonte | | |
| Escopo | | |
| Acionabilidade | | |
| Tom | | |

Nota media:
Pendente.

Correcao de Allan:
Pendente.

Promover para memoria?
- [ ] Nao
- [ ] Sim, em `.ollama/context/qdi_context.md`
- [ ] Sim, em `.ollama/context/architecture.md`
- [ ] Sim, em `.ollama/context/coding_rules.md`
- [ ] Sim, em outro arquivo:

Status:
- [x] Aberto
- [ ] Corrigido
- [ ] Aprovado
- [ ] Substituido
