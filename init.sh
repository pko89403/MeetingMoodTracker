#!/usr/bin/env bash
# init.sh: 로컬 개발 환경 초기화 및 서버 기동 스크립트

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "🚀 [1/4] Backend: 의존성 패키지 동기화 (uv sync)..."
cd "${SCRIPT_DIR}/backend"
uv sync

echo "🧪 [2/4] Backend: 하네스 테스트 (Pytest & Ruff)..."
uv run ruff check .
uv run ruff format .
uv run pytest tests/ -v

echo "========================================="
echo "🚀 [3/4] Frontend: 의존성 패키지 설치 (npm/pnpm/yarn)..."
cd "${SCRIPT_DIR}/frontend"
if command -v pnpm >/dev/null 2>&1; then
    pnpm install
elif command -v yarn >/dev/null 2>&1; then
    yarn install
else
    npm install
fi

echo "========================================="
echo "🌐 [4/4] 개발 서버 구동 안내"
echo "- Backend: cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "- Frontend: cd frontend && npm run dev"
echo "========================================="
