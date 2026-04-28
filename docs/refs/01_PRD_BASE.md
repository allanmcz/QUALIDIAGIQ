# Recomendações para o PRD do QualiDiagIQ

> **Documento de fechamento do Gap Analysis** — input pronto para redigir o PRD oficial do QDI
> **Documentos antecedentes:** `gap_analysis_oportunidades.md` + `matriz_decisao_features_qdi.md`
> **Documento próximo:** PRD oficial em `02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/DOCS/`

---

## 1. Resumo Executivo (3 frases)

O **QualiDiagIQ (QDI)** é o módulo de **diagnóstico tributário automatizado** do ecossistema Tributiq, construído como **lead magnet self-service** para a Reforma Tributária do Consumo. Em **5–15 minutos**, gera um relatório executivo + dashboard interativo com **score de prontidão 0-100** em 7 dimensões, ancoragem em ABNT NBR 17301, simulação financeira CBS+IBS+IS e plano de ação personalizado por LLM. Diferencia-se dos 7 concorrentes analisados pela combinação de **profundidade quantitativa + IA/RAG + integração ERP nativa + aderência normativa**.

---

## 2. Visão de Produto

### 2.1. Proposta de Valor (Value Proposition Canvas)

**Para o cliente final (CFO / Contador / Dono de PME):**
> *"Descubra em 15 minutos onde sua empresa está vulnerável à Reforma Tributária e receba um plano de ação executável com simulação financeira real — sem precisar contratar consultoria primeiro."*

**Pillars de valor:**
1. **Velocidade**: 15 minutos vs. 4 meses de auditoria tradicional (Fiscoplan)
2. **Profundidade**: simulação numérica real CBS+IBS+IS vs. linguagem qualitativa dos concorrentes
3. **Credibilidade**: aderência ABNT NBR 17301 + ancoragem legal dispositivo a dispositivo
4. **Acessibilidade**: gratuito (versão básica) vs. ticket de consultoria de R$ 30k+
5. **Personalização**: plano de ação gerado por IA, calibrado por persona

### 2.2. Personas-Alvo

| Persona | Cargo | Necessidade primária | Critério de decisão |
|---------|-------|----------------------|---------------------|
| **CFO Pragmática** | CFO de empresa média (R$ 50M–R$ 500M) | Quantificar exposição financeira da Reforma | Score relativo ao setor + simulação fluxo de caixa |
| **Contador Externo** | Sócio de escritório contábil | Diagnosticar carteira de clientes e cross-sell | White-label + relatório por cliente |
| **Dono de PME** | Empresário (R$ 5M–R$ 50M) | Entender se a Reforma vai "machucar" sua empresa | Linguagem simples + plano em 90 dias |
| **Diretor de TI** | CIO / Diretor de TI | Avaliar prontidão do ERP atual | Avaliação técnica + integração nativa |

---

## 3. Decisões Arquiteturais Pré-Definidas

Já validadas em ADRs anteriores e memória do projeto:

| ADR | Decisão | Impacto no QDI |
|-----|---------|----------------|
| **ADR-004** | Monorepo único `014-SAAS_REFORMA` | Código do QDI vai para `02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/SRC/` |
| **ADR-005** | Naming `QualiDiagIQ` (sigla QDI) | Branding consistente; codename interno preservado |
| **ADR-006** | ACL para APIs governamentais | QDI consome adapters em `_shared/infrastructure/gov_apis/` |
| **ADR-008** | Dual-track QDI + QMI (70/30) | QDI roda em paralelo com QMI; rituais de integração |

### Stack confirmada
- **Backend:** Python 3.12 + FastAPI 0.115+ + Pydantic v2
- **Frontend:** Next.js 14 (App Router) + React + Tailwind + shadcn/ui
- **DB:** Supabase (PostgreSQL 16 + RLS multi-tenant + pgvector)
- **IA:** Anthropic Claude / OpenAI + LangChain/LangGraph + RAG via pgvector
- **PDF:** WeasyPrint
- **Container:** Docker / OrbStack (dev M2 Max)
- **Test:** pytest + Playwright
- **CI:** GitHub Actions

---

## 4. Estrutura Recomendada do PRD

Recomendo redigir o PRD em **12 seções** (modelo padronizado para todos os 6 módulos Quali*IQ):

