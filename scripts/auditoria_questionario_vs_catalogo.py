#!/usr/bin/env python3
"""
Compara códigos de pergunta no catálogo JSON com os citados no PRD do questionário (P4).

Uso (na raiz do repositório):
    PYTHONPATH=. python scripts/auditoria_questionario_vs_catalogo.py
    PYTHONPATH=. python scripts/auditoria_questionario_vs_catalogo.py --write-doc

Camada: ferramenta de desenvolvimento (não importada pela API).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "src/infrastructure/questionario/data/perguntas_mvp.json"
MD_PATH = ROOT / "docs/refs/05_QUESTIONARIO_v1.md"
DOC_OUT = ROOT / "docs/operacao/auditoria_catalogo_vs_pr_v1_2026-05-01.md"

# Códigos alfanuméricos Q-SEG-NNN (trilha canônica do QDI).
CODE_RE = re.compile(r"\b(Q-[A-Z]+-\d{3})\b")


def _load_json_codes() -> tuple[str, set[str]]:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    versao = str(data.get("versao_catalogo", "unknown"))
    codes: set[str] = set()
    for item in data.get("perguntas", []):
        c = item.get("codigo")
        if isinstance(c, str):
            codes.add(c)
    return versao, codes


def _load_md_codes() -> set[str]:
    text = MD_PATH.read_text(encoding="utf-8")
    return set(CODE_RE.findall(text))


def _render_markdown(
    versao: str,
    n_json: int,
    n_md: int,
    only_json: set[str],
    only_md: set[str],
    inter: set[str],
) -> str:
    lines = [
        "# Auditoria catálogo JSON x PRD do questionário (P4)",
        "",
        "> **Gerado por:** `scripts/auditoria_questionario_vs_catalogo.py`",
        "> **Catálogo:** `versao_catalogo = " + versao + "` (`perguntas_mvp.json`).",
        "> **PRD:** `docs/refs/05_QUESTIONARIO_v1.md` (códigos extraídos por regex `Q-SEG-NNN`).",
        "",
        "## Contagens",
        "",
        "| Fonte | Quantidade de códigos únicos |",
        "|---|---:|",
        f"| JSON (catálogo completo) | {n_json} |",
        f"| Markdown PRD (ocorrências de código) | {n_md} |",
        f"| Interseção | {len(inter)} |",
        "",
        (
            "## Nota 35 x 37\n\n"
            "O PRD descreve **21 núcleo + 9 setoriais + 5 avançadas Lucro Real = 35** perguntas "
            "no desenho pedagógico. O catálogo runtime **`"
            + versao
            + "`** contém **37** perguntas (inclui ramificações setoriais/versionamento MVP). "
            "Não é inconsistência de código — é **escopo documental** vs **catálogo materializado**. "
            "Ver também `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` — auditoria formal **37x35**.\n"
        ),
        "",
        "## Divergências",
        "",
    ]
    if only_json:
        lines.append("### Só no JSON (não encontrados no markdown PRD)")
        lines.extend(f"- `{c}`" for c in sorted(only_json))
        lines.append("")
    else:
        lines.append("### Só no JSON")
        lines.append("*Nenhum.*")
        lines.append("")

    if only_md:
        lines.append("### Só no markdown PRD (não estão no JSON)")
        lines.extend(f"- `{c}`" for c in sorted(only_md))
        lines.append("")
    else:
        lines.append("### Só no markdown PRD")
        lines.append("*Nenhum.*")
        lines.append("")

    if only_json or only_md:
        lines.append(
            "**Ação sugerida:** alinhar doc ou catálogo numa sprint dedicada (não automático)."
        )
    else:
        lines.append(
            "**Resultado:** conjuntos de códigos **idênticos** entre JSON e extração do PRD."
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-doc",
        action="store_true",
        help=f"Grava {DOC_OUT.relative_to(ROOT)} com o relatório.",
    )
    args = parser.parse_args()

    if not JSON_PATH.is_file():
        print("ERRO: JSON não encontrado:", JSON_PATH, file=sys.stderr)
        return 2
    if not MD_PATH.is_file():
        print("ERRO: Markdown PRD não encontrado:", MD_PATH, file=sys.stderr)
        return 2

    versao, json_codes = _load_json_codes()
    md_codes = _load_md_codes()
    inter = json_codes & md_codes
    only_json = json_codes - md_codes
    only_md = md_codes - json_codes

    print(f"versao_catalogo: {versao}")
    print(
        f"JSON: {len(json_codes)} códigos | MD: {len(md_codes)} códigos | interseção: {len(inter)}"
    )
    if only_json:
        print("Só JSON:", ", ".join(sorted(only_json)))
    if only_md:
        print("Só MD: ", ", ".join(sorted(only_md)))
    if not only_json and not only_md:
        print("OK — conjuntos coincidentes.")

    if args.write_doc:
        DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
        body = _render_markdown(
            versao,
            len(json_codes),
            len(md_codes),
            only_json,
            only_md,
            inter,
        )
        DOC_OUT.write_text(body, encoding="utf-8")
        print("Escrito:", DOC_OUT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
