#!/usr/bin/env bash
# run_api.sh: FastAPI 서버 실행 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export APP_ENV="${APP_ENV:-dev}"
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${PROJECT_ROOT}/.venv}"
export FASTAPI_SERVER_PORT="${FASTAPI_SERVER_PORT:-8000}"

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

if [[ ! "${FASTAPI_SERVER_PORT}" =~ ^[0-9]+$ ]]; then
  echo "[run_api] 오류: FASTAPI_SERVER_PORT는 숫자여야 합니다. (입력값: ${FASTAPI_SERVER_PORT})"
  exit 2
fi

if (( FASTAPI_SERVER_PORT < 1 || FASTAPI_SERVER_PORT > 65535 )); then
  echo "[run_api] 오류: FASTAPI_SERVER_PORT는 1~65535 범위여야 합니다. (입력값: ${FASTAPI_SERVER_PORT})"
  exit 2
fi

echo "🌐 FastAPI 서버 실행 (APP_ENV=${APP_ENV}, port=${FASTAPI_SERVER_PORT})"
"${UV_BIN}" run uvicorn app.main:app --reload --host 0.0.0.0 --port "${FASTAPI_SERVER_PORT}"
