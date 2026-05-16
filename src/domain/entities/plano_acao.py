"""
Entidades do plano de ação (catálogo + item materializável).

Camada: Domain
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID  # noqa: TC003 — tipos de campo do dataclass (runtime + mypy)

from src.domain.value_objects.evidencia_lexiq import EvidenciaLexiq
from src.domain.value_objects.plano_acao import (
    CriticidadePlanoAcao,
    FasePdcaPlano,
    HorizontePlanoAcao,
    StatusExecucaoAcao,
)


@dataclass(frozen=True, slots=True)
class GapDetectado:
    """Lacuna sintética para o motor (ratio 0..1 — quanto menor, maior o gap)."""

    pergunta_codigo: str
    pergunta_id: UUID
    dimensao: str
    peso: float
    pontos_obtidos: float
    ratio: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.ratio <= 1.0:
            raise ValueError(f"ratio fora de [0,1]: {self.ratio}")
        if not 0.0 <= self.peso <= 10.0:
            raise ValueError(f"peso fora de [0,10]: {self.peso}")


@dataclass(slots=True)
class ItemAcao:
    """
    Item canónico do plano (espelho lógico de ``diagnostico_plano_acao`` + evidências).

    Campos mutáveis via consultor: ``prazo_meta``, ``status``, ``comentarios``, ``descricao_personalizada``.
    Demais campos são tratados como snapshot WORM na camada de aplicação/API.
    """

    id: UUID
    tenant_id: UUID
    diagnostico_id: UUID
    codigo: str
    titulo: str
    descricao: str
    dimensao: str
    fase_pdca: FasePdcaPlano
    horizonte: HorizontePlanoAcao
    criticidade: CriticidadePlanoAcao
    area_responsavel: str
    peso_calculado: float
    perguntas_origem: list[UUID]
    evidencias: tuple[EvidenciaLexiq, ...]
    prazo_meta: date | None = None
    status: StatusExecucaoAcao = StatusExecucaoAcao.PENDENTE
    upsell_tier: str | None = None
    mensagem_upsell: str | None = None
    descricao_personalizada: str | None = None
    comentarios: list[str] = field(default_factory=list)
    criado_em: datetime = field(default_factory=lambda: datetime.now(UTC))
    atualizado_em: datetime | None = None
    metodologia_versao: str = "v1.0.0"
    hash_sha256: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.peso_calculado <= 10.0:
            raise ValueError("peso_calculado deve estar em [0.0, 10.0]")
        if len(self.titulo) > 120:
            raise ValueError("titulo > 120 chars")
        if len(self.descricao) > 2000:
            raise ValueError("descricao > 2000 chars")
        if not self.evidencias:
            raise ValueError("ItemAcao requer ≥ 1 evidência Lexiq (curadoria ou RAG)")
        if self.prazo_meta is not None and self.prazo_meta <= self.criado_em.date():
            raise ValueError("prazo_meta deve ser estritamente posterior a criado_em (data)")
        if not self.hash_sha256:
            object.__setattr__(self, "hash_sha256", self._calcular_hash())

    def _calcular_hash(self) -> str:
        payload = (
            f"{self.codigo}|{self.titulo}|{self.descricao}|"
            f"{self.dimensao}|{self.fase_pdca.value}|{self.criticidade.value}|"
            f"{self.metodologia_versao}|"
            f"{','.join(e.chunk_id.hex for e in self.evidencias)}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
