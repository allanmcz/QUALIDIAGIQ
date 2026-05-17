# Memoria do Projeto QualiDiagIQ

## Identidade

- Nome: QualiDiagIQ
- Sigla: QDI
- Tipo: SaaS multi-tenant
- Status: MVP em planejamento, Sprint 1 de 12
- Funcao: diagnostico tributario automatizado para a Reforma Tributaria do Consumo
- Ecossistema: Tributiq, familia de produtos Quali*IQ

## Usuario Principal

Allan Marcio e Analista de Sistemas e Contador, com mais de 20 anos de experiencia.

Contexto tecnico:
- Delphi/Object Pascal
- Oracle e administracao de banco de dados
- ERP Winthor/TOTVS PC Sistemas
- Python 3.12, FastAPI, Pydantic, LangChain
- TypeScript, Fastify, Zod
- Supabase, Docker, OrbStack, VS Code/Cursor

Dominio:
- Contabilidade brasileira
- Legislacao tributaria
- SPED, ICMS, PIS/COFINS
- EC 132/2023 e LC 214/2025

## Objetivo do QDI

O QDI deve diagnosticar maturidade, riscos e aderencia tributaria no contexto da Reforma Tributaria do Consumo. O MVP e um lead magnet self-service, sem assumir escopos de apuracao continua, split payment ou auditoria continua de motores fiscais.

## Stack Obrigatoria

- Python 3.12+
- FastAPI 0.115+
- Pydantic v2
- Supabase/PostgreSQL 16 com RLS e pgvector
- LangChain e LangGraph
- Next.js 15 com App Router
- Tailwind e shadcn/ui
- WeasyPrint para PDF
- Docker e OrbStack
- pytest, Playwright, ruff, black e mypy strict

## Fora de Escopo do MVP

- Apuracao CBS/IBS continua: produto QAI
- Split payment orquestrador: produto QFC
- Auditoria continua de motores: produto QMI
- Defesa de autos de infracao
- Recuperacao ativa de creditos pre-CBS

Quando um pedido cair nesses itens, lembrar o limite do MVP e propor redirecionamento.
