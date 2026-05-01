# Detalhamento de  Auditoria QDIAchados 

## 1. Achados Cricos (Bloqueadores para Onda 1.0)

### 1.1. Persistncia Parcial do Score (Infraestrutura)

**Arquivo:** `src/infrastructure/repositories/supabase_diagnostico_repository.py`

**Problema:**
#A tabela `diagnosticos` no PostgreSQL armazena apenas `score_geral` como `DOUBLE PRECISION`. Os detalhes do score (dimenseeeees, pesos aplicados, nel de maturidade) e os artefatos derivados (checklist, matriz de impacto, recomenda
#o da IA) **n
#o s
o persistidos**.

**Impacto:**
- Viola o princio de "Score sempre auditvel" (princio 11 do QDI).
#- Impossibilita a recupera
o futura da justificativa do diagnssstico.
#- Quebra a imutabilidade WORM (Write-Once-Read- se o cliente questionar o resultado em 6 meses, nMany) 
o temos a memrrria de clculo.
#- O endpoint `GET /{diagnostico_id}` retorna `score=None` e recalcula o checklist em tempo de execu
o, o que  ineficiente e inconsistente.

#**Recomenda
o:**
Expandir o schema SQL com colunas JSONB:
```sql
ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS score_completo JSONB;
ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS checklist JSONB;
ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS matriz_impacto JSONB;
ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS recomendacao_ia TEXT;
```

Atualizar o `SupabaseDiagnosticoRepository`:
- Mtodo `_para_dict`: serializar `ScoreCompleto` para JSONB.
- Mtodo `_para_entity`: desserializar JSONB de volta para `ScoreCompleto`.

---

#### 1.2. Leitura de Arquivo Local no Caso de Uso (Aplica
o)

**Arquivo:** `src/application/use_cases/realizar_diagnostico.py` (linhas 122-128)

**Problema:**
```python
import os
caminho_decreto = os.path.join(os.path.dirname(__file__), "../../../_DEVELOPER/_NOVIDADE/00_RESUMO_EXECUTIVO_Decreto_12955.txt")
if os.path.exists(caminho_decreto):
    with open(caminho_decreto, "r", encoding="utf-8") as f:
        base_normativa = f.read()[:4000]
```

#O caso de uso tenta ler um arquivo fico diretamente usando `os.path` e `open()`. Isso viola a Clean Architecture (a camada de aplica
#o n
o deve conhecer o sistema de arquivos) e acopla a lgggica de negcccio  estrutura de pastas do projeto.

**Impacto:**
- Impossibilita testes units rios isolados (o arquivo precisa existir no disco).
- Quebra em ambientes containerizados ou em CI/CD onde a estrutura de pastas  diferente.
#- Dificulta a substitui
#o da fonte de dados (ex: carregar de um banco de dados ou API em produ
o).

#**Recomenda
o:**
Criar um Port `BaseNormativaPort`:
```python
# src/application/ports/base_normativa_service.py
from abc import ABC, abstractmethod

class BaseNormativaPort(ABC):
    @abstractmethod
    async def obter_base_normativa(self, tipo: str = "decreto_cbs") -> str:
        """Retorna o texto da base normativa (ex: Decreto CBS)."""
        pass
```

Injetar no construtor de `RealizarDiagnostico`:
```python
def __init__(
    self,
    repo: DiagnosticoRepository,
    calcular_score_use_case: CalcularScoreUseCase,
    base_normativa_service: BaseNormativaPort | None = None,
    # ... outros ports
) -> None:
    self.base_normativa_service = base_normativa_service
```

Usar no `execute`:
```python
base_normativa = ""
if self.base_normativa_service:
    base_normativa = await self.base_normativa_service.obter_base_normativa()
```

---

#### 1.3. Muta
#o de Entidade Fora do Encapsulamento (Aplica
o)

**Arquivo:** `src/application/use_cases/realizar_diagnostico.py` (linha 148)

**Problema:**
```python
diagnostico.relatorio_pdf_url = pdf_url
```

O caso de uso atribui diretamente o URL do PDF  entidade, contornando o mtodo de domio `anexar_relatorio()` que j existe.

