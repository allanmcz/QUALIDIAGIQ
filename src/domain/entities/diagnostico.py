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
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from src.domain.value_objects.checklist_m12_likert import validar_itens_m12_likert
from src.domain.value_objects.cnpj_brasil import exigir_cnpj_vazio_ou_com_dv_ok
from src.domain.value_objects.email import normalizar_email

if TYPE_CHECKING:
    from src.domain.value_objects.score import ScoreCompleto


class StatusDiagnostico(Enum):
    """Estados possíveis de um diagnóstico ao longo do ciclo de vida."""

    EM_ANDAMENTO = "em_andamento"
    FINALIZADO = "finalizado"
    EXPIRADO = "expirado"
    CANCELADO = "cancelado"


class PainelEstadoCicloDiagnostico(StrEnum):
    """
    Estado de acompanhamento no painel administrativo (separado do ``StatusDiagnostico`` técnico).

    O snapshot de evidência permanece imutável quando ``StatusDiagnostico.FINALIZADO``; este campo
    apenas classifica o ciclo operacional percebido pelo consultor (planeamento, descarte, encerramento).

    Base normativa complementar: LC 214/2025 (previsibilidade processual); ABNT NBR 17301:2026 (gestão).
    """

    REALIZADO = "realizado"
    EM_ANDAMENTO = "em_andamento"
    DESCARTADO = "descartado"
    FINALIZADO = "finalizado"


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
    GRANDE = "grande"  # a partir de R$ 500 mi (faixa superior única no assistente MVP)


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

    Documentação produto/convenção MVP: docs/operacao/FAIXA_FATURAMENTO_AUTODECLARADA.md.
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

    def para_snapshot_evidencia(self) -> dict[str, Any]:
        """Campos de empresa incluídos no hash de evidência v2 (alinhamento WORM / LGPD art. 46)."""
        return {
            "cnpj": self.cnpj,
            "razao_social": self.razao_social,
            "porte": self.porte.value,
            "regime": self.regime.value,
            "cnae_principal": self.cnae_principal,
            "uf": self.uf,
            "setor_macro": self.setor_macro.value,
            "faixa_faturamento": self.faixa_faturamento.value if self.faixa_faturamento else None,
        }


