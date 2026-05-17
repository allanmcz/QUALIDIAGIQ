"""
Backfill de respostas materializadas para diagnósticos legados (rascunho self-service).

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.application.services.diagnostico_payload_respostas import entradas_resposta_de_payload_dict
from src.application.services.diagnostico_resposta_materializacao import derivar_respostas_e_linhas


@dataclass(frozen=True)
class ComandoBackfillRespostasQuestionario:
    tenant_id: UUID
    limite: int = 50
    janela_horas_rascunho: int = 48


@dataclass(frozen=True)
class ResultadoBackfillRespostasQuestionario:
    processados: int
    preenchidos: int
    sem_fonte: int
    erros: int
    detalhes: tuple[dict[str, Any], ...]


class BackfillRespostasQuestionario:
    """
    Preenche ``diagnostico_resposta_questionario`` quando há rascunho consumido compatível.

    Diagnósticos criados só pelo painel (sem rascunho) permanecem sem fonte — relatório explícito.
    """

    def __init__(
        self,
        *,
        listar_sem_respostas,
        buscar_payload_rascunho,
        persistir_linhas,
    ) -> None:
        self._listar_sem_respostas = listar_sem_respostas
        self._buscar_payload_rascunho = buscar_payload_rascunho
        self._persistir_linhas = persistir_linhas

    async def execute(self, comando: ComandoBackfillRespostasQuestionario) -> ResultadoBackfillRespostasQuestionario:
        candidatos = await self._listar_sem_respostas(
            comando.tenant_id, limite=comando.limite
        )
        detalhes: list[dict[str, Any]] = []
        preenchidos = 0
        sem_fonte = 0
        erros = 0

        for row in candidatos:
            did = UUID(str(row["id"]))
            tid = UUID(str(row["tenant_id"]))
            try:
                payload_raw = await self._buscar_payload_rascunho(
                    did, tid, janela_horas=comando.janela_horas_rascunho
                )
                if payload_raw is None:
                    sem_fonte += 1
                    detalhes.append(
                        {
                            "diagnostico_id": str(did),
                            "status": "sem_fonte",
                            "motivo": "Nenhum rascunho self-service compatível (e-mail/CNPJ/janela temporal).",
                        }
                    )
                    continue
                try:
                    entradas = entradas_resposta_de_payload_dict(payload_raw)
                except ValueError as ve:
                    erros += 1
                    detalhes.append(
                        {
                            "diagnostico_id": str(did),
                            "status": "erro",
                            "motivo": f"Payload de rascunho inválido: {ve}",
                        }
                    )
                    continue
                if not entradas:
                    sem_fonte += 1
                    detalhes.append(
                        {
                            "diagnostico_id": str(did),
                            "status": "sem_fonte",
                            "motivo": "Rascunho sem respostas no payload.",
                        }
                    )
                    continue
                _, linhas = derivar_respostas_e_linhas(did, entradas)
                inseriu = await self._persistir_linhas(did, tid, linhas)
                if inseriu:
                    preenchidos += 1
                    detalhes.append(
                        {
                            "diagnostico_id": str(did),
                            "status": "preenchido",
                            "total_respostas": len(linhas),
                        }
                    )
                else:
                    detalhes.append(
                        {
                            "diagnostico_id": str(did),
                            "status": "ja_existia",
                            "total_respostas": len(linhas),
                        }
                    )
            except Exception as exc:
                erros += 1
                detalhes.append(
                    {
                        "diagnostico_id": str(did),
                        "status": "erro",
                        "motivo": str(exc),
                    }
                )

        return ResultadoBackfillRespostasQuestionario(
            processados=len(candidatos),
            preenchidos=preenchidos,
            sem_fonte=sem_fonte,
            erros=erros,
            detalhes=tuple(detalhes),
        )
