#!/usr/bin/env bash
# run_ui.sh: Streamlit Analyze Inspect 테스트 콘솔 실행 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export ANALYZE_API_BASE_URL="${ANALYZE_API_BASE_URL:-http://localhost:8000}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${PROJECT_ROOT}/.venv}"

if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [[ -x "${HOME}/.local/bin/uv" ]]; then
  UV_BIN="${HOME}/.local/bin/uv"
elif [[ -x "/opt/homebrew/bin/uv" ]]; then
  UV_BIN="/opt/homebrew/bin/uv"
else
  echo "[run_ui] 오류: uv 실행 파일을 찾을 수 없습니다."
  exit 127
fi

echo "🌐 Streamlit UI 실행 (ANALYZE_API_BASE_URL=${ANALYZE_API_BASE_URL})"
"${UV_BIN}" run streamlit run app/ui/analyze_console.py
