# Arquitetura QDI

## Clean Architecture

Estrutura obrigatoria:

```text
src/
├── domain/         # entidades, value objects e ports; zero dependencia externa
├── application/    # casos de uso; depende apenas de domain
├── infrastructure/ # adapters, repositories e clients externos
└── presentation/   # API FastAPI e schemas; depende de application
```

Regra de ouro: dependencias apontam para dentro.

## Principios Transversais Tributiq

1. Multi-tenant desde o dia 1, com RLS no PostgreSQL.
2. Versionamento normativo com vigencia sobreposta, sem hardcode.
3. Imutabilidade de evidencias, com append-only, hash e WORM.
4. RAG com guardrails: sem citacao valida, resposta rejeitada.
5. Idempotencia com Idempotency-Key obrigatoria.
6. Observabilidade end-to-end com OpenTelemetry e trace_id em logs.
7. Independencia de ERP por nucleo canonico e conectores isolados.

## Regras de Modelagem

- Entidades e value objects pertencem a domain.
- Portas/interfaces ficam em domain quando expressam contratos do nucleo.
- Casos de uso ficam em application e orquestram regras sem depender de framework.
- Implementacoes externas ficam em infrastructure.
- Schemas HTTP ficam em presentation usando Pydantic v2.
- Regras tributarias devem carregar base legal, vigencia e fonte.

## Analogia

Pense no domain como packages PL/SQL de regra central: ele nao deve conhecer tela, API, fila ou fornecedor. Infrastructure e como os adapters de integracao do Winthor: conectam o nucleo ao mundo externo sem contaminar a regra.
