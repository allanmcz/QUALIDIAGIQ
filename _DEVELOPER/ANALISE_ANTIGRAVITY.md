# Análise de Entendimento — QualiDiagIQ (QDI)
**Autor:** Antigravity (IA Pair Programmer / Arquiteto)
**Data:** 28 de Abril de 2026

---

## 1. Visão Executiva do Produto
O **QualiDiagIQ (QDI)** é a "porta de entrada" (Lead Magnet) do ecossistema **Tributiq**. Trata-se de um SaaS voltado à automação do diagnóstico tributário no contexto da Reforma Tributária do Consumo no Brasil (EC 132/2023 e LC 214/2025). 

A genialidade do negócio reside em transformar uma consultoria tributária tradicional e custosa em um produto escalável (SaaS). Através de um funil otimizado (do Free ao Enterprise), a ferramenta entrega um **Score de Maturidade** acompanhado de recomendações geradas por IA (Anthropic Claude). Diferente de concorrentes que se limitam a avaliações qualitativas e genéricas, o QDI traciona diferenciais inatingíveis para a maioria:
- Simulador quantitativo em nível de SKU (CBS+IBS+IS).
- Integração nativa de ERPs complexos (ex: Winthor, aproveitando expertise de domínio).
- RAG baseado em norma legal (Lexiq).
- Aderência pioneira à nova **ABNT NBR 17301:2026** (Compliance Tributário).

## 2. Posição no Ecossistema (Bounded Contexts)
O QDI possui fronteiras muito claras, o que é vital para evitar escopo *creep* (inchaço):
- **O que FAZ:** Mede prontidão, diagnostica falhas, gera um Score comparativo e emite um relatório final em PDF, captando leads.
- **O que NÃO FAZ:** Não apura tributos contínuos (papel do **QAI**), não gerencia Split Payment (papel do **QFC**), não audita motores continuamente (papel do **QMI**) nem atua na recuperação de créditos do passado (RestituIQ).

## 3. Metodologia de Avaliação
O diagnóstico baseia-se em um questionário de 35 perguntas criteriosamente mapeadas sobre **7 Dimensões**:
1. Fiscal
2. Estratégica
3. Contábil
4. Financeira
5. Operacional
6. Tecnológica
7. **Compliance ABNT 17301** (Diferencial que utiliza framework PDCA nos 7 eixos da norma).

O resultado não é apenas absoluto (0 a 100), mas também **relativo** (Percentil Setorial), graças à coleta multi-tenant que permite benchmark anônimo contra concorrentes de mesmo porte e segmento.

## 4. Arquitetura e Engenharia de Software
O sistema não é um mero script. Foi arquitetado como um SaaS de nível Enterprise focado na manutenibilidade em longo prazo:
- **Clean Architecture:** 4 camadas estritas. O domínio (`domain/`) é 100% livre de frameworks externos (puro Python com `dataclasses` tipados). A API FastAPI só toca a camada de Aplicação (`application/`). O banco de dados Supabase e o Claude ficam isolados em Adapters na Infraestrutura (`infrastructure/`).
- **Stack Python Moderna:** Python 3.12, FastAPI (async), Pydantic v2 para validação robusta nas bordas (Presentation/Infra).
- **Multi-Tenant Raiz:** Supabase (PostgreSQL 16) utilizando Row Level Security (RLS) para isolar dados (Toda query carrega o `tenant_id` forçosamente via sessão).
- **Princípios Transversais (Cross-cutting):** Imutabilidade de evidências, Idempotência de APIs, Versionamento Normativo (evitando código engessado em leis mutáveis) e observabilidade (OpenTelemetry).

## 5. O Fluxo de Trabalho (Roadmap Sprint 1)
Neste primeiro Sprint (30 dias), o foco não é a IA logo de cara, mas construir um motor de regras determinístico e resiliente:
- **Semana 1:** Setup da arquitetura e implementação impecável do Domínio (Value Objects de Score e Entidades). Testes unitários com mais de 85% de cobertura.
- **Semana 2:** Casos de uso (Application) e repositórios concretos (Infra / Supabase).
- **Semana 3:** Presentation layer (Rotas FastAPI, Schemas Pydantic, isolamento de Tenants).
- **Semana 4:** Fechamento do fluxo (Lead Form -> Diagnóstico -> Geração determinística do PDF via WeasyPrint -> Disparo de e-mail).

## 6. Próximos Passos Imediatos
Estamos posicionados para iniciar a primeira linha de código na camada de *Domain* (`score.py`). Antes da codificação técnica, garantimos a integridade local:
1. `make install`
2. `docker compose up -d db`
3. E, na sequência, criaremos os *Value Objects* com testes completos de *edge cases*.

---
*Este documento comprova o alinhamento arquitetural e estratégico para iniciarmos a codificação sem atritos, respeitando todas as regras, padrões de projeto e restrições estabelecidas.*