```
PRD_QDI.md
├── 1. Sumário Executivo (1 página)
├── 2. Problema e Oportunidade
│   ├── 2.1. Dor do cliente (com dados PwC)
│   ├── 2.2. Por que agora (janela 18-24 meses)
│   └── 2.3. Por que QDI (5 vetores de diferenciação)
├── 3. Personas e Jornadas
│   ├── 3.1. 4 personas detalhadas
│   ├── 3.2. Jornada do usuário (mapa fluxograma)
│   └── 3.3. Casos de uso priorizados (top 5)
├── 4. Proposta de Valor
│   ├── 4.1. Value Proposition Canvas
│   ├── 4.2. Pillars de diferenciação (5 vetores)
│   └── 4.3. Posicionamento vs. concorrentes
├── 5. Funcionalidades (MoSCoW)
│   ├── 5.1. MUST (12 features MVP)
│   ├── 5.2. SHOULD (11 features Beta)
│   ├── 5.3. COULD (10 features GA)
│   └── 5.4. WON'T (5 itens fora de escopo)
├── 6. Modelo de Domínio
│   ├── 6.1. Entidades principais
│   ├── 6.2. Value Objects
│   ├── 6.3. Agregados
│   └── 6.4. Eventos de domínio
├── 7. Arquitetura
│   ├── 7.1. Visão de macro arquitetura (Mermaid)
│   ├── 7.2. Clean Architecture (4 camadas)
│   ├── 7.3. Stack técnica
│   └── 7.4. Integrações externas
├── 8. Modelo de Dados
│   ├── 8.1. Schema PostgreSQL (Supabase)
│   ├── 8.2. RLS policies multi-tenant
│   └── 8.3. Indexação (B-tree + pgvector)
├── 9. UX/UI
│   ├── 9.1. Wireframes principais (10-15 telas)
│   ├── 9.2. Fluxo de telas
│   └── 9.3. Design tokens
├── 10. Métricas de Sucesso
│   ├── 10.1. Métricas de produto (NSM, North Star)
│   ├── 10.2. Métricas de negócio (CAC, LTV, conversão funil)
│   └── 10.3. Métricas técnicas (latência, uptime, error rate)
├── 11. Roadmap e Cronograma
│   ├── 11.1. MVP (90 dias)
│   ├── 11.2. Beta (75 dias)
│   ├── 11.3. GA (105 dias)
│   └── 11.4. Marcos e dependências
└── 12. Riscos e Mitigações
```

---

## 5. Modelo de Domínio Proposto (Camada Domain — Clean Architecture)

### 5.1. Entidades Principais

```python
# src/domain/entities/diagnostico.py
class Diagnostico:
    id: UUID
    tenant_id: UUID
    empresa: EmpresaInfo
    respondente: Respondente
    questionario: Questionario
    score: ScoreCompleto
    recomendacoes: list[Recomendacao]
    relatorio_pdf_url: URL | None
    criado_em: datetime
    finalizado_em: datetime | None

class EmpresaInfo:
    cnpj: CNPJ
    razao_social: str
    porte: PorteEmpresa  # SIMPLES_NACIONAL_MEI, ME, EPP, MEDIO, GRANDE
    regime: RegimeTributario  # SIMPLES, PRESUMIDO, REAL
    cnae_principal: CNAE
    uf: UF
    setor_macro: SetorMacro  # COMERCIO, INDUSTRIA, SERVICOS, AGRO

class Questionario:
    perguntas_respondidas: list[RespostaPergunta]
    progresso_percentual: float

class ScoreCompleto:
    score_geral: ScoreNumerico  # 0-100
    score_por_dimensao: dict[Dimensao, ScoreNumerico]
    score_relativo_setor: PercentilSetorial | None  # depende de N tenants
    nivel_maturidade: NivelMaturidade  # CRITICO, INICIAL, INTERMEDIARIO, AVANCADO
    aderencia_abnt_17301: AderenciaABNT
```

### 5.2. Value Objects

```python
# src/domain/value_objects/score.py
class ScoreNumerico:
    valor: float  # 0.0 - 100.0
    pesos_aplicados: dict[str, float]
    perguntas_consideradas: list[UUID]

class Dimensao(Enum):
    FISCAL = "fiscal"
    ESTRATEGICA = "estrategica"
    CONTABIL = "contabil"
    FINANCEIRA = "financeira"
    OPERACIONAL = "operacional"
    TECNOLOGICA = "tecnologica"
    COMPLIANCE_ABNT = "compliance_abnt_17301"  # 7ª dimensão exclusiva do QDI

class AderenciaABNT:
    score_pdca: dict[str, float]  # PLAN, DO, CHECK, ACT
    eixos_avaliados: dict[EixoABNT, EstadoMaturidade]
    gaps_identificados: list[GapABNT]
```

