#!/usr/bin/env python3
"""Gera FASE_B_BENCHMARK_MODELOS.md a partir de fase_b_raw.json + rubrica heuristica."""

from __future__ import annotations

import json
import re
from pathlib import Path

RAW = Path("_DEVELOPER/IA_DIAG_V2/reports/fase_b_raw.json")
OUT = Path("_DEVELOPER/IA_DIAG_V2/reports/FASE_B_BENCHMARK_MODELOS.md")


def _nota_pt_br(texto: str) -> int:
    if not texto.strip():
        return 0
    t = texto.lower()
    if any(w in t for w in ("qualidiagiq", "qdi", "diagnostico tributario", "reforma tributaria")):
        return 3 if "mvp" in t or "escopo" in t else 2
    return 1 if len(texto) > 80 else 0


def _nota_qdi(texto: str) -> int:
    t = texto.lower()
    score = 0
    if "qualidiagiq" in t or "qdi" in t:
        score += 1
    if any(x in t for x in ("mvp", "fora do escopo", "qai", "apuração", "winthor")):
        score += 1
    if "diagnóstico" in t or "diagnostico" in t:
        score += 1
    return min(score, 3)


def _nota_arquitetura(texto: str, pid: str) -> int:
    t = texto.lower()
    if pid == "P2":
        if "domain" in t and ("application" in t or "use case" in t or "caso de uso" in t):
            return 3
        if "domain" in t:
            return 2
        return 0 if "router" in t and "domain" not in t else 1
    if pid == "P5":
        if "auditar" in t or "evoluir" in t or "gateway" in t:
            return 3 if "paralel" not in t or "nao criar" in t else 2
        return 1
    return 2


def _nota_fonte(texto: str, pid: str) -> int:
    t = texto.lower()
    if pid in ("P3", "P4"):
        if "base insuficiente" in t or "insuficiente" in t:
            return 3
        if any(x in t for x in ("lc 214", "ec 132", "nt 2025", "citar", "citacao", "fonte")):
            return 3
        if "nao" in t and "sem cit" in t.replace("ç", "c"):
            return 2
        return 0
    return 2


def _nota_latencia(ms: int) -> int:
    if ms <= 0:
        return 0
    if ms < 30_000:
        return 3
    if ms < 90_000:
        return 2
    if ms < 180_000:
        return 1
    return 0


def main() -> None:
    data = json.loads(RAW.read_text(encoding="utf-8"))
    runs = data["runs"]

    linhas = [
        "# FASE B — Benchmark de Modelos Locais",
        "",
        "> **Gerado automaticamente** a partir de `fase_b_raw.json` + rubrica heuristica.",
        "> **Revisao humana recomendada** (Allan) antes de congelar modelo base.",
        "",
        f"**Executado em:** {data.get('executado_em', '')}",
        "",
        "## Modelos testados",
        "",
    ]
    modelos = sorted({r["modelo"] for r in runs})
    for m in modelos:
        linhas.append(f"- `{m}`")

    totais: dict[str, list[float]] = {m: [] for m in modelos}

    for r in runs:
        resp = str(r.get("resposta", ""))
        pid = str(r["pergunta_id"])
        ms = int(r.get("elapsed_ms") or 0)
        notas = {
            "PT-BR": _nota_pt_br(resp),
            "QDI": _nota_qdi(resp),
            "Arquitetura": _nota_arquitetura(resp, pid),
            "Fonte": _nota_fonte(resp, pid),
            "Acionabilidade": 2 if len(resp) > 200 else 1,
            "Latencia": _nota_latencia(ms),
        }
        media = sum(notas.values()) / len(notas)
        totais[str(r["modelo"])].append(media)

        linhas.extend(
            [
                "",
                f"### {r['modelo']} — {pid}",
                "",
                f"- **Latencia:** {ms} ms",
                f"- **Media rubrica:** {media:.2f}/3",
                "",
                "<details><summary>Resposta (trecho)</summary>",
                "",
                "```text",
                resp[:1200] + ("..." if len(resp) > 1200 else ""),
                "```",
                "",
                "</details>",
                "",
                "| Criterio | Nota |",
                "|---|---:|",
            ]
        )
        for k, v in notas.items():
            linhas.append(f"| {k} | {v} |")

    linhas.extend(["", "## Ranking (media geral)", ""])
    ranking = sorted(
        ((m, sum(v) / len(v) if v else 0) for m, v in totais.items()),
        key=lambda x: x[1],
        reverse=True,
    )
    for i, (m, avg) in enumerate(ranking, 1):
        linhas.append(f"{i}. **{m}** — {avg:.2f}/3")

    melhor = ranking[0][0] if ranking else "?"
    leve = min(ranking, key=lambda x: (x[1], x[0]))[0] if ranking else "?"
    # melhor leve: llama3.2 if in list
    for m, _ in ranking:
        if "llama3.2" in m or "7b" in m:
            leve = m
            break

    linhas.extend(
        [
            "",
            "## Decisao recomendada (handoff)",
            "",
            f"- **Modelo base qualidade:** `{melhor}`",
            f"- **Modelo leve / smoke:** `{leve}`",
            "- **Embedding RAG piloto:** `mxbai-embed-large:latest` (validado Fase D)",
            "",
            "```text",
            "Prosseguir Fase C/D com qdi-assistant para persona e "
            f"{melhor} para tarefas de raciocinio longo se latencia aceitavel.",
            "```",
            "",
        ]
    )

    OUT.write_text("\n".join(linhas), encoding="utf-8")
    print(f"OK -> {OUT}")


if __name__ == "__main__":
    main()
