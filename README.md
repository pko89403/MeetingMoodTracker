# MeetingMoodTracker

회의 대화 데이터를 분석해 **주제(topic)**, **감정 분포(sentiment)**, **정서/회의 시그널(emotion & meeting signals)** 을 추출하고, 프로젝트-회의-화자-발화 단위로 저장/조회할 수 있는 서비스입니다.  
백엔드는 **FastAPI + Azure OpenAI**, 프론트엔드는 **React + Vite**, 운영/검증용 보조 UI는 **Streamlit**으로 구성되어 있습니다.

## 주요 기능

- 회의록 전체 분석: `POST /api/v1/analyze`
- 분석 과정 추적: `POST /api/v1/analyze/inspect`
- SSE 스트리밍 로그 확인: `POST /api/v1/analyze/inspect/stream`
- 단일 발화 감정 분류: `POST /api/v1/sentiment/turn`
- 프로젝트/회의 기준 발화 저장: `POST /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`
- 저장된 회의 overview / turns / agents 조회
- 한국어 및 한/영 혼합 발화 중심 분석

## 저장소 구성

```text
.
├── backend/                # FastAPI API, 분석 서비스, 테스트, Streamlit UI
├── frontend/               # React/Vite 대시보드
├── data/                   # 프로젝트/회의/화자/발화 JSON 저장소(실행 중 생성)
├── docs/                   # 아키텍처/운영/환경설정 문서
├── scripts/                # worktree setup, pre-commit 등 운영 스크립트
├── feature_list.json       # 기능 진행 상태
└── init.sh                 # 로컬 초기 셋업 가이드 스크립트
```

## 기술 스택

### Backend

- Python 3.12
- FastAPI / Uvicorn
- Pydantic
- Azure OpenAI (`openai` SDK)
- uv
- pytest / Ruff

### Frontend

- React 18
- Vite
- Material UI
- Radix UI
- Recharts

## 빠른 시작

### 1) 필수 준비

- Python 3.12+
- Node.js / npm
- `uv`
- Azure OpenAI 사용 가능 환경

### 2) 환경 변수 준비

백엔드는 `backend/example.env`를 템플릿으로 사용합니다.

```bash
cp backend/example.env backend/dev.env
```

필수 값:

- `LLM_API_KEY`
- `LLM_ENDPOINT`
- `LLM_MODEL_NAME`
- `LLM_DEPLOYMENT_NAME`

자세한 설명은 `docs/ENVIRONMENT_GUIDE.md`를 참고하세요.

### 3) 로컬 실행

#### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 문서: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/healthz`

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

- 기본 개발 서버: `http://localhost:5173`
- 백엔드와 함께 사용할 때는 `http://localhost:8000`이 열려 있어야 합니다.

#### Streamlit 분석 콘솔

```bash
cd backend
./scripts/run_ui.sh
```

- 기본 주소: `http://localhost:8501`
- `ANALYZE_API_BASE_URL` 기본값: `http://localhost:8000`

### 4) Docker로 함께 실행

저장소 루트에서 실행합니다.

```bash
docker compose -f docker-compose.dev.yml up --build
```

실행 후:

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## 주요 API

### 회의록 전체 분석

`POST /api/v1/analyze`

```json
{
  "meeting_id": "meeting-001",
  "text": "오늘 배포 일정과 QA 리스크를 점검합시다."
}
```

### 분석 과정 포함 응답

`POST /api/v1/analyze/inspect`

- 최종 결과와 함께 내부 단계/로그를 반환합니다.

### 분석 과정 SSE 스트림

`POST /api/v1/analyze/inspect/stream`

- `start`, `log`, `result`, `done`, `error` 이벤트를 순차적으로 전달합니다.

### 단일 발화 감정 분류

`POST /api/v1/sentiment/turn`

```json
{
  "meeting_id": "meeting-001",
  "turn_id": "turn-014",
  "utterance_text": "이 방향이면 일정은 맞출 수 있을 것 같습니다."
}
```

### 프로젝트/회의 기준 발화 저장

`POST /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`

```json
{
  "agent_id": "alice",
  "turn_id": "turn-001",
  "utterance_text": "회귀 테스트가 아직 남아 있습니다.",
  "order": 1
}
```

관련 조회 API:

- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}`
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/agents`
- `GET /api/v1/env`
- `GET /healthz`

## 데이터 저장 구조

발화 저장은 현재 DB가 아닌 JSON 기반 계층 저장소를 사용합니다.

```text
data/
  projects/
    {project_id}/
      meta.json
      meetings/
        {meeting_id}/
          meta.json
          agents/
            {agent_id}/
              turns.json
```

식별자 기준은 `project_id + meeting_id + agent_id + turn_id` 조합입니다.

## 개발자용 명령어

### Worktree 셋업

```bash
./scripts/setup_worktree.sh
```

### 전체 초기 확인

```bash
./init.sh
```

### Backend 품질 확인

```bash
cd backend
uv run ruff check .
uv run pytest tests/ -v
```

### Frontend 빌드

```bash
cd frontend
npm run build
```

### 데모 회의 데이터 시드

```bash
cd backend
uv run python scripts/seed_issue27_demo_meeting.py
```

## 참고 문서

- `docs/ARCHITECTURE.md`
- `docs/DESIGN.md`
- `docs/ENVIRONMENT_GUIDE.md`
- `docs/AGENT_OPERATIONS_GUIDE.md`
- `backend/README.md`
- `frontend/README.md`

## 운영 시 유의사항

- Azure OpenAI 방화벽/네트워크 정책이 허용되어야 합니다.
- 일부 민감 표현은 Azure Content Filter 정책으로 차단될 수 있습니다.
- 분석/운영 문구는 한국어 사용자 경험을 기본으로 설계되어 있습니다.