### 5.3. Casos de Uso (Application Layer)

```python
# src/application/use_cases/realizar_diagnostico.py
class RealizarDiagnostico:
    """
    Use case principal — orquestra:
    1. Captura de lead (CNPJ + e-mail + dados básicos)
    2. Geração de questionário adaptativo (baseado em segmento + regime + porte)
    3. Coleta de respostas (etapas)
    4. Cálculo de score (motor com pesos transparentes)
    5. Geração de recomendações (regras + LLM)
    6. Geração de PDF (WeasyPrint)
    7. Envio de relatório (e-mail + dashboard navegável)
    """

class GerarQuestionarioAdaptativo:
    """Filtra perguntas condicionais por contexto da empresa."""

class CalcularScore:
    """Aplica pesos transparentes, gera score 0-100 + por dimensão."""

class GerarRecomendacoesLLM:
    """RAG sobre Lexiq + LLM (Claude) para plano de ação personalizado."""

class CalcularBenchmarkSetorial:
    """Compara o tenant com pares anônimos (mesmo setor + porte + UF)."""

class GerarRelatorioPDF:
    """Renderiza dashboard como PDF executivo + técnico."""
```

---

## 6. Modelo de Dados (Schema PostgreSQL/Supabase)

```sql
-- Schema simplificado — apenas tabelas core

create schema if not exists qdi;

-- Multi-tenant
create table qdi.tenants (
  id uuid primary key default gen_random_uuid(),
  cnpj varchar(14) unique not null,
  razao_social text not null,
  porte text not null,
  regime text not null,
  cnae_principal text not null,
  uf text not null,
  setor_macro text not null,
  criado_em timestamptz default now()
);

-- Diagnósticos (1 tenant pode ter N diagnósticos ao longo do tempo)
create table qdi.diagnosticos (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references qdi.tenants(id) on delete cascade,
  respondente_email text not null,
  respondente_cargo text,
  status text not null check (status in ('em_andamento', 'finalizado', 'expirado')),
  score_geral numeric(5,2),
  score_por_dimensao jsonb,
  aderencia_abnt jsonb,
  recomendacoes jsonb,
  relatorio_pdf_url text,
  criado_em timestamptz default now(),
  finalizado_em timestamptz
);

-- Perguntas e respostas
create table qdi.perguntas (
  id uuid primary key default gen_random_uuid(),
  codigo text unique not null,
  texto text not null,
  dimensao text not null,
  peso numeric(5,3) not null,
  condicional jsonb, -- {segmento: ['comercio'], regime: ['lucro_real']}
  base_legal text, -- "LC 214/2025 art. 5º, § 2º"
  ativo boolean default true
);

create table qdi.respostas (
  id uuid primary key default gen_random_uuid(),
  diagnostico_id uuid references qdi.diagnosticos(id) on delete cascade,
  pergunta_id uuid references qdi.perguntas(id),
  resposta_valor jsonb not null, -- pode ser bool, escala 1-5, múltipla escolha
  pontos_obtidos numeric(5,2) not null,
  respondida_em timestamptz default now()
);

-- Versionamento normativo (Lexiq)
create table qdi.normas_versionadas (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  versao text not null,
  vigencia_inicio date not null,
  vigencia_fim date,
  conteudo_chunk text not null,
  embedding vector(1536), -- pgvector p/ RAG
  unique(nome, versao)
);

-- Multi-tenant via RLS
alter table qdi.tenants enable row level security;
alter table qdi.diagnosticos enable row level security;
alter table qdi.respostas enable row level security;

create policy tenant_isolation on qdi.tenants
  using (id = current_setting('app.tenant_id')::uuid);

create policy diagnostico_isolation on qdi.diagnosticos
  using (tenant_id = current_setting('app.tenant_id')::uuid);
```

---

## 7. Métricas de Sucesso

### 7.1. North Star Metric (NSM)

> **Diagnósticos completados por mês** (proxy de adoção real do produto)

### 7.2. Métricas de Produto (top 7)

