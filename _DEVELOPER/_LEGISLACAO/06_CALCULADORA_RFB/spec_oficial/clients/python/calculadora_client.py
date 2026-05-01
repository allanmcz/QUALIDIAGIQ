"""
Cliente Python — Calculadora de Tributos do Consumo (Reforma Tributária)

Cliente HTTP enxuto baseado em httpx + Pydantic v2 + tenacity.
Pertence ao pacote `01_shared/calculadora_rfb` do monorepo Tributiq.

Princípios:
- Clean Architecture: este módulo é INFRAESTRUTURA. Não importe nada de domínio aqui.
- Tipagem forte (Pydantic v2)
- Resiliência (retry com backoff exponencial)
- Observabilidade (logging estruturado + hooks Prometheus)

Autor: Tributiq · Versão: 1.0 · 26/04/2026

Documentação oficial:
- Swagger UI: https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/swagger-ui/index.html
- OpenAPI:    https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/api-docs
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Exceções de domínio
# ═══════════════════════════════════════════════════════════════════
class CalculadoraError(Exception):
    """Erro retornado pela API da RFB no padrão RFC 7807 (ProblemDetail)."""

    def __init__(self, problem: dict[str, Any]) -> None:
        self.type: str | None = problem.get("type")
        self.title: str | None = problem.get("title")
        self.status: int | None = problem.get("status")
        self.detail: str | None = problem.get("detail")
        self.instance: str | None = problem.get("instance")
        self.properties: dict[str, Any] = problem.get("properties") or {}
        super().__init__(f"[{self.status}] {self.title}: {self.detail}")


class CalculadoraTimeout(CalculadoraError):
    """Timeout na chamada à API."""


# ═══════════════════════════════════════════════════════════════════
# DTOs Pydantic v2 — apenas os essenciais
# (gerar os 63 schemas via datamodel-code-generator em src/.../dto/generated.py)
# ═══════════════════════════════════════════════════════════════════
class TributacaoRegularInput(BaseModel):
    cst: str = Field(..., max_length=3, description="Código de Situação Tributária")
    cClassTrib: str = Field(..., max_length=6, description="Código de Classificação Tributária")


class ImpostoSeletivoInput(BaseModel):
    cst: str = Field(..., max_length=3)
    cClassTrib: str = Field(..., max_length=6)
    baseCalculo: Decimal
    impostoInformado: Decimal
    quantidade: Decimal | None = None
    unidade: str | None = None


class ItemOperacaoInput(BaseModel):
    numero: int
    cst: str = Field(..., max_length=3)
    cClassTrib: str = Field(..., max_length=6)
    ncm: str | None = None
    nbs: str | None = None
    baseCalculo: Decimal | None = None
    quantidade: Decimal | None = None
    unidade: str | None = None
    tributacaoRegular: TributacaoRegularInput | None = None
    impostoSeletivo: ImpostoSeletivoInput | None = None


class OperacaoInput(BaseModel):
    """Entrada do POST /calculadora/regime-geral"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Identificador do ROC (UUID/hash)")
    versao: str = Field(..., description="Versão do schema do ROC")
    municipio: int = Field(..., description="Código IBGE do município")
    itens: list[ItemOperacaoInput]
    dhFatoGerador: str | None = Field(
        None, description="Data e hora do fato gerador (ISO 8601 com offset)"
    )
    uf: str | None = Field(None, max_length=2)


class VersaoOutput(BaseModel):
    """Resposta de GET /dados-abertos/versao — usado como health check."""

    versaoApp: str
    versaoDb: str
    descricaoVersaoDb: str | None = None
    dataVersaoDb: str | None = None
    ambiente: str | None = None


class AliquotaDadosAbertosOutput(BaseModel):
    aliquotaReferencia: Decimal
    aliquotaPropria: Decimal
    formaAplicacao: Literal["SUBSTITUICAO", "ACRESCIMO", "DECRESCIMO"]


class UfDadosAbertosOutput(BaseModel):
    sigla: str
    nome: str
    codigo: int


class MunicipioDadosAbertosOutput(BaseModel):
    codigo: int
    nome: str


# ═══════════════════════════════════════════════════════════════════
# Settings (Pydantic Settings recomendado em produção)
# ═══════════════════════════════════════════════════════════════════
DEFAULT_BASE_URL = "https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api"
DEFAULT_TIMEOUT_S = 30.0
USER_AGENT = "Tributiq/1.0 (+https://tributiq.com.br)"