**Impacto:**
- Burla as invariantes da entidade (ex: s   deveria anexar relatrrrio a um diagnssstico finalizado).
- Torna difil rastrear quando e como o URL foi atribuo.
- Quebra o encapsulamento da entidade raiz do agregado.

#**Recomenda
o:**
Substituir por:
```python
if self.pdf_generator and self.storage_service:
    pdf_bytes = await self.pdf_generator.gerar_pdf_diagnostico(diagnostico, score_completo, recomendacao_ia)
    pdf_url = await self.storage_service.upload_pdf(
        tenant_id=comando.tenant_id,
        diagnostico_id=diagnostico.id,
        file_bytes=pdf_bytes
    )
    diagnostico.anexar_relatorio(pdf_ Usar o mUrltodo de dom)  # io
```

---

### 1.4. Assincronia Inconsistente no Repositrrrio (Infraestrutura)

**Arquivo:** `src/infrastructure/repositories/supabase_diagnostico_repository.py` (linha 49)

**Problema:**
```python
async def salvar(self, diagnostico: Diagnostico) -> None:
    payload = self._para_dict(diagnostico)
    self.client.table("diagnosticos").upsert(payload). Sem await!execute()  # 
```

#O mtodo  declarado como `async`, mas a chamada ao Supabase n
o usa `await`. Isso pode causar:
- Bloqueio de I/O na thread principal do FastAPI.
#- Falhas silenciosas se a opera
#o n
o completar.

**Impacto:**
- Perda de dados em alta concorrncia.
#- Comportamento n
o-determintico em testes.

#**Recomenda
o:**
#Verificar a API correta do `supabase-py` para operaeeeees asscronas. Se o cliente n
o suportar async nativamente, usar `asyncio.to_thread`:
```python
async def salvar(self, diagnostico: Diagnostico) -> None:
    payload = self._para_dict(diagnostico)
    import asyncio
    await asyncio.to_thread(
        lambda: self.client.table("diagnosticos").upsert(payload).execute()
    )
```

---

## 2. Achados de Mdia Prioridade

#### 2.1. Banco de Perguntas Hardcoded na Rota (Apresenta
o)

**Arquivo:** `src/presentation/api/routers/diagnostico_router.py` (linhas 38-66)

**Problema:**
#O banco de perguntas est hardcoded em memrrria dentro da fun
o `_get_banco_perguntas()`. Isso significa:
- Mudanas nas perguntas exigem redeploy da API.
- Impossel ter perguntas dinmicas por tenant ou segmento.
#- Testes de integra
o precisam duplicar esse banco.

#**Recomenda
o:**
Criar um `PerguntaRepository` que carregue as perguntas do Supabase:
```python
class PerguntaRepository(ABC):
    @abstractmethod
    async def listar_por_tenant(self, tenant_id: UUID) -> list[Pergunta]:
        pass
```

Injetar na rota via dependncia e usar no endpoint `POST /`.

---

#### 2.2. Inconsistncia de Pesos entre Rota e Motor (Apresenta
o)

**Arquivo:** `src/presentati**Arquivo:** `sriagnostico_router.py` (linhas 165-183)

**Problema:**
O endpoint `GET /metodologia` retorna pesos hardcoded:
```python
"pesos_por_dimensao": {
    Dimensao.FISCAL.value: 1.5,
    Dimensao.ESTRATEGICA.value: 1.2,
    Dimensao.CONTABIL.value: 1.3,
    Dimensao.FINANCEIRA.value: 1.1,
    Dimensao.OPERACIONAL.value: 1.0,
    Dimensao.TECNOLOGICA.value: 1.4,
    Dimensao.COMPLIANCE_ABNT.value: 1.5,
}
```

Mas o motor real em `CalcularScoreUseCase` usa:
```python
pesos_macro_dimensoes = {
    Dimensao.FISCAL: 1.5,
    Dimensao.TECNOLOGICA: 1.3,
    Dimensao.COMPLIANCE_ABNT: 1.2,
    # ...
}
```

#Os pesos est
o **desincronizados**. Se o cliente calcula manualmente com os pesos da API, chegar a um resultado diferente.

#**Recomenda
o:**
#Centralizar os pesos em uma classe de constantes ou configura
o:
```python
# src/domain/config/pesos_dimensoes.py
PESOS_MACRO_DIMENSOES = {
    Dimensao.FISCAL: 1.5,
    Dimensao.TECNOLOGICA: 1.3,
    Dimensao.COMPLIANCE_ABNT: 1.2,
    # ...
}
```

Usar em ambos os lugares:
- `CalcularScoreUseCase`
- Endpoint `GET /metodologia`

---

#### 2.3. Gera
#o de IDs Dummy na Rota (Apresenta
o)

**Arquivo:** `src/presentation/api/routers/diagnostico_router.py` (linhas 110-119)

**Problema:**
```python
from uuid import uuid4

