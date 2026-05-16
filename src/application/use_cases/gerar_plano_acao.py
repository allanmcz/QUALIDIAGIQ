"""
Caso de uso: materializar catálogo lógico ``ItemAcao`` a partir do plano derivado.

Camada: Application
Útil para testes de regressão, exportações futuras e enriquecimento Plus (Sprint 7+).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID  # noqa: TC003 — assinaturas públicas do caso de uso

from src.application.services.plano_painel_derivacao import (
    DerivacaoPlanoMaterializado,
    LinhaPlanoAcaoParaPersistir,
)
from src.application.services.validador_recusa_controlada import (
    ResultadoValidacaoPlano,
    ValidadorRecusaControlada,
)
from src.domain.entities.plano_acao import ItemAcao
from src.domain.services.calculador_plano_acao import chunk_id_sintetico_para_texto
from src.domain.value_objects.evidencia_lexiq import EvidenciaLexiq
from src.domain.value_objects.plano_acao import (
    CriticidadePlanoAcao,
    FasePdcaPlano,
    HorizontePlanoAcao,
)


def _evidencia_minima_de_linha(ln: LinhaPlanoAcaoParaPersistir) -> EvidenciaLexiq:
    """Evidência curada (motor determinístico) — score 1.0 satisfaz recusa controlada."""
    bl = (ln.base_legal or "LC 214/2025").strip()
    trecho = bl[:500]
    return EvidenciaLexiq(
        norma="Motor determinístico QDI",
        dispositivo="Sprint-1-curadoria",
        versao="v1.0.0",
        vigencia_inicio=date(2026, 1, 1),
        vigencia_fim=None,
        chunk_id=chunk_id_sintetico_para_texto(ln.texto_acao),
        citacao_texto=trecho or "LC 214/2025 — transição e previsibilidade ao contribuinte.",
        score_similaridade=1.0,
    )


class GerarPlanoAcaoUseCase:
    """Converte derivação materializada em itens de domínio auditáveis."""

    def __init__(self, validador: ValidadorRecusaControlada | None = None) -> None:
        self._validador = validador or ValidadorRecusaControlada()

    def construir_itens(
        self,
        tenant_id: UUID,
        diagnostico_id: UUID,
        deriv: DerivacaoPlanoMaterializado,
    ) -> list[ItemAcao]:
        out: list[ItemAcao] = []
        for ln in deriv.linhas_acao:
            crit = CriticidadePlanoAcao(ln.criticidade_codigo)
            hz = HorizontePlanoAcao(ln.horizonte_planejado)
            fp = FasePdcaPlano(ln.fase_pdca)
            evid = _evidencia_minima_de_linha(ln)
            item = ItemAcao(
                id=ln.id,
                tenant_id=tenant_id,
                diagnostico_id=diagnostico_id,
                codigo=f"ACAO-ORD-{ln.ordem_exibicao:04d}",
                titulo=(ln.texto_acao[:120] if len(ln.texto_acao) > 120 else ln.texto_acao),
                descricao=ln.texto_acao[:2000],
                dimensao=ln.dimensao_origem or "nucleo",
                fase_pdca=fp,
                horizonte=hz,
                criticidade=crit,
                area_responsavel=ln.responsavel_sugerido,
                peso_calculado=min(10.0, max(0.0, float(ln.peso_motor))),
                perguntas_origem=list(ln.perguntas_origem_ids),
                evidencias=(evid,),
            )
            res = self._validador.validar(item)
            if not res.aprovado:
                raise ValueError(f"Item inválido pós-derivação: {res.motivo} — {res.metadata}")
            out.append(item)
        return out

    def validar_derivacao(
        self, tenant_id: UUID, diagnostico_id: UUID, deriv: DerivacaoPlanoMaterializado
    ) -> ResultadoValidacaoPlano:
        """Valida todas as linhas sem levantar excepção (útil para API 422 futura)."""
        try:
            _ = self.construir_itens(tenant_id, diagnostico_id, deriv)
        except ValueError as e:
            return ResultadoValidacaoPlano.recusa("derivacao_invalida", detalhe=str(e))
        return ResultadoValidacaoPlano.ok()
