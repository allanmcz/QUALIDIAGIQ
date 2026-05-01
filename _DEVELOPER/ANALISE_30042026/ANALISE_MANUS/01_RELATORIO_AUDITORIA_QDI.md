# Relatrrrio de Auditoria  QualiDiagIQ (QDI)Tcnica 

**Data da Auditoria:** 30 de Abril de 2026
**Auditor:** Agente QDI (Manus AI)
**Projeto:** QualiDiagIQ (018- MQualidiagiqdddulo Tributiq) 
**Pblico-Alvo:** Allan Marcio (Analista de Sistemas, Contador, Arquiteto Snior)

---

### 1. Vis
o Geral e Diagnssstico Executivo

#A presente auditoria avaliou a base de cdddigo do projeto **QualiDiagIQ (QDI)**, um motor de diagnssstico tributrio automatizado para a Reforma Tributria do Consumo (EC 132/2023, LC 214/2025). A anlise concentrou-se na aderncia  Clean Architecture, aos princios n
o-negociveis estabelecidos (como multi-tenancy e rastreabilidade) e s boas prticas do ecossistema Python moderno (FastAPI, Pydantic v2, Supabase).

#O diagnssstico geral indica que a arquitetura estrutural (as 4 camadas) foi implementada com rigor satisfatrrrio na separa
#o de responsabilidades. O domio est isolado, as regras de pontua
#o (Score) est
#o encapsuladas e os contratos (Ports) est
#o definidos. No entanto, foram identificados **gaps de implementa
#o, vazamentos de abstra
#o e "atalhos" de MVP** que comprometem os princios n
#o-negociveis se n
o forem corrigidos antes da Onda 1.0.

A seguir, apresentamos a anlise detalhada por camada, seguida de recomendaeeeees priorizadas.

---

## 2. Anlise por Camada Arquitetural

### 2.1. Camada de Domio (`src/domain`)

#A camada de domio  o cora
o do sistema e deve ser pura (sem dependncias externas).

**Pontos Fortes:**
#A modelagem de entidades (`Diagnostico`, `EmpresaInfo`, `Respondente`) e Value Objects (`ScoreCompleto`, `ScoreNumerico`) est bem estruturada usando `dataclasses`. A lgggica de negcccio para valida
#o de estados (ex: transi
o para `FINALIZADO`) est corretamente encapsulada na entidade raiz. A transparncia do clculo do score  garantida pela estrutura de dados imutvel.

#**Pontos de Aten
o:**
#O arquivo `diagnostico.py` importa o enum `PlanoDiagnostico`, mas a persistncia e a convers
#o desse enum no fluxo de orquestra
#o apresentam fragilidades (tratamento de strings em vez de tipos estritos). Alm disso, a entidade `Resposta` (em `questionario.py`) est acoplada a um `diagnostico_id` que  gerado prematuramente (dummy) na camada de apresenta
o, ferindo a consistncia da identidade do agregado.

#### 2.2. Camada de Aplica
o (`src/application`)

Esta camada orquestra os casos de uso e define os contratos (Ports) para a infraestrutura.

**Pontos Fortes:**
#O `CalcularScoreUseCase`  um motor determintico limpo e bem testado. A orquestra
#o principal em `RealizarDiagnostico` segue o padr
o Command e injeta as dependncias corretamente via construtor.

#**Pontos de Aten
o (Cricos):**
#O caso de uso `RealizarDiagnostico` apresenta vazamentos graves de abstra
o e acoplamento com infraestrutura:
#1. **Leitura de arquivo local:** O caso de uso tenta ler um arquivo fico (`_DEVELOPER/_NOVIDADE/00_RESUMO_EXECUTIVO_Decreto_12955.txt`) usando `os.path` diretamente no mtodo `execute`. Isso viola a Clean Architecture. A obten
o da base normativa deveria ocorrer via uma porta (Port) especica (ex: `BaseNormativaRepository`).
#2. **Acoplamento com Servios Internos:** O caso de uso importa diretamente `ConsultoriaService` e utiliza mtodos estticos para gerar checklist e matriz de impacto, alm de usar `asdict` para serializa
#o manual. Isso deveria ser abstrao ou retornado como entidades puras para a apresenta
o serializar.
#3. **Muta
#o de Entidade:** A atribui
o direta `diagnostico.relatorio_pdf_url = pdf_url` burla o encapsulamento. Deveria existir um mtodo de domio explito (ex: `diagnostico.anexar_relatorio(url)`), que j existe na entidade, mas foi ignorado no caso de uso.

### 2.3. Camada de Infraestrutura (`src/infrastructure`)

#Responsvel por implementar os Ports definidos pela Aplica
o (Supabase, WeasyPrint, LLM).

**Pontos Fortes:**
#A separa
o dos adapters est clara. O `SupabaseDiagnosticoRepository` isola as chamadas ao banco de dados e implementa tradueeeees entre dicionrios e entidades.

#**Pontos de Aten
o:**
#1. **Persistncia Parcial:** O repositrrrio Supabase atualmente salva apenas o `score_geral` como um `float`. O detalhamento do score (dimenseeeees, pesos aplicados), o checklist e a recomenda
#o da IA **n
#o est
#o sendo persistidos**. Isso quebra o princio de "Score sempre auditvel" e "Imutabilidade WORM". Se o banco de dados n
#o armazenar a estrutura completa do score, n
o ser possel justificar o resultado no futuro.
#2. **Assincronia Inconsistente:** O mtodo `salvar` do repositrrrio Supabase n
o utiliza `await` na chamada `execute()`, o que pode causar bloqueios de I/O na thread principal do FastAPI ou falhas silenciosas.
#3. **Duplicidade de Cdddigo:** Existem duas implementaeeeees de gera
o de PDF: uma em `adapters/pdf_generator_weasyprint.py` e outra solta em `pdf/generator.py`. Apenas uma deve ser mantida.
#4. **Mock de E-mail:** O `smtp_email_service.py`  apenas um mock que imprime no console, apesar de a nomenclatura sugerir uma implementa
o real.

