# Plano de Execução Completo — QualiDiagIQ (Sprint 1)
**Autor:** Antigravity (IA Pair Programmer / Arquiteto)
**Data:** 28 de Abril de 2026

Este plano detalha a rota de execução técnica do MVP do QualiDiagIQ ao longo da Sprint 1 (30 dias). Ele traduz a estratégia de negócios e os requisitos de domínio para tarefas técnicas sequenciais, alinhadas com a **Clean Architecture** e garantindo que o valor seja entregue progressivamente.

---

## 🎯 Objetivo da Sprint 1
**Entregável:** API funcional cobrindo o fluxo completo: Captura do Lead -> Wizard Adaptativo -> Motor de Score (compesos calibráveis) -> Geração do Relatório PDF via WeasyPrint -> Envio por e-mail. *(Nota: IA Generativa / RAG entra apenas a partir do Sprint 4).*

---

## FASE 1: Fundação e Core Domain (Dias 1 a 7)
*O coração da aplicação. Sem frameworks externos, apenas regras de negócio puras em Python.*

- **Dia 1 (Setup e Value Objects base):**
  - Configuração do ambiente (`make install`, Docker DB).
  - Implementação de `ScoreNumerico`, `ScoreCompleto`, `Dimensao` e `PercentilSetorial` usando `dataclass` (frozen=True).
  - Testes unitários limítrofes com `pytest`.
- **Dia 2 e 3 (Entidades Core):**
  - Construção do Agregado Principal: `Diagnostico`.
  - Entidades periféricas: `EmpresaInfo`, `Respondente`.
  - Implementação da lógica de transição de status do diagnóstico (`EM_ANDAMENTO` -> `FINALIZADO`).
- **Dia 4 e 5 (Perguntas e Respostas):**
  - Entidades `Pergunta` (com pesos, condicionais e base legal) e `Resposta` (com pontuação convertida).
  - Testes cobrindo os diferentes tipos de respostas (Ternárias, Escala 1-5).
- **Dia 6 e 7 (Ports / Interfaces):**
  - Definição dos *Repositories Interfaces* (Ports) para as entidades acima.
  - Setup inicial do Supabase (Schema SQL e Migrations iniciais usando RLS com `tenant_id`).

---

## FASE 2: Casos de Uso e Adapters (Dias 8 a 14)
*Orquestrando as entidades e conectando-as à infraestrutura.*

- **Dia 8 e 9 (Motor de Score):**
  - Implementação de `calcular_score_use_case.py`.
  - Aplicação dos pesos por dimensão e cálculo da aderência à ABNT NBR 17301.
- **Dia 10 (Wizard Adaptativo):**
  - Use case `gerar_questionario_adaptativo.py`. Lógica para filtrar as 35 perguntas baseadas no regime, segmento e porte.
- **Dia 11 e 12 (Supabase Repositories):**
  - Implementação concreta dos repositórios consumindo a API do Supabase em Python (`asyncpg` / `supabase-py`).
  - Testes de integração (local) para garantir o isolamento Multi-tenant (RLS).
- **Dia 13 e 14 (Fechamento da Fase 2):**
  - Definição final dos 7 eixos da Dimensão ABNT no motor.
  - Code Review e Merge das features centrais.

---

## FASE 3: Presentation Layer (Dias 15 a 21)
*A borda HTTP. Recebendo requisições e validando com Pydantic.*

- **Dia 15 e 16 (API FastAPI Base):**
  - Setup do `main.py` e configuração do middleware de resolução do Tenant (`X-Tenant-ID`).
  - Endpoint `POST /diagnosticos` e `GET /diagnosticos/:id`.
- **Dia 17 e 18 (Schemas e Validação):**
  - Criação dos schemas Pydantic v2 para as requests e responses.
  - Validação estrita de CNPJ, UFs e regimes na entrada.
- **Dia 19 e 20 (Motor Determinístico de Gaps e Transparência):**
  - Implementação das recomendações hardcoded (Free tier) associadas aos Gaps críticos.
  - Exposição do endpoint público `GET /metodologia` com os pesos.
- **Dia 21:**
  - Testes de integração da API usando `httpx` via FastAPI TestClient.

---

## FASE 4: Saídas, PDFs e Fechamento (Dias 22 a 30)
*Entregando o valor percebido pelo usuário.*

- **Dia 22 e 23 (WeasyPrint):**
  - Criação dos templates Jinja2 base HTML/CSS (print-friendly) com o branding da Tributiq.
  - Implementação do adapter do gerador de PDF.
- **Dia 24 (Armazenamento):**
  - Upload automático do PDF finalizado para o Supabase Storage e registro do hash (WORM).
- **Dia 25 e 26 (Lead Form e SMTP):**
  - Finalização do fluxo de captura de e-mail ao final do diagnóstico.
  - Integração SMTP / envio do e-mail com link de acesso único.
- **Dia 27 e 28 (Polimento e Docs):**
  - Testes End-to-End (E2E) no fluxo completo (API).
  - Refinamento do Swagger/OpenAPI e adição de documentação complementar.
- **Dia 29 e 30 (Entrega e Retrospectiva):**
  - Verificação de latência (alvo de execução do motor < 2 segundos).
  - Validação de Segurança do RLS.
  - Deploy em homologação e gravação da demonstração.

---

## Diretrizes de Qualidade Contínua (Em todas as fases)
1. Antes do commit: Executar `make format` (Black+Ruff) e `make lint`.
2. Cobertura de Testes: Mínimo 85% para *Domain* e *Application* com `make test`.
3. Revisão de Código: Toda nova funcionalidade deve ser revisada pelas lentes do Clean Architecture (A dependência aponta SEMPRE para dentro).
