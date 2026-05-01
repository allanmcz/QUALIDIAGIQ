# 05 — Referências Oficiais e Estudo Aprofundado

> Curadoria de fontes oficiais, manuais técnicos, notas técnicas e materiais de aprofundamento — consolidados em 26/04/2026.

---

## 🏛️ 1. Fontes Oficiais Primárias

### Receita Federal do Brasil (RFB)

| Recurso | URL | Tipo |
|---|---|---|
| Notícia oficial — lançamento Beta da Calculadora (18/07/2025) | https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2025/julho/receita-federal-libera-ferramenta-oficial-de-calculo-da-reforma-tributaria-sobre-o-consumo | Comunicado |
| Orientações da Reforma Tributária para 2026 | https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/acoes-e-programas/programas-e-atividades/reforma-consumo/orientacoes-2026 | Orientações |
| Manual de Serviços da RTC v1 (PDF) | https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/manuais/reforma-tributaria-do-consumo/manual-servicos-rtc.pdf | Manual técnico |
| Comunicado Beta Produção (dez/2025) | https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/manuais/reforma-tributaria-do-consumo/comunicado-sobre-o-ambiente-de-producao-beta-versao-1-dezembro25 | Comunicado |
| FAQ — Piloto da Reforma Tributária | https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/perguntas-frequentes/piloto-da-reforma-tributaria-do-consumo | FAQ |
| Aderir ao Piloto da CBS | https://www.gov.br/pt-br/servicos/aderir-ao-piloto-da-cbs | Serviço |

### Portais e ambientes

| Portal | URL | Status |
|---|---|---|
| **Tributação sobre Consumo (Beta)** | https://consumo.tributos.gov.br | Produção Beta |
| **Calculadora — interface Web** | https://consumo.tributos.gov.br/servico/calcular-tributos-consumo | Beta |
| **Swagger UI da API (este projeto)** | https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/swagger-ui/index.html | Beta |
| **OpenAPI JSON** | https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/api-docs | Beta |
| **Portal do Piloto RTC—CBS** | https://piloto-cbs.tributos.gov.br | Piloto |
| **Calculadora-Consumo (Piloto)** | https://piloto-cbs.tributos.gov.br/servico/calculadora-consumo/calculadora | Piloto |
| **Documentação da API (Piloto)** | https://piloto-cbs.tributos.gov.br/servico/calculadora-consumo/calculadora/documentacao | Piloto |
| **Componente Offline** | https://piloto-cbs.tributos.gov.br/servico/calculadora-consumo/calculadora/calculadora-offline | Download |

### Comitê Gestor do IBS (CGIBS)

| Recurso | URL |
|---|---|
| Site oficial CGIBS | https://www.cgibs.gov.br |
| CGIBS + RFB — Orientações 01/01/2026 | https://www.cgibs.gov.br/comite-gestor-do-ibs-e-receita-federal-divulgam-orientacoes-sobre-a-entrada-em-vigor-da-cbs-e-do-ibs-em-1-de-janeiro-de-2026 |

### Portal Nacional NF-e (com tabelas e Notas Técnicas RTC)

| Recurso | URL |
|---|---|
| Portal NF-e — RTC (Adequações) | https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=AklZnck3o6I%3D |
| NT 2025.002 v1.40 — IBS/CBS/IS (Tabelas cClassTrib + CST + cCredPres) | https://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=YmYqYBW8gGQ%3D |

### Serpro

| Recurso | URL |
|---|---|
| Serpro opera maior infra digital tributária (notícia 2026) | https://www.serpro.gov.br/menu/noticias/noticias-2026/serpro-opera-a-maior-infraestrutura-digital-tributaria-da-historia-do-brasil |

---

## ⚖️ 2. Legislação Aplicável

| Norma | Descrição | Link |
|---|---|---|
| **EC 132/2023** | Emenda Constitucional que cria a Reforma Tributária do Consumo | https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc132.htm |
| **LC 214/2025** | Lei Complementar que institui IBS, CBS, IS e dispõe sobre o Comitê Gestor | http://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm |
| **LC 218/2025** | Cria o Comitê Gestor do IBS (CGIBS) | http://www.planalto.gov.br/ccivil_03/leis/lcp/lcp218.htm |

### Artigos da LC 214/2025 mais relevantes para a API

