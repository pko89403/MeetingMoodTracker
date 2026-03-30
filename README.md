# Meeting Mood Tracker

A FastAPI-based application that analyzes meeting transcripts to accurately identify conversation topics and overall participant moods. Built strictly with Specification-Driven Development (SDD) principles.

## 한국어 우선 개발 가이드

- 본 프로젝트는 한국어 사용자/개발자 경험을 기본값으로 둡니다.
- 회의 발화 입력은 한국어를 우선 지원하며, 한/영 혼합 발화도 지원합니다.
- 코드 식별자는 영어를 유지하고, 문서/설명/docstring은 한국어 중심으로 관리합니다.

## Worktree 셋업

- 기본 셋업 스크립트: `scripts/setup_worktree.sh`
- 동작:
  - `UV_PROJECT_ENVIRONMENT=.venv` 기준으로 가상환경 생성/재사용
  - `uv sync --locked`로 의존성 동기화
  - 현재 worktree에 `dev.env`/`prod.env`가 없으면, `main` branch worktree를 찾아 동일 파일을 복사
- 보안 주의:
  - `dev.env`, `prod.env`는 로컬 전용 파일이며 Git에 커밋하지 않습니다.

## Codex IDE Actions

- `FastAPI 실행`: `./scripts/run_api.sh`
- `Streamlit 실행`: `./scripts/run_ui.sh`

## Turn Sentiment API

- Endpoint: `POST /api/v1/sentiment/turn`
- Purpose: classify one meeting turn utterance into:
  - `POS`
  - `NEG`
  - `NEUTRAL`
- Request fields:
  - `meeting_id`
  - `turn_id`
  - `speaker_id` (optional)
  - `utterance_text`
- Response fields:
  - `label`
  - `confidence` (`0.0` - `1.0`)
  - `evidence`

## LLM Environment Config API

- Endpoint: `GET /api/env/v1`
- Reads env file by `APP_ENV`:
  - `APP_ENV=dev` or unset -> `dev.env`
  - `APP_ENV=prod` -> `prod.env`
- Returns raw values:
  - `LLM_API_KEY`
  - `LLM_ENDPOINT`
  - `LLM_MODEL_NAME`
  - `LLM_DEPLOYMENT_NAME`
  - `LLM_MODEL_VERSION` (optional, sentiment service API version source)
- Error behavior:
  - `422` if required keys are missing
  - `500` if env file is missing or `APP_ENV` is invalid
  - 오류 응답 `detail`에는 `error_code`, `message_ko`, `message_en`가 포함됩니다.

## Analyze Inspect APIs

- 기존 유지:
  - `POST /api/v1/analyze` (`AnalyzeRequest -> AnalyzeResponse`)
- 신규 inspect REST:
  - `POST /api/v1/analyze/inspect`
  - 반환: `request_id`, `result`, `logic_steps`, `logs`
- 신규 inspect SSE:
  - `POST /api/v1/analyze/inspect/stream` (`text/event-stream`)
  - 이벤트 순서: `start -> log* -> result -> done` (오류 시 `error`)
- 구현 원칙:
  - `/analyze`와 `/inspect`는 동일한 서비스 메서드 `run_analyze_pipeline`을 호출합니다.
  - analyze 로그는 메모리 링버퍼(`maxlen=200`)에 저장됩니다.

## Streamlit 테스트 UI

- 실행 전제:
  - FastAPI 서버 실행: `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Streamlit 실행:
  - `./scripts/run_ui.sh`
  - 또는 `ANALYZE_API_BASE_URL=http://localhost:8000 uv run streamlit run app/ui/analyze_console.py`
- UI 동작:
  - 기본 모드: SSE(`/api/v1/analyze/inspect/stream`) 사용
  - 실패 시 fallback: inspect REST(`/api/v1/analyze/inspect`)
  - `화면 Clear`: 현재 표시 중인 결과/에러를 초기화
  - `히스토리 삭제`: 저장된 요청 히스토리를 전체 삭제
  - 요청 성공 시 최신 30건 히스토리 자동 저장 및 재조회(`표시할 결과 선택`)

## 운영 시 유의사항

- Azure OpenAI 리소스 네트워크 정책(VNet/Firewall)이 닫혀 있으면 감정분류 호출이 실패합니다.
- 자해/자살 관련 문구 등은 Azure Content Filter 정책에 의해 차단될 수 있습니다.

Use `example.env` as the template. Keep `dev.env` and `prod.env` local only.

## LLM-as-Judge Offline Evaluation

- Script: `scripts/evaluate_sentiment_with_judge.py`
- Input: JSONL with `utterance_text`, `predicted_label` and optional IDs
- Output: JSON report with agreement rate and per-turn judge rationale
