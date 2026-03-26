#!/usr/bin/env bash
# init.sh: 로컬 개발 환경 초기화 및 서버 기동 스크립트

echo "🚀 [1/3] 의존성 패키지 동기화 (uv sync)..."
uv sync

echo "🧪 [2/3] 베이스라인 구조 및 에이전트 하네스 테스트 (Pytest & Ruff)..."
uv run ruff check .
uv run ruff format .
uv run pytest tests/ -v

echo "🌐 [3/3] 로컬 API 서버 구동 (포트 8000)..."
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