# ═══════════════════════════════════════════════════════════════════
# Cliente HTTP
# ═══════════════════════════════════════════════════════════════════
class CalculadoraClient:
    """Cliente síncrono para a API oficial da Calculadora RTC.

    Exemplo:
        >>> cli = CalculadoraClient()
        >>> versao = cli.consultar_versao()
        >>> print(versao.versaoApp, versao.ambiente)
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout_s: float = DEFAULT_TIMEOUT_S,
        verify: bool = True,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(timeout_s, connect=5.0),
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            verify=verify,
        )

    # --- ciclo de vida ---
    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "CalculadoraClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # --- núcleo HTTP com retry ---
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _request(
        self, method: str, path: str, *, params: dict | None = None, json: Any = None
    ) -> httpx.Response:
        try:
            r = self._client.request(method, path, params=params, json=json)
        except httpx.TimeoutException as e:
            raise CalculadoraTimeout(
                {"title": "Timeout", "status": 408, "detail": str(e)}
            ) from e

        if r.status_code >= 400:
            try:
                problem = r.json()
            except ValueError:
                problem = {"title": "Erro desconhecido", "status": r.status_code, "detail": r.text}
            raise CalculadoraError(problem)
        return r

    # ═════════════════════════════════════════════════════════════
    # Endpoints — Calculadora
    # ═════════════════════════════════════════════════════════════
    def calcular_regime_geral(self, operacao: OperacaoInput | dict) -> dict:
        """POST /calculadora/regime-geral — retorna o ROC (dict bruto)."""
        body = operacao.model_dump(exclude_none=True) if isinstance(operacao, BaseModel) else operacao
        r = self._request("POST", "/calculadora/regime-geral", json=body)
        return r.json()

    def validar_xml(
        self,
        xml_bytes: bytes,
        tipo: Literal["nfe", "nfce", "nfse", "cte", "cte-simplificado", "bpe", "bpe-tm", "nf3e"],
        subtipo: Literal["grupo", "nota"] = "nota",
    ) -> dict:
        """POST /calculadora/xml/validate"""
        r = self._client.post(
            "/calculadora/xml/validate",
            params={"tipo": tipo, "subtipo": subtipo},
            content=xml_bytes,
            headers={"Content-Type": "application/xml"},
        )
        if r.status_code >= 400:
            raise CalculadoraError(r.json())
        return r.json()

    def gerar_xml(
        self,
        roc: dict,
        tipo: Literal["nfe", "nfce", "nfse", "cte", "cte-simplificado", "bpe", "bpe-tm", "nf3e"],
    ) -> bytes:
        """POST /calculadora/xml/generate — retorna o XML do DF-e em bytes."""
        r = self._client.post(
            "/calculadora/xml/generate", params={"tipo": tipo}, json=roc
        )
        if r.status_code >= 400:
            raise CalculadoraError(r.json())
        return r.content

    # ═════════════════════════════════════════════════════════════
    # Endpoints — Base de Cálculo
    # ═════════════════════════════════════════════════════════════
    def calcular_bc_cibs(self, payload: dict) -> Decimal:
        """POST /calculadora/base-calculo/cbs-ibs-mercadorias — retorna apenas a BC."""
        r = self._request(
            "POST", "/calculadora/base-calculo/cbs-ibs-mercadorias", json=payload
        )
        return Decimal(str(r.json()["baseCalculo"]))

    def calcular_bc_is(self, payload: dict) -> Decimal:
        """POST /calculadora/base-calculo/is-mercadorias"""
        r = self._request(
            "POST", "/calculadora/base-calculo/is-mercadorias", json=payload
        )
        return Decimal(str(r.json()["baseCalculo"]))

    # ═════════════════════════════════════════════════════════════
    # Endpoints — NFS-e
    # ═════════════════════════════════════════════════════════════
    def calcular_bc_nfse(self, payload: dict) -> Decimal:
        """POST /calculadora/nfse/base-calculo"""
        r = self._request("POST", "/calculadora/nfse/base-calculo", json=payload)
        return Decimal(str(r.json()["baseCalculo"]))

    # ═════════════════════════════════════════════════════════════
    # Endpoints — Pedágio
    # ═════════════════════════════════════════════════════════════
    def calcular_pedagio(self, payload: dict) -> dict:
        """POST /calculadora/pedagio"""
        r = self._request("POST", "/calculadora/pedagio", json=payload)
        return r.json()

    # ═════════════════════════════════════════════════════════════
    # Endpoints — Dados Abertos
    # ═════════════════════════════════════════════════════════════
    def consultar_versao(self) -> VersaoOutput:
        """GET /calculadora/dados-abertos/versao — health check."""
        r = self._request("GET", "/calculadora/dados-abertos/versao")
        return VersaoOutput.model_validate(r.json())

    def consultar_ufs(self) -> list[UfDadosAbertosOutput]:
        """GET /calculadora/dados-abertos/ufs"""
        r = self._request("GET", "/calculadora/dados-abertos/ufs")
        return [UfDadosAbertosOutput.model_validate(x) for x in r.json()]

    def consultar_municipios(self, sigla_uf: str) -> list[MunicipioDadosAbertosOutput]:
        """GET /calculadora/dados-abertos/ufs/municipios"""
        r = self._request(
            "GET", "/calculadora/dados-abertos/ufs/municipios", params={"siglaUf": sigla_uf}
        )
        return [MunicipioDadosAbertosOutput.model_validate(x) for x in r.json()]

    def consultar_situacoes_tributarias_cbs_ibs(self, data_ref: date) -> list[dict]:
        """GET /calculadora/dados-abertos/situacoes-tributarias/cbs-ibs"""
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/situacoes-tributarias/cbs-ibs",
            params={"data": data_ref.isoformat()},
        )
        return r.json()

    def consultar_situacoes_tributarias_is(self, data_ref: date) -> list[dict]:
        """GET /calculadora/dados-abertos/situacoes-tributarias/imposto-seletivo"""
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/situacoes-tributarias/imposto-seletivo",
            params={"data": data_ref.isoformat()},
        )
        return r.json()

    def consultar_ncm(self, ncm: str, data_ref: date) -> dict:
        """GET /calculadora/dados-abertos/ncm"""
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/ncm",
            params={"ncm": ncm, "data": data_ref.isoformat()},
        )
        return r.json()

    def consultar_nbs(self, nbs: str, data_ref: date) -> dict:
        """GET /calculadora/dados-abertos/nbs"""
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/nbs",
            params={"nbs": nbs, "data": data_ref.isoformat()},
        )
        return r.json()

    def consultar_classificacoes_cbs_ibs(self, data_ref: date) -> list[dict]:
        """GET /calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs"""
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs",
            params={"data": data_ref.isoformat()},
        )
        return r.json()

    def consultar_classificacoes_is(self, data_ref: date) -> list[dict]:
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/classificacoes-tributarias/imposto-seletivo",
            params={"data": data_ref.isoformat()},
        )
        return r.json()

    def validar_cclasstrib_dfe(
        self, sigla_dfe: str, c_class_trib: str, data_ref: date
    ) -> dict:
        """GET /calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs/{sigla}/{cClassTrib}"""
        r = self._request(
            "GET",
            f"/calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs/{sigla_dfe}/{c_class_trib}",
            params={"data": data_ref.isoformat()},
        )
        return r.json()

    def consultar_aliquota_uniao(self, data_ref: date) -> AliquotaDadosAbertosOutput:
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/aliquota-uniao",
            params={"data": data_ref.isoformat()},
        )
        return AliquotaDadosAbertosOutput.model_validate(r.json())

    def consultar_aliquota_uf(
        self, codigo_uf: int, data_ref: date
    ) -> AliquotaDadosAbertosOutput:
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/aliquota-uf",
            params={"codigoUf": codigo_uf, "data": data_ref.isoformat()},
        )
        return AliquotaDadosAbertosOutput.model_validate(r.json())

    def consultar_aliquota_municipio(
        self, codigo_municipio: int, data_ref: date
    ) -> AliquotaDadosAbertosOutput:
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/aliquota-municipio",
            params={"codigoMunicipio": codigo_municipio, "data": data_ref.isoformat()},
        )
        return AliquotaDadosAbertosOutput.model_validate(r.json())

    def consultar_fundamentacoes_legais(self, data_ref: date) -> list[dict]:
        r = self._request(
            "GET",
            "/calculadora/dados-abertos/fundamentacoes-legais",
            params={"data": data_ref.isoformat()},
        )
        return r.json()


# ═══════════════════════════════════════════════════════════════════
# Demo / smoke test
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    with CalculadoraClient() as cli:
        # 1) Health check
        v = cli.consultar_versao()
        print(f"✓ API online — versão app={v.versaoApp}, db={v.versaoDb}, amb={v.ambiente}")

        # 2) Lista UFs
        ufs = cli.consultar_ufs()
        print(f"✓ {len(ufs)} UFs carregadas — primeira: {ufs[0].sigla} ({ufs[0].nome})")

        # 3) Alíquota da União hoje
        aliq = cli.consultar_aliquota_uniao(data_ref=date.today())
        print(
            f"✓ Alíquota CBS hoje: própria={aliq.aliquotaPropria}% "
            f"(forma={aliq.formaAplicacao}, ref={aliq.aliquotaReferencia}%)"
        )
