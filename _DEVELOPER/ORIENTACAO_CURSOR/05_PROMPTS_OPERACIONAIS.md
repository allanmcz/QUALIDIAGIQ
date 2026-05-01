# Biblioteca de Prompts Operacionais — Cursor QDI

| Campo | Valor |
|---|---|
| **Documento** | Biblioteca de prompts prontos para colar no Cursor (Cmd+L) |
| **Audiência** | Allan Marcio durante S0.5 → S4 |
| **Como usar** | Copiar prompt, colar no Cursor (chat), preencher `[bracket]`, executar |

---

## Índice

1. [Diagnóstico inicial S0.5](#1-diagnóstico-inicial-s05)
2. [Criar nova entidade Domain](#2-criar-nova-entidade-domain)
3. [Criar Value Object](#3-criar-value-object)
4. [Criar Port + Adapter](#4-criar-port--adapter)
5. [Criar Use Case](#5-criar-use-case)
6. [Criar Router FastAPI](#6-criar-router-fastapi)
7. [Criar Migration SQL com RLS](#7-criar-migration-sql-com-rls)
8. [Criar testes unitários](#8-criar-testes-unitários)
9. [Criar testes de integração](#9-criar-testes-de-integração)
10. [Refatoração Clean Arch](#10-refatoração-clean-arch)
11. [Criar ADR](#11-criar-adr)
12. [Code review automatizado](#12-code-review-automatizado)
13. [Debug de bug runtime](#13-debug-de-bug-runtime)
14. [Atualizar documentação](#14-atualizar-documentação)
15. [Pesquisa de norma legal](#15-pesquisa-de-norma-legal)

---

## 1. Diagnóstico inicial S0.5

> **Quando usar:** primeiro prompt no Cursor após substituir `.cursorrules` (sábado 02/05 manhã).

```
Olá. Vou iniciar a Sprint S0.5 de Hardening do QDI.

Confirme:
1. Você é o agente QDI v2.0 (pós-auditoria 30/04/2026)?
2. Cite os 12 princípios não-negociáveis em ordem
3. Cite os 6 anti-padrões de SEGURANÇA da seção 5 do .cursorrules
4. Confirme o bug runtime descoberto em consultoria_service.py linha 44

Em seguida, leia:
- `/Users/allan/000-PROJETOS/018-QUALIDIAGIQ/_DEVELOPER/ORIENTACAO_CURSOR/04_PLANO_EXECUCAO.md` *(ou na raiz do repo: `_DEVELOPER/ORIENTACAO_CURSOR/04_PLANO_EXECUCAO.md`)*
- `_DEVELOPER/ANALISE_30042026/02_REGISTRO_ISSUES.md` (foco P0)

E me apresente um plano de execução para os próximos 5h (Bloco 1 + Bloco 2 + Bloco 3) seguindo
04_PLANO_EXECUCAO.md §2.2 (Sábado 02/05 manhã).

Termine perguntando se posso iniciar o Bloco 1.
```

---

## 2. Criar nova entidade Domain

```
Tarefa: criar entidade [NomeDaEntidade] no domain layer

Camada Clean Arch: src/domain/entities/
Princípios NN aplicáveis: §10.[X], §10.[Y]
Base normativa: [LC 214 art. X / EC 132 art. Y / ABNT 17301 cap Z]

Especificação:
- Atributos:
  - [campo1: tipo] — [descrição PT-BR]
  - [campo2: tipo | None] — [descrição PT-BR]
- Invariantes:
  - [regra 1]
  - [regra 2]
- Métodos de domínio:
  - [verbo](self, [params]) — [efeito]

Restrições:
- @dataclass(frozen=[True/False], slots=True)
- from __future__ import annotations
- Type hints estritos
- Docstring PT-BR completa com Base normativa + Analogia Allan
- Exceções de domínio dedicadas (não usar Exception genérico)
- Sem imports de pydantic, fastapi, supabase, anthropic, sqlalchemy

Entregáveis:
- src/domain/entities/[arquivo].py
- tests/unit/domain/test_[arquivo].py com 5+ casos felizes e 3+ erros (parametrize)

Validação:
- make test passa
- make lint zero warnings
- Cobertura ≥ 90% para essa entidade

Commit: feat(qdi-domain): adicionar entidade [NomeDaEntidade]
```

---

## 3. Criar Value Object

```
Tarefa: criar Value Object [NomeVO] no domain layer

Camada Clean Arch: src/domain/value_objects/
Princípios NN aplicáveis: imutabilidade, auditabilidade

Especificação:
- Atributos imutáveis:
  - [campo1: tipo]
  - [campo2: tipo]
- Invariantes em __post_init__:
  - [regra de validação 1]
  - [regra de validação 2]
- Properties úteis:
  - @property def [nome](self) -> [tipo]: ...

Restrições:
- @dataclass(frozen=True, slots=True)  ← OBRIGATÓRIO
- Sem métodos que mutem estado
- Comparável por valor (frozen=True dá __eq__ e __hash__)
- Sem dependências externas

Entregáveis:
- src/domain/value_objects/[arquivo].py
- tests/unit/domain/test_[arquivo].py com 4+ cenários (parametrize)
  - Casos válidos
  - Casos inválidos
  - Igualdade entre VOs
  - Hash consistente

Commit: feat(qdi-domain): adicionar value object [NomeVO]
```

---

## 4. Criar Port + Adapter

```
Tarefa: criar Port [NomePort] + Adapter [Tecnologia]

Camadas Clean Arch:
- Port: src/application/ports/
- Adapter: src/infrastructure/adapters/

Princípios NN aplicáveis: Clean Arch (DI), §10.[X]

Especificação Port (ABC):
- Interface abstrata para [responsabilidade]
- Métodos abstratos:
  - async def [metodo1]([params]) -> [retorno]
  - async def [metodo2]([params]) -> [retorno]

Especificação Adapter:
- Implementação concreta usando [biblioteca/SDK]
- Tratamento de erro com structlog
- Retry/circuit breaker via tenacity + pybreaker (se for I/O remoto)
- Cache LRU se aplicável

Restrições:
- Port: ABC + @abstractmethod (NÃO usar Protocol)
- Adapter: structlog para logs estruturados
- Sem print() em nenhum momento
- Adapter recebe dependências via __init__ (não lê env diretamente)
- Configuração via pydantic-settings em src/infrastructure/config/settings.py

Entregáveis:
- src/application/ports/[modulo].py
- src/infrastructure/adapters/[tecnologia]_[modulo].py
- tests/unit/application/test_[modulo]_port.py com mock
- tests/unit/infrastructure/test_[tecnologia]_[modulo]_adapter.py
- Atualizar src/presentation/api/dependencies.py para injetar

Validação:
- make test passa
- Adapter não vaza tipos da biblioteca para o Port

Commits:
- arch(qdi-app): definir Port [NomePort]
- feat(qdi-infra): implementar [Tecnologia]Adapter para [NomePort]
```

---

## 5. Criar Use Case

```
Tarefa: criar Use Case [NomeUseCase] na application layer

Camada Clean Arch: src/application/use_cases/
Princípios NN aplicáveis: §10.[X], §10.[Y]

Especificação:
- Comando (input): @dataclass(frozen=True) ComandoXxx com:
  - [campo1: tipo]
  - [campo2: tipo]
- Resultado (output): @dataclass(frozen=True) ResultadoXxx com:
  - [campo1: tipo]
- Orquestração:
  1. [etapa 1] — chamar [Port1]
  2. [etapa 2] — chamar [Port2]
  3. [etapa 3] — método de domain ([entidade].[método])
  4. [etapa 4] — persistir via [Repository]

Restrições:
- Use Case NÃO contém regras de negócio — apenas orquestra
- Regras de negócio vão nos métodos das entities
- Dependências via __init__ (DI explícita)
- Sem acesso a filesystem, sem print(), sem hardcode
- structlog com tenant_id em todo log

Entregáveis:
- src/application/use_cases/[arquivo].py
- tests/unit/application/test_[arquivo].py com:
  - Cenário feliz
  - Cenário de erro em cada etapa (mock que falha)
  - Verificação de chamadas aos ports

Commit: feat(qdi-app): adicionar use case [NomeUseCase]
```

---

## 6. Criar Router FastAPI

```
Tarefa: criar router HTTP /[recurso] na presentation layer

Camada Clean Arch: src/presentation/api/routers/
Princípios NN aplicáveis: §10.1 (multi-tenant), §10.3 (idempotência)

Especificação:
- Endpoints:
  - POST /[recurso]/ — criar
  - GET /[recurso]/{id} — recuperar
  - PATCH /[recurso]/{id} — atualizar (se aplicável)
- Schemas Pydantic v2 em src/presentation/api/schemas.py:
  - [Recurso]Request com validações field_validator
  - [Recurso]Response com from_attributes=True

Restrições obrigatórias:
- Toda rota autenticada exige Depends(get_current_user_tenant) → tenant_id via JWT
- POST exige header Idempotency-Key (validado por middleware)
- response_model explícito em todo endpoint
- summary e description em PT-BR (vão para Swagger)
- tags=["[Tag PT-BR]"]
- Tratamento explícito: ValueError → 400, RuntimeError → 500

Entregáveis:
- src/presentation/api/routers/[recurso]_router.py
- Atualizar src/presentation/api/schemas.py
- Atualizar src/presentation/api/main.py (include_router)
- tests/unit/presentation/test_[recurso]_router.py com:
  - 401 sem JWT
  - 400 sem Idempotency-Key
  - 201 happy path
  - 404 recurso não encontrado
  - RLS isolamento (mock 2 tenants)

Commit: feat(qdi-api): adicionar router /[recurso] com JWT + idempotência
```

---

## 7. Criar Migration SQL com RLS

```
Tarefa: criar migration [número] para [propósito]

Camada Clean Arch: src/infrastructure/db/migrations/
Princípios NN aplicáveis: §10.1 (RLS), §10.2 (vigencia), §10.4 (WORM)

Especificação:
- Nome do arquivo: [NNNN]__[verbo]_[objeto].sql (ex: 0004__criar_tabela_perguntas.sql)
- Tabelas a criar/alterar: [lista]
- Colunas obrigatórias em toda tabela qdi.*:
  - id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  - tenant_id UUID NOT NULL  ← Multi-tenant
  - criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - versao_otimista INT NOT NULL DEFAULT 1  ← Lock
- Para tabelas de regras: vigencia_inicio TIMESTAMPTZ NOT NULL, vigencia_fim TIMESTAMPTZ
- Constraints:
  - PK em id
  - FK para outras tabelas com ON DELETE [CASCADE/RESTRICT]
  - CHECK em campos enumerados
- Índices:
  - idx_[tabela]_tenant_id
  - idx_[tabela]_[campo_busca]
- RLS:
  - ENABLE ROW LEVEL SECURITY
  - 4 policies: SELECT, INSERT, UPDATE, DELETE
  - Usar auth.jwt() ->> 'tenant_id' (NÃO auth.uid())
- Triggers (se aplicável):
  - block_update_finalizado (para WORM)
  - atualizar_atualizado_em

Restrições:
- Nunca criar tabela sem RLS
- Nunca usar VARCHAR(N) onde TEXT funciona
- Sempre TIMESTAMPTZ (nunca TIMESTAMP)
- Comentários SQL em PT-BR (-- ...)

Entregáveis:
- src/infrastructure/db/migrations/[NNNN]__[nome].sql
- Atualizar docker-compose.yml para incluir migration
- tests/integration/test_migration_[NNNN].py validando RLS

Validação:
- make down && make dev
- docker exec qdi-db psql -c "\d+ [tabela]"
- Verificar "Row Level Security is enabled"

Commit: feat(qdi-infra): migration [NNNN] criar tabela [nome] com RLS
```

---

## 8. Criar testes unitários

```
Tarefa: criar testes unitários para [arquivo]

Camada: tests/unit/[domain|application|infrastructure|presentation]/
Princípios NN aplicáveis: §10.10 (cobertura DOMAIN ≥ 85%)

Especificação:
- Para cada classe pública: criar TestNomeClasse
- Para cada método: ≥ 3 cenários (feliz, borda, erro)
- Usar pytest.mark.parametrize para múltiplos casos
- Fixtures em conftest.py (não duplicar setup)
- Mocks via pytest-mock (não unittest.mock direto)

Padrão de teste:
```python
import pytest
from src.[camada].[modulo] import [Classe]


class Test[Classe]:
    """Testes de [Classe]."""

    @pytest.mark.parametrize("entrada,esperado", [
        ([caso1], [resultado1]),
        ([caso2], [resultado2]),
    ])
    def test_[acao]_com_[contexto](self, entrada, esperado) -> None:
        """[descrição PT-BR do que valida]."""
        resultado = [Classe]([entrada]).[metodo]()
        assert resultado == esperado

    def test_rejeita_[entrada_invalida](self) -> None:
        """Deve levantar ValueError com mensagem específica."""
        with pytest.raises(ValueError, match=r"[regex]"):
            [Classe]([entrada_invalida])
```

Restrições:
- Sem I/O real em testes unit (sem rede, sem DB, sem filesystem)
- Para integração com I/O: usar testcontainers em tests/integration/
- Cada teste tem docstring PT-BR
- Asserts específicos (não assert True)

Entregáveis:
- tests/unit/[camada]/test_[arquivo].py com:
  - 1+ cenários felizes (parametrize)
  - 1+ cenários de erro/borda
  - Cobertura ≥ 90% do arquivo testado

Validação:
- pytest tests/unit/[camada]/test_[arquivo].py -v
- pytest tests/unit/[camada]/test_[arquivo].py --cov=src/[camada]/[arquivo]

Commit: test(qdi-test): adicionar testes unit para [arquivo]
```

---

## 9. Criar testes de integração

```
Tarefa: criar testes de integração para [funcionalidade]

Camada: tests/integration/
Princípios NN aplicáveis: anti-padrão "Mock de DB em integration"

Especificação:
- Usar testcontainers (PostgresContainer)
- Aplicar migrations em fixture de módulo
- Validar comportamento real com banco
- Cenários obrigatórios:
  - Happy path completo
  - RLS isolamento (2 tenants distintos)
  - Idempotência (2x mesma chave → mesmo resultado)
  - Concorrência (lock otimista funcionando)

Padrão:
```python
import pytest
from testcontainers.postgres import PostgresContainer
from supabase import create_async_client

@pytest.fixture(scope="module")
def pg_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        # Aplicar migrations
        with open("src/infrastructure/db/migrations/0001__...sql") as f:
            pg.exec_in_container(["psql", ..., "-c", f.read()])
        yield pg


@pytest.fixture
async def client_a(pg_container):
    return await create_async_client(...)


@pytest.fixture
async def client_b(pg_container):
    return await create_async_client(...)


@pytest.mark.asyncio
async def test_rls_isola_tenants(client_a, client_b):
    """Tenant A NÃO deve ver dados de tenant B."""
    # ...
```

Restrições:
- pytest-asyncio asyncio_mode = "auto"
- testcontainers scope=module (não criar container por teste)
- Cleanup automático ao fim do módulo

Entregáveis:
- tests/integration/test_[funcionalidade].py
- Atualizar pyproject.toml se faltar testcontainers nas deps

Commit: test(qdi-test): integration tests para [funcionalidade] com testcontainers
```

---

## 10. Refatoração Clean Arch

```
Tarefa: refatorar [arquivo] removendo [violação Clean Arch]

Camada afetada: [camada]
Princípio violado: [Clean Arch — dependência apontando para fora]

Diagnóstico:
- O arquivo [arquivo] na camada [X] importa/acessa [Y] (camada Z)
- Isso fere a regra de ouro: dependências apontam para dentro
- Exemplo concreto: [trecho de código]

Plano de refatoração:
1. Definir Port [NomePort] em src/application/ports/
2. Implementar Adapter [Tecnologia][Nome]Adapter em src/infrastructure/adapters/
3. Refatorar [arquivo original] para receber Port via __init__
4. Atualizar src/presentation/api/dependencies.py (injetar adapter)
5. Atualizar testes existentes para usar mock do Port

Restrições:
- Preservar comportamento externo (nenhum endpoint muda contrato)
- Refatoração em commits pequenos e atômicos
- Cada commit deve manter make test verde
- Sem reescrever — usar Edit (diff)

Entregáveis:
- src/application/ports/[nome].py (Port)
- src/infrastructure/adapters/[nome].py (Adapter)
- [arquivo original] refatorado (sem import direto)
- src/presentation/api/dependencies.py atualizado
- Testes existentes ajustados

Validação:
- grep -r "from os" src/application/ → zero ocorrências (exemplo)
- make test passa
- make lint zero warnings

Commits:
- arch(qdi-app): definir Port [NomePort]
- feat(qdi-infra): implementar [Adapter]
- refactor(qdi-app): [arquivo] usar Port em vez de [Y]
```

---

## 11. Criar ADR

```
Tarefa: criar ADR-[NNN] sobre [decisão arquitetural]

Localização: docs/adrs/
Formato: padrão Michael Nygard

Especificação:
- Número: próximo disponível (ler ls docs/adrs/ e somar 1)
- Título: ADR-[NNN]: [decisão concisa, infinitivo]

Estrutura obrigatória:
```markdown
# ADR-[NNN] — [Título]

**Data:** [YYYY-MM-DD]
**Status:** [Proposto | Aceito | Substituído | Obsoleto]
**Autor:** [nome]
**Substituído por:** [se aplicável, ADR-XXX]

## Contexto
[Por que esta decisão precisa ser tomada agora?]
[Quais forças estão em jogo?]

## Decisão
[O que foi decidido, em linguagem ativa]

## Alternativas consideradas
1. [Alternativa A] — descartada porque [razão]
2. [Alternativa B] — descartada porque [razão]

## Consequências
- ✅ Positiva 1
- ✅ Positiva 2
- ⚠️ Trade-off 1
- ❌ Negativa aceita

## Referências
- [link/ADR/auditoria/INSTRUCAO_KICKOFF §X.Y]
```

Restrições:
- Linguagem PT-BR formal
- Citar princípio NN específico que motiva
- Citar ADRs relacionados
- Ser específico: "Migrar para AsyncClient" não "melhorar performance"

Entregáveis:
- docs/adrs/ADR-[NNN]-[slug].md

Commit: arch(qdi-docs): publicar ADR-[NNN] sobre [decisão]
```

---

## 12. Code review automatizado

> **Quando usar:** após terminar uma feature, antes do commit final.

```
Faça code review crítico das mudanças desde o último commit.

Avalie:
1. Aderência Clean Architecture (dependências apontam para dentro?)
2. Aderência aos 12 princípios não-negociáveis (lista cada um)
3. Anti-padrões (print, Optional, datetime.utcnow, etc.)
4. Cobertura de testes (DOMAIN ≥ 85%? cenários de erro presentes?)
5. Citação de base legal (toda regra fiscal cita art./§/anexo?)
6. Tipagem mypy strict (sem Any, sem ignore type)
7. Docstrings PT-BR completas
8. Conventional Commits PT-BR

Para cada problema encontrado, liste:
- Arquivo:linha
- Princípio violado ou anti-padrão
- Sugestão de correção (snippet curto)

Termine com:
- ✅ Pode commitar
- ⚠️ Precisa ajustar antes (lista)
- ❌ Bloqueado, precisa refatoração maior

Não modifique nada — apenas reporte.
```

---

## 13. Debug de bug runtime

```
Estou com bug runtime: [descrição]

Stack trace:
```
[colar stack trace completo]
```

Comando que reproduz:
```bash
[comando]
```

Comportamento esperado: [descrição]
Comportamento observado: [descrição]

Tarefa: investigar e corrigir.

Procedimento:
1. Localizar arquivo:linha do erro
2. Ler o código ao redor (use Read tool)
3. Verificar se o erro está nas regras de domain ou no adapter
4. Confirmar se há teste que cobre esse caso (se não houver, criar)
5. Aplicar correção (Edit, não rewrite)
6. Adicionar teste regression
7. Validar com make test

Restrições:
- Sem mudar contrato público (API/método)
- Sem suprimir o erro (try/except amplo)
- Commit obrigatório: fix(qdi-[escopo]): corrigir [problema]
  com referência ao bug e ao teste regression

Saída esperada:
- Análise da causa raiz (1 parágrafo)
- Diff da correção
- Teste regression
- Commit message
```

---

## 14. Atualizar documentação

```
Tarefa: atualizar documentação após mudanças em [arquivo/feature]

Identificar quais docs precisam atualizar:
- README.md raiz — se mudou setup ou estrutura
- docs/01_arquitetura.md — se mudou Clean Arch
- docs/02_dominio_qdi.md — se mudou entidade
- docs/03_roadmap_sprint_1.md — se mudou cronograma
- docs/refs/04_METODOLOGIA.md — se mudou cálculo de score
- docs/adrs/ — se decisão arquitetural

Restrições:
- Sempre atualizar a documentação ANTES do commit final
- Diagramas Mermaid se houver fluxo
- Tabelas para trade-offs
- PT-BR técnico-formal

Entregáveis:
- Diff dos arquivos de doc atualizados
- Commit: docs(qdi-docs): atualizar [doc] após [mudança]
```

---

## 15. Pesquisa de norma legal

> **Quando usar:** ao ter dúvida sobre dispositivo legal aplicável.

```
Pesquisa normativa: [questão legal]

Contexto:
- Empresa: [setor, regime, porte]
- Operação: [descrição]
- Dúvida: [pergunta concreta]

Tarefa:
1. Buscar em _DEVELOPER/_LEGISLACAO/01_REFORMA_TRIBUTARIA/:
   - LC 214/2025 — texto integral
   - EC 132/2023
   - LC 227/2026 (CGIBS)
2. Buscar em _DEVELOPER/_LEGISLACAO/03_NORMAS_TECNICAS/:
   - NT 2025.002 v1.33+
3. Buscar em _DEVELOPER/_LEGISLACAO/05_PARECERES_INTERNOS/:
   - PT-001 a PT-011
4. Buscar em _DEVELOPER/_LEGISLACAO/02_TABELAS_OFICIAIS/:
   - cClassTrib, cCredPres, CST, NCM

Apresente:
1. Dispositivo aplicável (citação literal: art., §, inciso)
2. Vigência (a partir de quando)
3. Hierarquia (EC > LC > Lei > Decreto > NT)
4. Conflitos com outras normas (se houver)
5. Posição em parecer interno PT-XXX (se houver)

Em caso de dúvida ou ambiguidade:
- NÃO inventar interpretação
- Marcar como "requer parecer adicional"
- Sugerir qual parecer interno consultar

Saída:
- Citação textual completa do(s) artigo(s) aplicável(is)
- Resposta direta à dúvida
- Caveats (vigência, regime tributário, exceções)
- Referência a PT-XXX se houver
```

---

## 16. Prompts compostos para tarefas grandes

### 16.1 Implementar feature MUST completa

```
Tarefa GRANDE: implementar feature MUST [Nome] da Onda 1.0.

Etapas (pedir confirmação após cada uma):

ETAPA 1 — Domain
- Criar entidade(s) e value object(s) puros
- Testes unitários ≥ 90% cobertura
- ADR se necessário

ETAPA 2 — Application
- Criar Port(s) necessário(s)
- Criar Use Case orquestrador
- Testes unitários com mocks dos Ports

ETAPA 3 — Infrastructure
- Implementar Adapter(s)
- Migration SQL com RLS
- Testes integration com testcontainers

ETAPA 4 — Presentation
- Schemas Pydantic v2
- Router FastAPI com JWT + Idempotência
- Testes de rota

ETAPA 5 — Frontend (se aplicável)
- Schema Zod
- Componente Next.js
- Teste Playwright E2E

ETAPA 6 — Documentação
- Atualizar docs/refs/
- Atualizar OpenAPI tags

ETAPA 7 — Validação
- make test (geral verde)
- Cobertura DOMAIN ≥ 87%
- Smoke E2E manual

Após cada etapa, aguarde minha confirmação ("ok prossiga") antes da próxima.
Pedir-me opinião sempre que houver decisão arquitetural relevante.
```

---

## 17. Template de prompt — fim do dia

```
Resumo da sessão:

1. O que foi entregue hoje (commits PT-BR + arquivos modificados)
2. Cobertura DOMAIN atual (rodar pytest --cov)
3. P0/P1 abertos no momento
4. Bloqueios encontrados (se houver)
5. 3 próximas ações para amanhã

Atualize:
- `_DEVELOPER/ORIENTACAO_CURSOR/04_PLANO_EXECUCAO.md` (marcar tasks completadas)
- TASKS.md se existir

Verifique:
- git status limpo
- make test verde
- Sem TODO esquecidos no código

Faça última validação e me avise se posso encerrar.
```

---

## 18. Atalhos do Cursor (cheatsheet)

| Atalho | Ação |
|---|---|
| `Cmd+L` | Abrir chat lateral (perguntar ao agente) |
| `Cmd+K` | Editar inline (selecionar código + descrever mudança) |
| `Cmd+I` | Composer (mudanças multi-arquivo) |
| `Cmd+/` | Toggle Cursor Tab (autocomplete IA) |
| `Cmd+Shift+P` | Command palette |
| `Cmd+P` | File quick open |
| `Cmd+Shift+L` | Adicionar próxima ocorrência (multi-cursor) |
| `Cmd+D` | Selecionar próxima ocorrência da palavra |
| `@file` | Mencionar arquivo no chat |
| `@folder` | Mencionar pasta no chat |
| `@docs` | Mencionar docs (Cursor docs indexados) |
| `@web` | Pesquisa web em tempo real |
| `@git` | Contexto do Git (commits, diff) |

---

## 19. Como pedir help quando travar

> Se o Cursor estiver dando voltas, **PARE** e use este prompt:

```
Estou travado. Vou pedir uma análise honesta.

Contexto:
- Tarefa: [descrição]
- O que já tentei: [lista]
- Erros que vi: [lista]
- Tempo gasto: [Xh]

Pergunta:
1. Estou abordando o problema do ângulo errado?
2. Há um princípio NN que está me forçando complexidade desnecessária?
3. Vale a pena fazer um ADR para registrar trade-off e seguir?
4. Devo pedir ajuda ao Allan/Claude (chat externo) antes de continuar?

Não escreva código nesta resposta — apenas análise estratégica em PT-BR.
```

---

## 20. Encerramento

Allan, esta biblioteca cobre **as 90% das situações comuns** durante S0.5 → S4. Para os 10% restantes (situações novas), o template **§4.2 do `03_GUIA_DESENVOLVIMENTO.md`** fornece estrutura genérica.

**Lembre-se:** prompt curto e específico > prompt longo e genérico. Citar princípio NN, citar arquivo:linha, citar base legal — sempre que possível.

**Bom desenvolvimento.**

---

**Autor:** Claude · **Versão:** 1.0 · **Data:** 30/04/2026