| Artigo | Tema | Endpoint API relacionado |
|---|---|---|
| Arts. 12 e 13 | Base de Cálculo do CIBS | `/calculadora/base-calculo/cbs-ibs-mercadorias` |
| Art. 6º | BC NFS-e (locação imóveis, serviços médicos) | `/calculadora/nfse/base-calculo` (`vCalcDedRedIBSCBS`) |
| Art. 11 | Rateio IBS-Mun para transporte | `/calculadora/pedagio` |
| Art. 343 | Alíquotas-teste 2026 (CBS 0,9% / IBS 0,1%) | `/dados-abertos/aliquota-*` |
| Art. 384 | Fundos de Compensação (ICMS) | — (SISEN) |
| Art. 417 §2º | Bonificações no IS | `/calculadora/base-calculo/is-mercadorias` (`bonificacao`) |
| Art. 418 | Devolução de vendas | `/calculadora/base-calculo/is-mercadorias` (`devolucaoVendas`) |

---

## 📰 3. Notícias e Análises Técnicas (estudo aprofundado)

| Fonte | Tema | URL |
|---|---|---|
| Receita Federal — Lançamento Plataforma Digital | Lula sanciona Comitê Gestor + Plataforma Digital RTC (12/01/2026) | https://www.gov.br/planalto/pt-br/acompanhe-o-planalto/noticias/2026/01/lula-sanciona-projeto-de-lei-que-cria-comite-gestor-do-ibs-e-participa-do-lancamento-oficial-da-plataforma-digital-da-reforma-tributaria |
| Agência Gov | Portal RTC em fase de testes com 66 empresas | https://agenciagov.ebc.com.br/noticias/202506/reforma-tributaria-consumo-novo-portal-testes-com-66-empresas-1o-de-julho |
| Reforma Tributária 360 | Disponibilização do Manual da RTC (jan/2026) | https://reformatributaria360.com.br/noticias/receita-federal-disponibiliza-o-manual-da-rtc-o-que-muda-na-pratica-com-o-portal-a-calculadora-e-a-apuracao-assistida-da-cbs/ |
| Reforma Tributária 360 | Tabela cClassTrib (27/01/2026) | https://reformatributaria360.com.br/notas-tecnicas/tabela-cclasstrib-27-01-2026/ |
| Tecnospeed | NT 2025.002 IBS/CBS/IS — Grupos, Campos, Validações | https://blog.tecnospeed.com.br/nota-tecnica-reforma-tributaria-nfe-nfce/ |
| Tecnospeed | Tabela cClassTrib detalhada | https://blog.tecnospeed.com.br/tabela-cclasstrib/ |
| Sistema Fenacon | Portal NF-e publica novo Informe Técnico p/ IBS/CBS | https://fenacon.org.br/noticias/portal-da-nf-e-publica-novo-informe-tecnico-com-atualizacoes-para-ibs-e-cbs/ |
| IOB Notícias | Fase piloto CBS/IBS entra em vigor | https://noticias.iob.com.br/reforma-tributaria-cbs-ibs/ |
| CBIC | Receita Federal lança Calculadora de Tributos | https://cbic.org.br/receita-federal-lanca-calculadora-de-tributos-com-base-nas-novas-regras-da-reforma-tributaria/ |
| Fiscoplan | Quais são as Alíquotas-Teste para IBS e CBS? | https://www.grupofiscoplan.com.br/quais-sao-as-aliquotas-teste-para-ibs-e-cbs/ |
| Tax Group | Como funciona a alíquota teste IBS/CBS | https://www.taxgroup.com.br/intelligence/entenda-como-funciona-a-aliquota-teste-de-ibs-e-cbs/ |
| APET | Alíquota teste CBS/IBS em 2026 (artigo doutrinário) | https://apet.org.br/artigos/a-aliquota-teste-da-cbs-ibs-no-ano-de-2026/ |
| TOTVS — Espaço Legislação | Material consolidado Reforma Tributária | https://espacolegislacao.totvs.com/reforma-tributaria/ |
| SEFAZ-MG | Reforma Tributária do Consumo (visão estadual) | https://www.fazenda.mg.gov.br/reforma-tributaria/ |
| Legisweb | Manual de Serviços RTC | https://www.legisweb.com.br/noticia/?id=32313 |

### Documentação técnica de terceiros