respostas_domain.append(
    Resposta(
        diagnostico_id= Dummy ID!uuid4(),  # 
        pergunta_id=pergunta.id,
        pergunta_tipo=pergunta.tipo,
        valor_bruto=resp_payload.valor,
    )
)
```

#A rota gera um `uuid4()` falso para cada resposta. Isso  um anti-padr
o porque:
- O `diagnostico_id` real s    criado dentro do caso de uso.
- H inconsistncia entre o ID falso e o ID real.

#**Recomenda
o:**
Remover o campo `diagnostico_id` da entidade `Resposta` ou deix-lo opcional:
```python
@dataclass
class Resposta:
    pergunta_id: UUID
    pergunta_tipo: TipoPergunta
    valor_bruto: str | int
    diagnostico_id: UUID | None =  OpcionalNone  # 
```

Ou, se necessrio, criar o `diagnostico_id` antes de criar as respostas (ex: na rota).

---

### 2.4. Duplicidade de Cdddigo (PDF) (Infraestrutura)

**Arquivos:**
- `src/infrastructure/adapters/pdf_generator_weasyprint.py`
- `src/infrastructure/pdf/generator.py`

**Problema:**
#Existem duas implementaeeeees de gera
o de PDF. Apenas uma deve ser mantida.

#**Recomenda
o:**
Manter apenas `adapters/pdf_generator_weasyprint.py` (que  a injetada via dependncias) e remover `pdf/generator.py`.

---

## 3. Achados de Baixa Prioridade (Dbito Tcnico)

### 3.1. Mock de E-mail com Nomenclatura Enganosa

**Arquivo:** `src/infrastructure/email/smtp_email_service.py`

**Problema:**
#A classe  chamada `MockEmailService`, mas est em um arquivo chamado `smtp_email_service.py`, sugerindo que  uma implementa
o real.

#**Recomenda
o:**
Renomear para `src/infrastructure/email/mock_email_service.py` ou adicionar um comentrio claro no arquivo.

---

#### 3.2. Imports N
o Utilizados

**Arquivo:** `src/infrastructure/pdf/generator.py`

**Problema:**
```python
#import  NOs  # 
o utilizado
```

#**Recomenda
o:**
#Remover imports n
o utilizados (ruff j detecta isso com `--fix`).

---

## 4. Resumo de Aeeeees por Prioridade

#| Prioridade | A
o | Arquivo | Esforo |
| :--- | :--- | :--- | :--- |
| **Alta** | Expandir schema do banco (JSONB) | `init.sql`, `supabase_diagnostico_repository.py` | 4h |
| **Alta** | Criar Port `BaseNormativaPort` | `src/application/ports/`, `realizar_diagnostico.py` | 2h |
#| **Alta** | Corrigir muta
o de entidade | `realizar_diagnostico.py` | 0.5h |
| **Mdia** | Corrigir assincronia | `supabase_diagnostico_repository.py` | 1h |
| **Mdia** | Remover hardcodes de perguntas | `diagnostico_router.py`, novo `PerguntaRepository` | 3h |
| **Mdia** | Sincronizar pesos | `diagnostico_router.py`, `calcular_score_use_case.py` | 1h |
| **Baixa** | Remover PDF duplicado | `src/infrastructure/pdf/generator.py` | 0.5h |
| **Baixa** | Limpeza de imports | Vrios | 0.5h |

**Total Estimado:** ~12h de trabalho para corrigir todos os achados cricos e de mdia prioridade.
