#!/usr/bin/env bash
# run_api.sh: FastAPI 서버 실행 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export APP_ENV="${APP_ENV:-dev}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${PROJECT_ROOT}/.venv}"

if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [[ -x "${HOME}/.local/bin/uv" ]]; then
  UV_BIN="${HOME}/.local/bin/uv"
elif [[ -x "/opt/homebrew/bin/uv" ]]; then
  UV_BIN="/opt/homebrew/bin/uv"
else
  echo "[run_api] 오류: uv 실행 파일을 찾을 수 없습니다."
  exit 127
fi

echo "🌐 FastAPI 서버 실행 (APP_ENV=${APP_ENV}, port=8000)"
"${UV_BIN}" run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