| Fonte | Descrição | URL |
|---|---|---|
| NS Tecnologia (Documentação Calculadora) | Guia técnico de integração | https://documentacao.nstecnologia.com.br/docs/integracao-via-api-calculadora-da-reforma-tributaria/ |
| NS Tecnologia — Primeiros Passos | Onboarding API Calculadora | https://documentacao.nstecnologia.com.br/docs/integracao-via-api-calculadora-da-reforma-tributaria/primeiros-passos/ |
| SAP Community | Instalando a API da Calculadora no BTP | https://community.sap.com/t5/s%C3%A3o-paulo-blog-posts/instalando-a-api-da-calculadora-da-reforma-tribut%C3%A1ria-no-btp/ba-p/14310525 |

---

## 🛠️ 4. Recursos para Desenvolvedores

### Ferramentas que ajudam na integração

| Ferramenta | Uso | Link |
|---|---|---|
| `datamodel-code-generator` | Gera Pydantic v2 a partir do OpenAPI | https://github.com/koxudaxi/datamodel-code-generator |
| `openapi-typescript-codegen` | Gera client TypeScript | https://github.com/ferdikoomen/openapi-typescript-codegen |
| `httpx` (Python) | Client HTTP recomendado | https://www.python-httpx.org/ |
| `tenacity` (Python) | Retry com backoff | https://tenacity.readthedocs.io |
| `cockatiel` (TypeScript) | Circuit Breaker / Retry | https://github.com/connor4312/cockatiel |
| `zod` (TypeScript) | Validação runtime | https://zod.dev |

### Documentação de tecnologias do Tributiq

| Tecnologia | Doc oficial |
|---|---|
| **FastAPI** | https://fastapi.tiangolo.com |
| **Pydantic v2** | https://docs.pydantic.dev/latest/ |
| **Supabase** (Auth/DB/Edge Functions) | https://supabase.com/docs |
| **PostgreSQL RLS** | https://supabase.com/docs/guides/database/postgres/row-level-security |
| **LangChain** | https://python.langchain.com/docs |
| **LangGraph** | https://langchain-ai.github.io/langgraph/ |
| **MCP Protocol** | https://modelcontextprotocol.io |

---

## 🎓 5. Trilha de Estudo Sugerida (Allan)

**Tempo estimado: 8 blocos de 45 min (~6h) divididos em 3 dias.**

### Dia 1 — Fundamentos da Reforma (2 blocos)
1. Ler Orientações 2026 da RFB (link 1.RFB)
2. Ler EC 132/2023 e arts. 1º a 50 da LC 214/2025

### Dia 2 — Calculadora e Modelo de Dados (3 blocos)
3. Explorar Swagger UI ao vivo + chamar `consultarVersao` via curl
4. Ler [`docs/01-endpoints.md`](01-endpoints.md) e [`docs/02-schemas.md`](02-schemas.md) deste projeto
5. Reproduzir os 5 exemplos de [`examples/`](../examples/) via Postman/curl

### Dia 3 — Integração Tributiq (3 blocos)
6. Ler [`docs/04-integracao-tributiq.md`](04-integracao-tributiq.md)
7. Esboçar ADR-006 e revisar com a si mesmo (perfil arquiteto)
8. Implementar PoC do `CalculadoraRfbHttpClient` no QualiFiscaIQ

---

## 🧠 6. Glossário Rápido

| Sigla | Significado |
|---|---|
| **RTC** | Reforma Tributária do Consumo |
| **CBS** | Contribuição sobre Bens e Serviços (federal) |
| **IBS** | Imposto sobre Bens e Serviços (estadual + municipal) |
| **IS** | Imposto Seletivo (sobre bens nocivos) |
| **CIBS** | CBS + IBS (BC unificada) |
| **NFS-e** | Nota Fiscal de Serviço Eletrônica |
| **DF-e** | Documento Fiscal Eletrônico (gênero) |
| **NCM** | Nomenclatura Comum do Mercosul |
| **NBS** | Nomenclatura Brasileira de Serviços |
| **CST** | Código de Situação Tributária |
| **cClassTrib** | Código de Classificação Tributária |
| **ROC** | Recibo da Operação de Consumo |
| **CGIBS** | Comitê Gestor do IBS |
| **TaaS** | Tax-as-a-Service |
| **DeRE** | Declaração dos Regimes Específicos |
| **SISEN** | Sistema de Habilitação a Direitos de Compensação |
