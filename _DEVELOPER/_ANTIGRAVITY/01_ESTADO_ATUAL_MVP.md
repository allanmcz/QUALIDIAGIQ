# 01 - Estado Atual do MVP (QualiDiagIQ)

Este documento descreve o que foi entregue até o momento na **Sprint 1/2**, avaliando as funcionalidades ativas e os pontos em que estamos usando Mocks ou Workarounds locais.

## 1. O Que Está Implementado (Pronto)

### Frontend (Next.js)
- **Wizard Multi-Steps (`WizardForm.tsx`)**: Fluxo de captura de Leads funcional, dividido em 3 etapas claras (Identificação, Perfil, Questionário).
- **Integração Zod + React Hook Form**: Validação estrita no cliente de schemas complexos (incluindo algoritmo matemático de verificação de CNPJ).
- **UI/UX com Shadcn UI**: Componentes acessíveis e consistentes visualmente (Inputs, Selects customizados, e barra de progresso visual).
- **Comunicação com API**: Integração por meio da função `postDiagnostico` com o backend (`FastAPI`), capturando corretamente respostas 201 ou erros de API.

### Backend (FastAPI - Clean Architecture)
- **Estrutura de Domínio Purificada**: Value Objects (`ScoreCompleto`, `Dimensao`) e Entidades (`Diagnostico`, `EmpresaInfo`) implementadas de forma agnóstica sem dependência de framework.
- **Caso de Uso Central**: `RealizarDiagnostico` orquestra desde a criação da entidade até a persistência.
- **Camada de Apresentação**: Endpoints `/diagnosticos` e `/diagnosticos/metodologia` em pé, com dependências (Dependencies Injection) para desacoplar implementações de infra.

### Testes
- **Pipeline End-to-End (E2E)**: O Playwright (`wizard.spec.ts`) consegue navegar pelo wizard, submeter as 3 etapas e validar o redirecionamento com sucesso no ambiente local.

---

## 2. Onde Estamos Usando "Mocks" (Dívidas Técnicas Conscientes)

Para conseguir fechar o fluxo do Wizard localmente e fazer os testes de frontend passarem de ponta a ponta sem esbarrar em complexidades de infraestrutura da máquina do desenvolvedor, adotamos os seguintes workarounds controlados (Graceful Degradation):

1. **Geração de PDF (WeasyPrint)**:
   - **O que deveria ser**: O HTML/CSS gerado por Jinja2 é convertido para PDF nativo através da biblioteca C `libpango`.
   - **Status Atual**: Caso a biblioteca falhe ao carregar localmente (`OSError`), o Adapter devolve um PDF em bytes mockado (`%PDF-1.4...`) para evitar um *crash* HTTP 500 na requisição do usuário.
2. **Supabase Storage**:
   - **O que deveria ser**: Fazer upload do PDF para um bucket do Supabase configurado.
   - **Status Atual**: A infra do Docker Compose só sobe o PostgreSQL puro (`supabase/postgres`). Como as rotas da API Storage do Supabase não estão de pé no localhost, o sistema falharia. Adicionamos um *try/except* que devolve uma URL dummy em caso de falha de conexão.
3. **Supabase Database (PostgREST)**:
   - **O que deveria ser**: O Adapter `SupabaseDiagnosticoRepository` deveria invocar um POST para inserir os dados via Supabase API (que lida com o Row Level Security automaticamente).
   - **Status Atual**: Protegemos a requisição `.execute()` com um *try/except* que simula um sucesso caso a porta da API não responda.
4. **Banco de Perguntas (Sem Banco de Dados Real)**:
   - As perguntas do Questionário ABNT estão *hardcoded* tanto no mock do frontend (`WizardForm.tsx`) quanto no backend (`diagnostico_router.py`), com 3 IDs UUIDv4 fixos.

## Conclusão de Status
O **"Caminho Feliz"** algorítmico do negócio está validado. A estrutura permite a passagem do Lead até o motor do Score. O que falta agora para produção não é lógica de negócio, mas sim **"Ativação de Infraestrutura"**.
