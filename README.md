# Meeting Mood Tracker

한국어 | [English](./README.en.md)

![Meeting Mood Tracker 로고](./frontend/public/brand/meeting-mood-tracker-lockup.png)

Meeting Mood Tracker는 회의 발화 데이터를 `프로젝트 → 회의 → 에이전트 → 발화 턴` 구조로 저장하고, 감정 흐름과 회의 시그널을 분석·시각화하는 conversation intelligence 저장소입니다. 백엔드는 FastAPI와 Azure OpenAI 기반 분석 파이프라인을 제공하고, 프론트엔드는 React Flow 및 Timeline UI로 회의 흐름을 탐색할 수 있게 구성되어 있습니다.

## Why This Repo

- 회의 전체 요약뿐 아니라 턴 단위 감정 흐름과 agent 패턴까지 추적합니다.
- project-aware 저장 모델을 통해 회의 데이터를 누적하고 조회 API로 재사용할 수 있습니다.
- 한국어 중심 회의 데이터와 한/영 혼합 발화(code-switching)를 기본 시나리오로 다룹니다.
- 분석 결과, inspect 디버깅 경로, 시각화 UI가 하나의 흐름으로 연결됩니다.

## Highlights

- `POST /api/v1/analyze`
  - 회의록 전체를 topic / sentiment / emotion / correlation로 분석합니다.
- `POST /api/v1/analyze/inspect`, `POST /api/v1/analyze/inspect/stream`
  - 분석 단계와 로그를 REST/SSE로 추적합니다.
- `POST /api/v1/sentiment/turn`
  - 단일 발화(turn)에 대한 감정 라벨과 confidence를 반환합니다.
- `POST /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`
  - project-aware 저장 경로로 turn 분석 결과를 저장합니다.
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}`
  - 회의 overview 집계를 반환합니다.
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`
  - timeline/detail 패널용 turn 목록을 반환합니다.
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/agents`
  - agent aggregate와 패턴 요약을 반환합니다.
- React Flow 보드 + Timeline 페이지
  - 회의 관계도와 감정 시계열을 각각의 화면에서 탐색합니다.

## Tech Stack

- Backend: FastAPI, Pydantic, Python 3.12, uv
- LLM: Azure OpenAI, structured output(JSON schema)
- Frontend: React, Vite, Tailwind, React Flow, ApexCharts
- Storage: JSON repository 기반 project-aware 저장 구조
- Quality Gate: custom harness, Ruff, Pytest, Playwright

## Repository Layout

- `backend/`
  - FastAPI 서버, 분석 서비스, 저장소, 테스트, Streamlit inspect UI
- `frontend/`
  - React 기반 대시보드, Flow 보드, Timeline UI
- `docs/`
  - 아키텍처, 설계 원칙, 환경 설정, 운영 가이드
- `data/`
  - project-aware JSON 저장 데이터
- `scripts/`
  - worktree setup, pre-commit 보조 스크립트
- `frontend/public/brand/`
  - 로고, 파비콘 등 브랜드 자산

## Quick Start

### Prerequisites

- Python `3.12+`
- `uv`
- Node.js `18+`
- Azure OpenAI 접근 정보
- 선택: Docker / Docker Compose

### 1. 환경 변수 준비

```bash
cp backend/example.env backend/dev.env
```

`backend/dev.env`에 아래 값을 채웁니다.

- `LLM_API_KEY`
- `LLM_ENDPOINT`
- `LLM_MODEL_NAME`
- `LLM_DEPLOYMENT_NAME`
- 선택: `LLM_API_VERSION`, `LLM_MODEL_VERSION`

자세한 규칙은 [`docs/ENVIRONMENT_GUIDE.md`](./docs/ENVIRONMENT_GUIDE.md)를 참조하세요.

### 2. worktree / 로컬 환경 준비

```bash
./scripts/setup_worktree.sh
```

이 스크립트는 worktree 전용 `.venv`를 준비하고 feature-issue 동기화까지 수행합니다.

### 3. 백엔드 실행

```bash
./backend/scripts/run_api.sh
```

- 기본 포트: `8000`
- health check: `http://localhost:8000/healthz`

### 4. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`으로 접속합니다.

### 5. 빠른 검증

```bash
curl http://localhost:8000/healthz
```

정상 응답 예시:

```json
{"status":"ok"}
```

## Docker Development

로컬 개발용 Docker Compose는 루트의 `docker-compose.dev.yml`을 사용합니다.

```bash
docker compose -f docker-compose.dev.yml up --build
```

기본 포트:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

상위 리포지토리에서 서브모듈로 사용할 경우 템플릿은 [`docs/templates/docker-compose.parent.api.yml`](./docs/templates/docker-compose.parent.api.yml)을 참고하세요.

## Development Workflow

### 전체 초기화 + 기본 검증

```bash
./init.sh
```

이 스크립트는 다음을 순서대로 수행합니다.

- backend `uv sync`
- backend `ruff`, `pytest`
- frontend 의존성 설치
- 개발 서버 실행 가이드 출력

### 자주 쓰는 명령어

```bash
# backend lint
cd backend && uv run ruff check .

# backend test
cd backend && uv run pytest tests/ -v

# frontend build
cd frontend && npm run build

# issue sync
cd backend && uv run python scripts/sync_feature_issues.py

# Streamlit inspect UI
./backend/scripts/run_ui.sh
```

## API Overview

루트 README는 입문용 개요만 제공합니다. 자세한 스키마와 분석 항목은 아래 문서를 참고하세요.

- [`backend/README.md`](./backend/README.md)
- [`docs/DESIGN.md`](./docs/DESIGN.md)
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)

핵심 엔드포인트만 빠르게 보면:

- `GET /healthz`
- `POST /api/v1/analyze`
- `POST /api/v1/analyze/inspect`
- `POST /api/v1/analyze/inspect/stream`
- `POST /api/v1/sentiment/turn`
- `POST /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}`
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/agents`

## Documentation Map

- [`docs/REPOSITORY_DETAIL.md`](./docs/REPOSITORY_DETAIL.md)
  - GitHub About / 저장소 소개문 초안
- [`docs/ENVIRONMENT_GUIDE.md`](./docs/ENVIRONMENT_GUIDE.md)
  - `dev.env`, `prod.env`, `APP_ENV` 운영 규칙
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)
  - 계층 구조, 저장 모델, 조회/분석 흐름
- [`docs/DESIGN.md`](./docs/DESIGN.md)
  - 도메인 목표와 API 설계 원칙
- [`docs/AGENT_OPERATIONS_GUIDE.md`](./docs/AGENT_OPERATIONS_GUIDE.md)
  - agent/workflow 운영 규칙
- [`docs/QUALITY_SCORE.md`](./docs/QUALITY_SCORE.md)
  - harness / lint / validator 기준

## Operational Notes

- Azure OpenAI 방화벽 정책이 허용되어 있어야 실제 LLM 호출이 동작합니다.
- 자해/자살/혐오 표현 등은 Azure Content Filter로 인해 `502`가 발생할 수 있습니다.
- 저장소 전반의 문서와 운영 문구는 한국어 우선 원칙을 따릅니다.

## Contributing Notes

- 새로운 worktree나 세션에서는 먼저 `./scripts/setup_worktree.sh`를 실행하세요.
- 기능 구현은 `feature_list.json`의 현재 목표와 GitHub issue 동기화 규칙을 따릅니다.
- 아키텍처나 기능 계약이 바뀌면 `README.md`와 `docs/`를 함께 갱신해야 합니다.
