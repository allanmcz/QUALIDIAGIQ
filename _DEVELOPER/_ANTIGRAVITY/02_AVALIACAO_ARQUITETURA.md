# 02 - Avaliação da Arquitetura (QualiDiagIQ)

Esta avaliação foca nas escolhas de design arquitetural e sua capacidade de escalar as regras de negócio complexas do QualiDiagIQ sem incorrer em um *Big Ball of Mud*.

## 1. Backend: Clean Architecture & Domain-Driven Design (DDD)

A estrutura de diretórios adotada no backend (`src/domain`, `src/application`, `src/infrastructure`, `src/presentation`) é uma implementação canônica e excepcionalmente bem-feita da Clean Architecture.

### Pontos Fortes Notáveis:
- **Agregados e Entidades Limpas**: As classes no pacote de Domínio (ex: `Diagnostico`, `EmpresaInfo`) não possuem nenhuma menção ao framework web (`FastAPI`) ou ORM (`SQLAlchemy`/`Supabase`). Elas são puro Python (com `dataclasses`), fáceis de testar em milissegundos.
- **Inversão de Dependência (Ports and Adapters)**: No `RealizarDiagnostico` (Use Case), o sistema depende de `PdfGeneratorPort` e `StorageServicePort`. Ele não "conhece" o WeasyPrint nem o Supabase. Isso foi crucial para nos permitir adicionar Mocks na camada de Infraestrutura *sem tocar em nenhuma linha* de código da regra de negócio.
- **Data Transfer Objects (DTOs)**: A camada de `Presentation` utiliza schemas robustos do `Pydantic` v2, blindando a camada de aplicação de dados mal formatados ou perigosos, lidando nativamente com coerção de tipos e validação estrita (ex: regex para o CNAE).

### Oportunidades de Melhoria (Gaps):
- **Event Driven Architecture**: Hoje o Use Case executa de forma síncrona o salvamento, a geração do PDF e o envio de E-mail. No futuro, para evitar gargalos, eventos de domínio (ex: `DiagnosticoFinalizadoEvent`) poderiam ser despachados para workers assíncronos (ex: Celery ou BackgroundTasks do FastAPI) para processar o PDF sem segurar o fluxo HTTP do usuário.
- **Gerenciamento de Instâncias (Singleton/Factory)**: Atualmente, `dependencies.py` é responsável pela injeção. Com o aumento de Adapters, considerar o uso de uma biblioteca de Injeção de Dependência mais completa (como o `dependency-injector` do Python) pode ser mais escalável.

## 2. Frontend: Next.js (App Router)

O projeto de interface foi desenhado seguindo práticas modernas.

### Pontos Fortes Notáveis:
- **Zod + React Hook Form**: A escolha dessa dupla provou-se excepcional no `WizardForm`. O controle explícito sobre o ciclo de vida da validação via `trigger(camposEspecificos)` permitiu um Wizard real de múltiplas etapas dentro do mesmo componente `form`, mantendo o estado perfeitamente coeso.
- **Componentização com Shadcn**: Os componentes base isolados (`Input`, `Card`, `Button`, `Progress`) em uma pasta `components/ui` protegem as páginas complexas do excesso de utilitários Tailwind (HTML poluído), criando um padrão visual (Design System) elegante e fácil de refatorar.

### Oportunidades de Melhoria (Gaps):
- **Separação Server/Client**: O `WizardForm` inteiro é um arquivo com `"use client"`. Como este componente lida com uma UI pesada, isso é esperado, mas as lógicas de API Client (`lib/api/diagnostico.ts`) não se beneficiam de Actions ou cache server-side. Para um SaaS de SaaS (Lead Magnet público), pode ser favorável aproveitar Next.js **Server Actions** em vez de requisições Fetch normais no client para melhorar SEO, Segurança (chaves ocultas) e tempo de resposta.
- **Context API vs Local State**: Atualmente os dados ficam no estado local do `react-hook-form`. Se novas páginas dependessem desses mesmos dados, valeria externalizar o `formState` em um `Zustand` ou React Context. Como o fluxo é curto (apenas 3 steps contíguos no mesmo componente), a solução atual é perfeitamente adequada (YAGNI - *You Aren't Gonna Need It*).

## Conclusão Arquitetural
A arquitetura do projeto possui qualidade de padrão "Enterprise". Está muito acima da média de protótipos de startups, focando claramente na estabilidade exigida para o domínio tributário-fiscal. As separações garantem que a futura implementação de LLMs (RAG) não prejudicará o core determinístico do sistema.