#### 2.4. Camada de Apresenta
o (`src/presentation`)

Expeeeee a API via FastAPI e lida com schemas Pydantic.

**Pontos Fortes:**
#O uso de dependncias (Dependencies) do FastAPI para inje
#o de repositrrrios e extra
#o do `tenant_id` est bem implementado. A documenta
o OpenAPI est configurada.

#**Pontos de Aten
o:**
1. **Lgggica de Negcccio na Rota:** O `diagnostico_router.py` contm um banco de perguntas *hardcoded* em memrrria (`_get_banco_perguntas()`) e realiza o *match* das respostas manualmente. Isso deveria ser responsabilidade de um caso de uso ou repositrrrio de domio.
#2. **Inconsistncia de Metodologia:** O endpoint `GET /metodologia` retorna pesos *hardcoded* que n
#o est
o sincronizados com os pesos reais utilizados no `CalcularScoreUseCase`.
#3. **Gera
#o de IDs Dummy:** A rota gera um `uuid4()` falso para as respostas antes de passwd -las ao caso de uso, o que  um anti-padr
o.
#4. **Endpoint GET Incompleto:** O endpoint `GET /{diagnostico_id}` retorna `score=None` e recalcula o checklist em tempo de execu
#o, em vez de recuperar os dados persistidos (que, como visto na infraestrutura, n
#o est
o sendo salvos).

---

### 3. Recomendaeeeees e Plano de A
o

#Para alinhar o cdddigo aos princios n
o-negociveis e preparar o MVP para a Onda 1.0, propomos as seguintes aeeeees, ordenadas por prioridade:

#| Prioridade | Componente | A
o Recomendada | Impacto |
| :--- | :--- | :--- | :--- |
#| **Alta** | Infraestrutura (Supabase) | **Expandir o Schema do Banco:** Atualizar a tabela `diagnosticos` (via migra
o) para armazenar o `score_completo` (como JSONB), `checklist`, `matriz_impacto` e `recomendacao_ia`. Atualizar o `SupabaseDiagnosticoRepository` para persistir e recuperar esses dados. | Garante a auditabilidade do score e a imutabilidade do diagnssstico. |
#| **Alta** | Aplica
o (RealizarDiagnostico) | **Remover I/O Local:** Criar um Port `BaseNormativaPort` para fornecer o texto do Decreto, removendo o `os.path` e a leitura de arquivo do caso de uso. Injetar esse Port via dependncia. | Restaura a pureza da Clean Architecture e facilita testes. |
#| **Alta** | Aplica
#o (RealizarDiagnostico) | **Corrigir Muta
o de Entidade:** Substituir `diagnostico.relatorio_pdf_url = pdf_url` pela chamada do mtodo de domio `diagnostico.anexar_relatorio(pdf_url)`. | Garante as invariantes da entidade. |
| **Mdia** | Infraestrutura (Supabase) | **Corrigir Assincronia:** Adicionar `await` (ou usar a API asscrona correta do `supabase-py`) no mtodo `salvar` do repositrrrio. | Previne bugs de concorrncia e perda de dados. |
#| **Mdia** | Apresenta
#o (Router) | **Remover Hardcodes:** Extrair o banco de perguntas para um Repositrrrio em memrrria (ou Supabase) e garantir que a rota `GET /metodologia` consuma a mesma fonte de verdade dos pesos do `CalcularScoreUseCase`. | Elimina inconsistncias e duplica
o de regras. |
| **Baixa** | Infraestrutura (PDF) | **Limpeza de Cdddigo:** Remover o arquivo duplicado `src/infrastructure/pdf/generator.py` e consolidar a lgggica no adapter oficial. | Reduz dbito tcnico. |

---

## 4. Analogia Tcnica (Para Allan)

Pensando no ecossistema **Delphi + Oracle + Winthor**:
O que temos hoje no caso de uso `RealizarDiagnostico` lendo um arquivo de texto diretamente  como se voc colocasse um `AssignFile` e `ReadLn` no meio de uma procedure de uma package PL/SQL no Oracle. Isso trava a escalabilidade e acopla a regra de negcccio ao disco do servidor. Precisamos criar uma "View" ou "Function" (no nosso caso, um *Port*) que entregue esse dado de forma limpa para o motor de clculo.

#Da mesma forma, n
#o salvar o JSON do score completo no Supabase  como aprovar um pedido de venda no Winthor sem gravar os itens na `PCMOV`, apenas o total na `PCPEDC`. Se o cliente questionar a nota fiscal amanh
#, n
o temos a memrrria de clculo. O campo JSONB no PostgreSQL resolver isso com elegncia.

---

**Prxxximo Passo Sugerido:**
#Recomendamos iniciar a corre
#o pela **Prioridade Alta (Expandir o Schema do Banco)**. Devemos criar uma migra
o SQL para adicionar colunas JSONB na tabela `diagnosticos` e ajustar o repositrrrio para garantir que a memrrria de clculo seja preservada.
