# Regras de Codigo QDI

## Idioma

- Respostas em PT-BR.
- Comentarios e docstrings em PT-BR.
- Termos tecnicos em ingles podem ser mantidos, com explicacao curta na primeira ocorrencia quando necessario.

## Python

- Usar Python 3.12+.
- Usar Pydantic v2 para schemas externos.
- Nao usar dataclass para schemas de entrada/saida de API.
- Preferir tipos explicitos e codigo compativel com mypy strict.
- Nao deixar print esquecido; usar logger.
- Testes com pytest.

## FastAPI

- Camada presentation contem rotas, dependencias de framework e schemas HTTP.
- Casos de uso devem ser chamados pela camada presentation, sem regra de negocio pesada no endpoint.
- Operacoes mutaveis devem considerar Idempotency-Key.
- Logs devem carregar trace_id quando disponivel.

## Banco e Multi-Tenant

- Supabase/PostgreSQL 16.
- RLS obrigatoria para isolamento de tenant.
- Nunca filtrar tenant apenas na aplicacao quando a protecao pertence ao banco.
- Evidencias relevantes devem ser append-only com hash quando aplicavel.

## Commits e Qualidade

Antes de declarar tarefa concluida:
- Rodar testes aplicaveis.
- Rodar lint/format quando disponivel.
- Manter ou aumentar cobertura em domain.
- Usar Conventional Commits quando Allan autorizar commit.
- Nao fazer git push, git rebase ou git commit sem confirmacao explicita.
