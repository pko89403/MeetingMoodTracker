#!/usr/bin/env bash
# Codex worktree 생성 시 실행되는 기본 셋업 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKTREE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export UV_PROJECT_ENVIRONMENT="${WORKTREE_ROOT}/.venv"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${HOME}/.cache/uv}"

if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [[ -x "${HOME}/.local/bin/uv" ]]; then
  UV_BIN="${HOME}/.local/bin/uv"
elif [[ -x "/opt/homebrew/bin/uv" ]]; then
  UV_BIN="/opt/homebrew/bin/uv"
else
  echo "[setup] 오류: uv 실행 파일을 찾을 수 없습니다."
  exit 127
fi

echo "[setup] worktree 가상환경 준비: ${UV_PROJECT_ENVIRONMENT}"
if [[ -f "${UV_PROJECT_ENVIRONMENT}/pyvenv.cfg" ]]; then
  echo "[setup] 기존 가상환경 재사용"
else
  "${UV_BIN}" venv "${UV_PROJECT_ENVIRONMENT}"
fi

echo "[setup] uv 의존성 동기화 시작 (cache: ${UV_CACHE_DIR})"
cd "${WORKTREE_ROOT}"
"${UV_BIN}" sync --locked
echo "[setup] worktree 셋업 완료"