| Métrica | Meta MVP | Meta GA |
|---------|----------|---------|
| Diagnósticos iniciados / mês | 50 | 1.000 |
| Taxa de conclusão (start → finalizado) | 40% | 60% |
| Tempo médio de preenchimento | <15 min | <10 min |
| NPS pós-relatório | 30+ | 60+ |
| Taxa de upgrade para módulos pagos (QFI/QMI) | 5% | 15% |
| Aderência média ABNT NBR 17301 do parque diagnosticado | mapeada | mapeada |
| % diagnósticos com simulação financeira concluída | 0% (MVP não tem) | 80% |

### 7.3. Métricas de Negócio

| Métrica | Meta MVP (90d) | Meta Beta (165d) | Meta GA (270d) |
|---------|----------------|-------------------|-----------------|
| Empresas únicas no banco | 100 | 500 | 2.000 |
| Conversão lead → cliente pagante | n/a | 3% | 8% |
| CAC (Custo de Aquisição de Cliente) | <R$ 50 | <R$ 100 | <R$ 200 |
| LTV (Lifetime Value) | n/a | R$ 800 | R$ 2.400 |

### 7.4. Métricas Técnicas

| Métrica | Meta |
|---------|------|
| Latência API (P95) | <500ms |
| Tempo de geração de PDF | <30s |
| Uptime | 99.5% (MVP) → 99.9% (GA) |
| Erro rate | <1% |
| Cobertura de testes (domain layer) | ≥85% |

---

## 8. Recomendações Específicas para o PRD

Cinco diretrizes editoriais para garantir qualidade do PRD:

### 8.1. Use dados reais quando possível
- Citar percentuais PwC (83% impacto, 70% diagnóstico ERP, 37% inicial) — **base de credibilidade gratuita**.
- Referenciar dispositivos legais exatos (LC 214/2025 art. X, NT 2025.002 cláusula Y) — vide `04_PESQUISA/NCM_CST/TABELAS_TRIBUTARIAS/03_legislacao/`.

### 8.2. Mantenha o cliente em primeiro plano
- Cada feature do MoSCoW deve ter um **"para quê" explícito** (Job to Be Done framework).
- Evitar features auto-justificadas pela engenharia.

### 8.3. Quantifique o que for quantificável
- Substituir "alto impacto" por "exposição estimada de R$ X em capital de giro adicional".
- Substituir "necessidade de adequação" por "score de aderência: 35/100 (percentil 18 do setor)".

### 8.4. Vincule decisões a ADRs
- Cada decisão arquitetural não-óbvia → criar ADR formal em `99_ARQUIVO/ADRS/`.
- Próxima ADR previsível: **ADR-009 — Modelo de Score do QDI (pesos, dimensões, normalização)**.

### 8.5. Documente em PT-BR técnico, com comentários inline
- Termos técnicos em inglês mantém termo + breve glosa na 1ª ocorrência: *"Multi-tenant (multi-inquilino — múltiplas empresas em uma mesma instância com isolamento RLS)"*.
- Tabelas e diagramas Mermaid sempre que houver decisão de trade-off.

---

## 9. Próximas Decisões Pendentes (após aprovação deste documento)

| # | Decisão | Quem decide | Prazo sugerido |
|---|---------|-------------|----------------|
| 1 | Aprovar MoSCoW (12 MUST, 11 SHOULD, 10 COULD, 5 WON'T) | Allan | Esta semana |
| 2 | Validar 7ª dimensão (Compliance ABNT) | Allan | Esta semana |
| 3 | Confirmar stack frontend (Next.js 14) | Allan | Esta semana |
| 4 | Confirmar modelo comercial (Freemium) | Allan | 2 semanas |
| 5 | Definir 5 cases de calibração de score | Allan + 3 contadores externos | 4 semanas |
| 6 | Redigir ADR-009 (Modelo de Score) | Allan + IA | 1 semana após aprovação MoSCoW |
| 7 | Redigir PRD oficial em `02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/DOCS/` | Allan + IA | 2 semanas |

---

## 10. Próximo Passo Sugerido

Recomendo abrir o **scaffold de desenvolvimento do QDI** em `05_PROPOSTA_018_QUALIDIAGIQ/018-QUALIDIAGIQ/` (próximo documento desta entrega — **F5**) e começar pelo Sprint 1 do MVP (M01 + M02 + M03). Em paralelo, redigir o **PRD oficial** usando este documento como input estruturado.

> **Lembrete arquitetural:** quando o MVP estiver validado e estável, mover o código de `05_PROPOSTA_018_QUALIDIAGIQ/018-QUALIDIAGIQ/` para `02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/SRC/` (conforme ADR-004). O scaffold em 018 é **prototipagem**, não a versão definitiva.
