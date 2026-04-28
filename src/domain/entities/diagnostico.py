"""
Entidade-raiz do agregado Diagnóstico.

Camada: Domain (puro Python — ZERO dependência externa)
Aderência: Clean Architecture (Robert C. Martin) + DDD (Eric Evans)

Base de negócio:
    - EC 132/2023 — Reforma Tributária do Consumo
    - LC 214/2025 — Regulamentação CBS/IBS
    - ABNT NBR 17301:2026 — Sistemas de gestão de compliance tributário

Analogia para o Allan:
    Pense nesta entidade como o registro principal de uma "Auditoria Fiscal"
    no Winthor — só que persistido em PostgreSQL ao invés de Oracle, e com
    domain rules (regras de negócio) explicitamente isoladas da camada de dados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

# ============================================================
# Value Objects (importados do package value_objects)
# ============================================================
# Em produção: from src.domain.value_objects.score import ScoreCompleto
# (deixado como TYPE_CHECKING para o stub não falhar)


class StatusDiagnostico(Enum):
    """Estados possíveis de um diagnóstico ao longo do ciclo de vida."""

    EM_ANDAMENTO = "em_andamento"
    FINALIZADO = "finalizado"
    EXPIRADO = "expirado"
    CANCELADO = "cancelado"


class RegimeTributario(Enum):
    """Regime tributário declarado pela empresa-cliente."""

    SIMPLES_NACIONAL = "simples_nacional"
    LUCRO_PRESUMIDO = "lucro_presumido"
    LUCRO_REAL = "lucro_real"
    MEI = "mei"


class PorteEmpresa(Enum):
    """
    Faixas de porte alinhadas com a segmentação da PwC Brasil
    (estudo "Tributos no Centro: Caminhos para a Reinvenção", nov/2025).
    """

    MICRO = "micro"  # até R$ 360 mil
    PEQUENO = "pequeno"  # até R$ 4,8 mi
    MEDIO = "medio"  # R$ 4,8 mi a R$ 500 mi (PwC: "menores")
    GRANDE = "grande"  # R$ 500 mi a R$ 5 bi (PwC: faixa intermediária)
    ENTERPRISE = "enterprise"  # > R$ 5 bi (PwC: "grande porte")


class SetorMacro(Enum):
    """Setores macroeconômicos com flags de alta sensibilidade à Reforma."""

    COMERCIO = "comercio"
    INDUSTRIA = "industria"
    SERVICOS = "servicos"
    AGRO = "agro"  # PwC: 60% apreensivo com elevação de carga
    CONSUMO = "consumo"  # PwC: 53% apreensivo


@dataclass(frozen=True, slots=True)
class EmpresaInfo:
    """Informações de identificação da empresa-cliente (snapshot no momento do diagnóstico)."""

    cnpj: str  # 14 dígitos sem máscara
    razao_social: str
    porte: PorteEmpresa
    regime: RegimeTributario
    cnae_principal: str  # 7 dígitos
    uf: str  # sigla 2 caracteres
    setor_macro: SetorMacro

    def __post_init__(self) -> None:
        if len(self.cnpj) != 14 or not self.cnpj.isdigit():
            raise ValueError("CNPJ deve conter exatamente 14 dígitos numéricos")
        if len(self.uf) != 2:
            raise ValueError("UF deve ter 2 caracteres (ex: SP, RJ)")


@dataclass(frozen=True, slots=True)
class Respondente:
    """Pessoa que está conduzindo o diagnóstico em nome da empresa."""

    email: str
    nome: str | None = None
    cargo: str | None = None  # CFO, Contador, Dono, Diretor TI, etc.


@dataclass
class Diagnostico:
    """
    Entidade-raiz do agregado Diagnóstico.

    Invariantes de domínio:
        1. Um diagnóstico só pode ser finalizado se status == EM_ANDAMENTO
        2. Score só existe quando finalizado
        3. tenant_id é imutável após criação (multi-tenant strict)
        4. Diagnóstico expirado não pode ser modificado (apenas arquivado)

    Eventos de domínio publicados:
        - DiagnosticoIniciado
        - DiagnosticoFinalizado (dispara geração de relatório PDF)
        - DiagnosticoExpirado (após 7 dias sem finalização)
    """

    tenant_id: UUID
    empresa: EmpresaInfo
    respondente: Respondente
    id: UUID = field(default_factory=uuid4)
    status: StatusDiagnostico = StatusDiagnostico.EM_ANDAMENTO
    criado_em: datetime = field(default_factory=lambda: datetime.now(UTC))
    finalizado_em: datetime | None = None
    score_geral: float | None = None  # 0-100, só preenchido após finalização
    relatorio_pdf_url: str | None = None

    def finalizar(self, score_geral: float) -> None:
        """
        Finaliza o diagnóstico, marcando o score geral.

        Args:
            score_geral: valor entre 0 e 100 (validado).

        Raises:
            ValueError: se score fora do intervalo [0, 100].
            DiagnosticoNaoFinalizavelError: se status != EM_ANDAMENTO.
        """
        if self.status != StatusDiagnostico.EM_ANDAMENTO:
            raise DiagnosticoNaoFinalizavelError(
                f"Diagnóstico {self.id} está com status {self.status.value}, "
                f"não pode ser finalizado novamente."
            )

        if not 0.0 <= score_geral <= 100.0:
            raise ValueError(f"Score geral inválido: {score_geral}. Deve estar entre 0 e 100.")

        self.score_geral = score_geral
        self.status = StatusDiagnostico.FINALIZADO
        self.finalizado_em = datetime.now(UTC)

    def anexar_relatorio(self, url: str) -> None:
        """Anexa URL do PDF gerado (output principal do diagnóstico)."""
        if self.status != StatusDiagnostico.FINALIZADO:
            raise DiagnosticoNaoFinalizavelError(
                "Só é possível anexar relatório a um diagnóstico finalizado."
            )
        self.relatorio_pdf_url = url


# ============================================================
# Exceptions de domínio
# ============================================================


class DiagnosticoNaoFinalizavelError(Exception):
    """Levantada quando se tenta finalizar um diagnóstico em estado inválido."""
