"""
Caso de uso: comparar respostas do questionário entre vários diagnósticos (mesmo tenant).

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.domain.repositories.diagnostico_repository import DiagnosticoRepository


@dataclass(frozen=True)
class ComandoCompararQuestionario:
    tenant_id: UUID
    diagnostico_ids: tuple[UUID, ...]


class CompararQuestionarioDiagnosticos:
    """Alinha respostas por ``pergunta_codigo`` para evolução entre ciclos."""

    MIN_DIAGNOSTICOS = 2
    MAX_DIAGNOSTICOS = 5

    def __init__(self, repo: DiagnosticoRepository) -> None:
        self._repo = repo

    async def execute(self, comando: ComandoCompararQuestionario) -> dict[str, Any]:
        ids = comando.diagnostico_ids
        n = len(ids)
        if n < self.MIN_DIAGNOSTICOS:
            raise ValueError(
                f"Selecione pelo menos {self.MIN_DIAGNOSTICOS} diagnósticos para comparar."
            )
        if n > self.MAX_DIAGNOSTICOS:
            raise ValueError(f"Máximo de {self.MAX_DIAGNOSTICOS} diagnósticos por comparação.")

        unicos = list(dict.fromkeys(ids))
        if len(unicos) != n:
            raise ValueError("Lista de diagnósticos contém IDs duplicados.")

        meta: list[dict[str, Any]] = []
        por_diag: dict[str, list[dict[str, Any]]] = {}
        cnpj_ref: str | None = None
        razao_ref: str | None = None

        for did in unicos:
            d = await self._repo.buscar_por_id(did, comando.tenant_id)
            if d is None:
                raise ValueError(f"Diagnóstico não encontrado: {did}")
            cnpj = (d.empresa.cnpj or "").strip()
            if cnpj_ref is None:
                cnpj_ref = cnpj
                razao_ref = d.empresa.razao_social
            elif cnpj and cnpj_ref and cnpj != cnpj_ref:
                raise ValueError(
                    "Todos os diagnósticos comparados devem ser da mesma empresa (CNPJ)."
                )
            respostas = await self._repo.listar_respostas_questionario(did, comando.tenant_id)
            por_diag[str(did)] = respostas
            fin = d.finalizado_em.isoformat() if d.finalizado_em else None
            meta.append(
                {
                    "diagnostico_id": str(did),
                    "finalizado_em": fin,
                    "score_geral": d.score_geral,
                    "numero_interno_grupo": d.numero_interno_grupo,
                    "total_respostas": len(respostas),
                }
            )

        meta.sort(key=lambda m: m.get("finalizado_em") or "")

        # União ordenada por código + primeira ordem vista
        codigos_ordem: list[str] = []
        vistos: set[str] = set()
        for did in [UUID(m["diagnostico_id"]) for m in meta]:
            for r in por_diag[str(did)]:
                cod = str(r["pergunta_codigo"])
                if cod not in vistos:
                    vistos.add(cod)
                    codigos_ordem.append(cod)

        linhas: list[dict[str, Any]] = []
        for cod in codigos_ordem:
            texto = ""
            dimensao = ""
            base_legal: str | None = None
            valores: dict[str, dict[str, Any]] = {}
            for m in meta:
                did_s = m["diagnostico_id"]
                match = next(
                    (r for r in por_diag[did_s] if str(r["pergunta_codigo"]) == cod),
                    None,
                )
                if match:
                    if not texto:
                        texto = str(match["texto_pergunta"])
                        dimensao = str(match["dimensao"])
                        base_legal = match.get("base_legal")
                    valores[did_s] = {
                        "valor_exibicao": str(match["valor_exibicao"]),
                        "pontuacao_item": match.get("pontuacao_item"),
                        "excluida_calculo": bool(match.get("excluida_calculo")),
                        "ordem_exibicao": int(match["ordem_exibicao"]),
                    }
                else:
                    valores[did_s] = {
                        "valor_exibicao": "—",
                        "pontuacao_item": None,
                        "excluida_calculo": False,
                        "ordem_exibicao": None,
                    }
            linhas.append(
                {
                    "pergunta_codigo": cod,
                    "texto_pergunta": texto,
                    "dimensao": dimensao,
                    "base_legal": base_legal,
                    "valores_por_diagnostico": valores,
                }
            )

        return {
            "empresa_cnpj": cnpj_ref or "",
            "empresa_razao_social": razao_ref or "",
            "diagnosticos": meta,
            "linhas": linhas,
        }