@dataclass(frozen=True, slots=True)
class Respondente:
    """Pessoa que está conduzindo o diagnóstico em nome da empresa."""

    email: str
    nome: str | None = None
    cargo: str | None = None  # CFO, Contador, Dono, Diretor TI, etc.
    telefone: str | None = (
        None  # M09 — lead na plataforma opcional (persistência quando coluna existir)
    )
    #: Melhor esforço na camada HTTP (LGPD — removido na anonimização padronizada).
    ip_origem: str | None = None


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
    # M12 - autoconf ABNT (10 x Likert 1-5); mutável após finalizado com versao_otimista (vide PATCH dedicado).
    checklist_m12_estado: list[int] | None = None
    # Quadro de implantação — anotações do consultor por ação (chave f{i}_a{j}); não entra no hash WORM.
    # Cada item: prazo_meta (ISO) + comentarios[]; opcional descricao_personalizada (substitui texto canônico no painel).
    quadro_implantacao_anotacoes: dict[str, dict[str, str | list[str]]] | None = None
    # LGPD — instante do aceite declarado no POST (persistido pelo servidor; imutável após finalizado via WORM).
    aceite_termos_privacidade_em: datetime | None = None
    # Relatório PDF (WeasyPrint) — pt-BR default; en preparado para expansão i18n.
    locale_relatorio: str = "pt-BR"
    # Versão do plano de ação materializado (snapshot checklist/matriz/cronograma — D3).
    versao_plano: int = 1
    # Última narrativa POST explicacao-score-llm (JSONB); mutável pós-finalizado — fora do hash WORM.
    explicacao_score_llm: dict[str, Any] | None = None
    # Sequencial por tenant + CNPJ (ou e-mail do respondente quando CNPJ vazio) — apenas para listagens do painel.
    numero_interno_grupo: int | None = None
    # Ciclo administrativo visível na grelha do painel (coluna Postgres ``painel_estado_ciclo``).
    painel_estado_ciclo: str = PainelEstadoCicloDiagnostico.EM_ANDAMENTO.value

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
        self.painel_estado_ciclo = PainelEstadoCicloDiagnostico.REALIZADO.value
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
            "_versao_payload_hash": "v2",
            "diagnostico_id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "plano": self.plano.value,
            "versao_plano": self.versao_plano,
            "empresa": self.empresa.para_snapshot_evidencia(),
            "respondente": {
                "email": normalizar_email(self.respondente.email),
                "nome": self.respondente.nome,
                "cargo": self.respondente.cargo,
                "telefone": self.respondente.telefone,
            },
            "score_geral": self.score_geral,
            "status": self.status.value,
            "finalizado_em": self.finalizado_em.isoformat() if self.finalizado_em else None,
            "score_completo": score_completo.para_dict_serializavel(),
            "checklist_m12_estado": self.checklist_m12_estado,
            "aceite_termos_privacidade_em": (
                self.aceite_termos_privacidade_em.isoformat()
                if self.aceite_termos_privacidade_em
                else None
            ),
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

    def definir_checklist_m12_autoconf(self, itens: list[int]) -> None:
        """
        Persistência lógica da autoconf ABNT - 10 itens em escala Likert 1-5 (M12).

        Base normativa: ABNT NBR 17301:2026 (autoconferência operacional).
        """
        if self.status != StatusDiagnostico.FINALIZADO:
            raise DiagnosticoNaoFinalizavelError(
                "Só é possível atualizar a autoconf M12 em diagnóstico finalizado."
            )
        validar_itens_m12_likert(itens)
        self.checklist_m12_estado = list(itens)

    def definir_painel_estado_ciclo(self, estado: PainelEstadoCicloDiagnostico) -> None:
        """
        Atualiza o ciclo operacional exibido ao consultor (campo ``painel_estado_ciclo``).

        Não altera nem invalida a evidência técnica já congelada quando ``status`` é finalizado;
        é metadado de acompanhamento (ABNT NBR 17301 — ciclo PDCA operacional).
        """
        self.painel_estado_ciclo = estado.value

    _CHAVE_QUADRO_RE = re.compile(r"^f\d+_a\d+$")
    _CHAVE_QUADRO_UUID_RE = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    _QUADRO_MAX_COMENTARIOS_POR_ACAO = 30
    _QUADRO_MAX_CHARS_POR_COMENTARIO = 2000
    _QUADRO_MAX_DESCRICAO_PERSONALIZADA = 4000

    def definir_quadro_implantacao_anotacoes(self, anotacoes: dict[str, dict[str, Any]]) -> None:
        """
        Substitui o mapa de anotações do quadro de implantação (prazo meta + vários comentários por ação).

        Chaves esperadas: ``f{{i}}_a{{j}}`` (índices da frente e da ação no checklist derivado).

        Entrada aceita ``comentarios`` (lista de strings) e/ou ``comentario`` (legado — vira um único item),
        além de ``descricao_personalizada`` opcional (texto exibido no lugar da descrição canônica da ação).

        Raises:
            DiagnosticoNaoFinalizavelError: se não finalizado.
            ValueError: chaves ou estrutura inválidas.
        """
        if self.status != StatusDiagnostico.FINALIZADO:
            raise DiagnosticoNaoFinalizavelError(
                "Só é possível atualizar o quadro de implantação em diagnóstico finalizado."
            )
        if len(anotacoes) > 200:
            raise ValueError("No máximo 200 anotações no quadro de implantação.")
        limpo: dict[str, dict[str, str | list[str]]] = {}
        for chave, item in anotacoes.items():
            ck = str(chave).strip()
            chave_ok = bool(self._CHAVE_QUADRO_RE.match(ck)) or bool(
                self._CHAVE_QUADRO_UUID_RE.match(ck)
            )
            if not chave_ok:
                raise ValueError(
                    f"Chave de anotação inválida: {ck!r}. Use UUID da ação materializada ou f{{índice}}_a{{índice}}."
                )
            prazo_meta = str(item.get("prazo_meta", "") or "").strip()
            if prazo_meta != "" and (
                len(prazo_meta) != 10 or prazo_meta[4] != "-" or prazo_meta[7] != "-"
            ):
                raise ValueError("prazo_meta deve ser data ISO YYYY-MM-DD ou vazio.")

            comentarios: list[str] = []
            raw_list = item.get("comentarios")
            if isinstance(raw_list, list):
                for x in raw_list:
                    s = str(x).strip()
                    if s:
                        comentarios.append(s)
            if not comentarios:
                leg = str(item.get("comentario", "") or "").strip()
                if leg:
                    comentarios = [leg]
            if len(comentarios) > self._QUADRO_MAX_COMENTARIOS_POR_ACAO:
                raise ValueError(
                    f"No máximo {self._QUADRO_MAX_COMENTARIOS_POR_ACAO} comentários por ação sugerida."
                )
            for c in comentarios:
                if len(c) > self._QUADRO_MAX_CHARS_POR_COMENTARIO:
                    raise ValueError(
                        f"Cada comentário excede {self._QUADRO_MAX_CHARS_POR_COMENTARIO} caracteres."
                    )
            desc_pers = str(item.get("descricao_personalizada", "") or "").strip()
            if len(desc_pers) > self._QUADRO_MAX_DESCRICAO_PERSONALIZADA:
                raise ValueError(
                    "descricao_personalizada excede "
                    f"{self._QUADRO_MAX_DESCRICAO_PERSONALIZADA} caracteres."
                )
            entrada: dict[str, str | list[str]] = {
                "prazo_meta": prazo_meta,
                "comentarios": comentarios,
            }
            if desc_pers:
                entrada["descricao_personalizada"] = desc_pers
            limpo[ck] = entrada
        self.quadro_implantacao_anotacoes = limpo

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
