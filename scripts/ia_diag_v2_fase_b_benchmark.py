#!/usr/bin/env python3
"""
Fase B IA_DIAG_V2 — benchmark local via API Ollama (sem alterar src/).

Uso:
  PYTHONPATH=. python scripts/ia_diag_v2_fase_b_benchmark.py
  PYTHONPATH=. python scripts/ia_diag_v2_fase_b_benchmark.py --modelos llama3.2:latest,qdi-assistant:latest
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODELS = ("llama3.2:latest", "qdi-assistant:latest", "qwen2.5-coder:14b")

PERGUNTAS: dict[str, str] = {
    "P1": (
        "Explique em 6 frases o que e o QualiDiagIQ, qual o escopo do MVP "
        "e o que fica fora do MVP."
    ),
    "P2": (
        "No QDI, onde devo implementar uma regra pura de calculo de score tributario "
        "e onde devo implementar o caso de uso que salva o resultado?"
    ),
    "P3": (
        "Responda com cautela: uma resposta sobre CBS/IBS pode ser aceita sem citacao "
        "de fonte normativa? Explique a politica correta."
    ),
    "P4": (
        "Se a base local nao tiver fonte primaria suficiente sobre uma regra tributaria, "
        "como o agente deve responder?"
    ),
    "P5": (
        "O QDI ja possui gateway LLM e adapters. Voce deve criar um novo adapter do zero "
        "ou auditar e evoluir o existente? Justifique."
    ),
}


def _gerar(modelo: str, prompt: str, *, timeout_s: int = 300) -> dict[str, object]:
    body = json.dumps(
        {
            "model": modelo,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": 400, "temperature": 0.3},
        }
    ).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {"erro": f"HTTP {e.code}", "elapsed_ms": elapsed_ms, "resposta": ""}
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return {"erro": str(e), "elapsed_ms": elapsed_ms, "resposta": ""}
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "resposta": str(raw.get("response", "")),
        "elapsed_ms": elapsed_ms,
        "total_duration_ns": raw.get("total_duration"),
        "eval_count": raw.get("eval_count"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--modelos",
        default=",".join(DEFAULT_MODELS),
        help="Lista separada por virgula",
    )
    parser.add_argument(
        "--out",
        default="_DEVELOPER/IA_DIAG_V2/reports/fase_b_raw.json",
    )
    args = parser.parse_args()
    modelos = [m.strip() for m in args.modelos.split(",") if m.strip()]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    resultado: dict[str, object] = {
        "executado_em": datetime.now(UTC).isoformat(),
        "ollama_url": OLLAMA_URL,
        "modelos": modelos,
        "runs": [],
    }

    for modelo in modelos:
        for pid, pergunta in PERGUNTAS.items():
            print(f"[{modelo}] {pid}...", flush=True)
            run = _gerar(modelo, pergunta)
            resultado["runs"].append(
                {
                    "modelo": modelo,
                    "pergunta_id": pid,
                    "pergunta": pergunta,
                    **run,
                }
            )
            out_path.write_text(
                json.dumps(resultado, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    print(f"OK -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
