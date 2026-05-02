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

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from src.domain.value_objects.cnpj_brasil import exigir_cnpj_vazio_ou_com_dv_ok

if TYPE_CHECKING:
    from src.domain.value_objects.score import ScoreCompleto


class StatusDiagnostico(Enum):
    """Estados possíveis de um diagnóstico ao longo do ciclo de vida."""

    EM_ANDAMENTO = "em_andamento"
    FINALIZADO = "finalizado"
    EXPIRADO = "expirado"
    CANCELADO = "cancelado"


class PlanoDiagnostico(Enum):
    """Nível do serviço escolhido."""

    GRATUITO = "gratuito"
    AVANCADO = "avancado"


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


class FaixaFaturamentoDeclarada(Enum):
    """
    Faixa de faturamento bruto anual **autodeclarada** (opcional).

    Valores em R$ para segmentação / benchmark; não substitui escrituração nem auditoria.
    Marcos alinhados a faixas usuais de enquadramento (ex.: limites do Simples Nacional, LC 123/2006).
    """

    ATE_360_MIL = "ate_360_mil"
    ENTRE_360_MIL_E_4_8_MI = "entre_360_mil_e_4_8_mi"
    ENTRE_4_8_MI_E_10_MI = "entre_4_8_mi_e_10_mi"
    ENTRE_10_MI_E_60_MI = "entre_10_mi_e_60_mi"
    ENTRE_60_MI_E_100_MI = "entre_60_mi_e_100_mi"
    ENTRE_100_MI_E_500_MI = "entre_100_mi_e_500_mi"
    ACIMA_500_MI = "acima_500_mi"


@dataclass(frozen=True, slots=True)
class EmpresaInfo:
    """Informações de identificação da empresa-cliente (snapshot no momento do diagnóstico)."""

    cnpj: str  # 14 dígitos sem máscara, ou "" se não informado (fluxo sem identificação cadastral)
    razao_social: str
    porte: PorteEmpresa
    regime: RegimeTributario
    cnae_principal: str  # 7 dígitos
    uf: str  # sigla 2 caracteres
    setor_macro: SetorMacro
    faixa_faturamento: FaixaFaturamentoDeclarada | None = None

    def __post_init__(self) -> None:
        if self.cnpj == "":
            pass
        elif len(self.cnpj) != 14 or not self.cnpj.isdigit():
            raise ValueError("CNPJ deve conter exatamente 14 dígitos numéricos ou ficar vazio")
        else:
            exigir_cnpj_vazio_ou_com_dv_ok(self.cnpj)
        if len(self.uf) != 2:
            raise ValueError("UF deve ter 2 caracteres (ex: SP, RJ)")


@dataclass(frozen=True, slots=True)
class Respondente:
    """Pessoa que está conduzindo o diagnóstico em nome da empresa."""

    email: str
    nome: str | None = None
    cargo: str | None = None  # CFO, Contador, Dono, Diretor TI, etc.
    telefone: str | None = None  # M09 — lead B2B opcional (persistência quando coluna existir)


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
    plano: PlanoDiagnostico = PlanoDiagnostico.GRATUITO
    id: UUID = field(default_factory=uuid4)
    status: StatusDiagnostico = StatusDiagnostico.EM_ANDAMENTO
    criado_em: datetime = field(default_factory=lambda: datetime.now(UTC))
    finalizado_em: datetime | None = None
    score_geral: float | None = None  # 0-100, só preenchido após finalização
    relatorio_pdf_url: str | None = None
    # Evidência auditável (persistência: hash_sha256, score_completo JSONB, versao_otimista)
    score_completo_snapshot: ScoreCompleto | None = None
    hash_evidencia: str | None = None  # SHA-256 hex (64 caracteres)
    versao_otimista: int = 1
    # M12 — autoconf ABNT (10 booleanos); mutável após finalizado com versao_otimista (vide PATCH dedicado).
    checklist_m12_estado: list[bool] | None = None
    # LGPD — instante do aceite declarado no POST (persistido pelo servidor; imutável após finalizado via WORM).
    aceite_termos_privacidade_em: datetime | None = None
    # Relatório PDF (WeasyPrint) — pt-BR default; en preparado para expansão i18n.
    locale_relatorio: str = "pt-BR"

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

    def registrar_score_completo_para_evidencia(self, score_completo: ScoreCompleto) -> None:
        """
        Congela o score completo e calcula hash de integridade para trilha de auditoria.

        Deve ser chamado imediatamente após `finalizar`, antes da primeira persistência
        definitiva (imutabilidade alinhada ao trigger WORM no PostgreSQL).
        """
        if self.status != StatusDiagnostico.FINALIZADO:
            raise DiagnosticoNaoFinalizavelError(
                "Score completo para evidência só pode ser registrado após finalização."
            )
        if self.score_geral is None:
            raise ValueError("Score geral ausente — inconsistência de estado.")

        self.score_completo_snapshot = score_completo
        payload = {
            "diagnostico_id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "score_geral": self.score_geral,
            "status": self.status.value,
            "finalizado_em": self.finalizado_em.isoformat() if self.finalizado_em else None,
            "score_completo": score_completo.para_dict_serializavel(),
            "locale_relatorio": self.locale_relatorio,
        }
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        self.hash_evidencia = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def finalizar_e_registrar_evidencia(self, score_completo: ScoreCompleto) -> None:
        """
        Fluxo atômico de domínio: finalizar com o score geral do snapshot e registrar evidência.

        Garante ordenação correta antes da persistência WORM (PostgreSQL) e alinhamento ao
        ciclo de rastreabilidade (ABNT NBR 17301:2026 — governança do compliance tributário).
        """
        self.finalizar(score_geral=score_completo.score_geral.valor)
        self.registrar_score_completo_para_evidencia(score_completo)

    def anexar_relatorio(self, url: str) -> None:
        """Anexa URL do PDF gerado (output principal do diagnóstico)."""
        if self.status != StatusDiagnostico.FINALIZADO:
            raise DiagnosticoNaoFinalizavelError(
                "Só é possível anexar relatório a um diagnóstico finalizado."
            )
        self.relatorio_pdf_url = url

    def definir_checklist_m12_autoconf(self, itens: list[bool]) -> None:
        """
        Persistência lógica da autoconf ABNT — 10 controles binários (M12).

        Base normativa: ABNT NBR 17301:2026 (autoconferência operacional).
        """
        if self.status != StatusDiagnostico.FINALIZADO:
            raise DiagnosticoNaoFinalizavelError(
                "Só é possível atualizar a autoconf M12 em diagnóstico finalizado."
            )
        if len(itens) != 10:
            raise ValueError("Autoconf M12 exige exatamente 10 itens booleanos.")
        self.checklist_m12_estado = list(itens)

    def registrar_aceite_termos_privacidade(self, instante_utc: datetime) -> None:
        """
        Associa o instante do aceite LGPD antes da finalização.

        Raises:
            DiagnosticoNaoFinalizavelError: se já finalizado (evidência em formação inconsistente).
            ValueError: se instante inválido.
        """
        if self.status != StatusDiagnostico.EM_ANDAMENTO:
            raise DiagnosticoNaoFinalizavelError(
                "Aceite LGPD só pode ser registrado enquanto o diagnóstico está em andamento."
            )
        if instante_utc.tzinfo is None:
            raise ValueError("Instante de aceite deve ser timezone-aware (UTC).")
        self.aceite_termos_privacidade_em = instante_utc


# ============================================================
# Exceptions de domínio
# ============================================================


class DiagnosticoNaoFinalizavelError(Exception):
    """Levantada quando se tenta finalizar um diagnóstico em estado inválido."""
