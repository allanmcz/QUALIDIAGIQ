#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MODEL_NAME="${QDI_OLLAMA_MODEL:-qdi-assistant}"

FULL_CONTEXT=0

if [ "${1:-}" = "--full" ]; then
  FULL_CONTEXT=1
  shift
fi

if [ "$#" -eq 0 ]; then
  echo "Uso: .ollama/scripts/ask_qdi.sh [--full] \"sua pergunta\"" >&2
  exit 1
fi

QUESTION="$*"

CONTEXT_FILES=(
  "${PROJECT_ROOT}/.ollama/context/qdi_context.md"
  "${PROJECT_ROOT}/.ollama/context/architecture.md"
  "${PROJECT_ROOT}/.ollama/context/coding_rules.md"
)

FULL_CONTEXT_FILES=(
  "${PROJECT_ROOT}/AGENTS.md"
)

DOC_REFS=(
  "${PROJECT_ROOT}/docs/refs/00_INDICE.md"
  "${PROJECT_ROOT}/docs/refs/01_PRD_BASE.md"
  "${PROJECT_ROOT}/docs/refs/02_MOSCOW_FEATURES.md"
  "${PROJECT_ROOT}/docs/refs/03_GAP_ANALYSIS.md"
  "${PROJECT_ROOT}/docs/refs/06_MATRIZ_COMPETITIVA.md"
)

build_context() {
  local files=("${CONTEXT_FILES[@]}")

  if [ "${FULL_CONTEXT}" -eq 1 ]; then
    files+=("${FULL_CONTEXT_FILES[@]}" "${DOC_REFS[@]}")
  fi

  for file in "${files[@]}"; do
    if [ -f "${file}" ]; then
      printf '\n\n===== %s =====\n\n' "${file#"${PROJECT_ROOT}/"}"
      sed -n '1,160p' "${file}"
    fi
  done
}

PROMPT="$(cat <<EOF
Voce esta respondendo dentro do projeto QualiDiagIQ (QDI).

Use o contexto abaixo como memoria do projeto. Se a pergunta depender de documento ausente ou requisito ambiguo, informe a lacuna e pergunte antes de assumir.

Modo de contexto: $([ "${FULL_CONTEXT}" -eq 1 ] && echo "completo" || echo "enxuto")

$(build_context)

Pergunta do Allan:
${QUESTION}
EOF
)"

ollama run "${MODEL_NAME}" "${PROMPT}"
