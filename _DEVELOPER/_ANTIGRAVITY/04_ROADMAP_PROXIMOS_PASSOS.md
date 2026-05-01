# 04 - Roadmap e Próximos Passos (QualiDiagIQ)

Com a arquitetura central validada e o "caminho feliz" do usuário garantido pelo teste E2E, o foco do desenvolvimento precisa migrar da estruturação de regras estáticas para a **ativação da infraestrutura em nuvem e a expansão do valor**. 

Abaixo detalhamos o Roadmap recomendado.

## 1. Fase de Desmockagem (Imediato - Sprint 3)

Os Mocks locais protegeram o desenvolvimento focado no Frontend, mas não devem escalar para o ambiente de *Staging*.
- **Configuração do Supabase Completa**: Adicionar ao `docker-compose.yml` os contêineres faltantes do Supabase (GoTrue para Auth, Storage-API para Buckets e PostgREST). Isso permitirá testar a API do Supabase real (com Row Level Security) em `localhost`.
- **Containersing PDF (WeasyPrint)**: Modificar a imagem local Docker (`Dockerfile` do Backend) para garantir que todas as dependências nativas em C do `libpango` e `cairo` sejam empacotadas no container Debian/Alpine. Isso elimina a dependência de OS da máquina hospedeira e remove o "Mock" PDF.
- **Integração Real SMTP**: Configurar provedores locais (como Mailhog no Docker) ou SendGrid/AWS SES de Dev para garantir o disparo efetivo de e-mail ao invés de usar `print` no terminal.

## 2. Injeção de Inteligência Artificial (Sprint 4)

O coração do diferencial do *QualiDiagIQ* (em relação aos questionários convencionais do Google Forms) é a devolutiva analítica baseada no "Lexiq" (RAG).
- **Integração Anthropic Claude (API)**: Construir um novo adapter no Backend focado no SDK da Anthropic. O motor de score deve passar os resultados do questionário e as dimensões diretamente para um modelo *Claude 3.5 Sonnet* como Contexto (Prompt Engineering).
- **Prompt Base de Consultoria**: Treinar o modelo via Prompt para assumir a *persona* de Consultor Tributário Sênior e devolver recomendações não estáticas, avaliando as faixas de GAP do percentil da empresa em relação às melhores práticas da reforma (EC 132/2023).
- **Orquestração Assíncrona**: O tempo de chamada a LLMs pode adicionar 5 a 15 segundos à resposta. Será vital implementar *Celery* ou background tasks, respondendo "202 Accepted" ao frontend imediatamente, enviando o PDF apenas por e-mail quando a IA concluir o trabalho de escrita.

## 3. Gestão Multi-Tenant e Autenticação (Sprint 5)

Como é um SaaS:
- **Painel Administrativo (B2B)**: Criar uma área logada (usando `Supabase Auth`) onde as Assessorias Parceiras possam acompanhar os "Leads" que preencheram o Diagnóstico e seus respectivos Scores.
- **Tenant Isolation Enforcement**: Validar os tokens JWT emitidos no front com as Policies RLS já configuradas no banco de dados para garantir que a *Assessoria A* não consiga acessar diagnosticos de *Leads da Assessoria B*.

## Conclusão do Roadmap
Se os próximos passos seguirem a estrita aderência arquitetural (`Clean Architecture`) e a manutenção da qualidade do código (`Playwright + Pytest`), as transições entre Sprints devem ser excepcionalmente fáceis de plugar e plugar módulos (como a entrada e saída das chamadas do Claude via Interfaces/Ports), reduzindo radicalmente a dívida técnica natural de um projeto jovem.
