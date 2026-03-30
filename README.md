# Meeting Mood Tracker

A FastAPI-based application that analyzes meeting transcripts to identify discussion topics and sentiment distribution. Built strictly with Specification-Driven Development (SDD) principles.

## 한국어 우선 개발 가이드

- 본 프로젝트는 한국어 사용자/개발자 경험을 기본값으로 둡니다.
- 회의 발화 입력은 한국어를 우선 지원하며, 한/영 혼합 발화도 지원합니다.
- 코드 식별자는 영어를 유지하고, 문서/설명/docstring은 한국어 중심으로 관리합니다.

## Codex Worktree Setup

- worktree별 가상환경은 프로젝트 루트의 `.venv`를 사용합니다.
- setup script(`scripts/setup_worktree.sh`)는 `UV_PROJECT_ENVIRONMENT=.venv`를 강제합니다.
- 패키지 설치 캐시는 `UV_CACHE_DIR`(기본 `~/.cache/uv`)를 재사용해 설치 비용을 줄입니다.
- Codex 환경 등록은 `.codex/environments/environment.toml`의 `[setup].script`를 사용합니다.
- setup script는 현재 worktree에 `dev.env`/`prod.env`가 없을 때 `main` worktree에서 자동 복사합니다.
- setup script는 `uv` 바이너리 경로를 `PATH`에 선반영해 pre-commit 훅에서도 동일 실행 환경을 유지합니다.
- `dev.env`, `prod.env`는 로컬 전용 파일이며 Git에 커밋하지 않습니다.
- setup 시 `scripts/sync_feature_issues.py`가 자동 실행되어 `feature_list.json`과 GitHub Issue를 동기화합니다.
- `GITHUB_TOKEN`이 없으면 `gh auth token`을 사용해 토큰을 자동 확보합니다(로그인된 경우).
- 동기화를 건너뛰려면 `SKIP_FEATURE_ISSUE_SYNC=1 ./scripts/setup_worktree.sh`로 실행합니다.

## Codex IDE Actions

- `FastAPI 실행`: `FASTAPI_SERVER_PORT=18000 ./scripts/run_api.sh`
- `Streamlit 실행`: `./scripts/run_ui.sh`

## Parent Compose 기반 Docker 실행 (서브모듈 대상)

- 이 저장소는 `docker-compose.yml`을 직접 제공하지 않고, 상위 리포지토리에서 포함할 템플릿을 제공합니다.
- 템플릿 위치: `docs/templates/docker-compose.parent.api.yml`
- 기본 환경변수:
  - `APP_ENV` (기본값: `dev`, `dev.env`/`prod.env` 선택)
  - `FASTAPI_SERVER_PORT` (기본값: `8000`)
  - `MEETING_MOOD_TRACKER_SUBMODULE_PATH` (기본값: `./MeetingMoodTracker`)
- 상위 리포지토리에서 사용할 때는 템플릿 내용을 상위 `docker-compose.yml`에 반영하거나 include하여 사용합니다.
- 템플릿은 `APP_ENV` 값에 맞춰 `${APP_ENV}.env`를 `env_file`과 컨테이너 내부 `/app/${APP_ENV}.env`에 함께 연결합니다.

대표 실행 예시(상위 리포지토리 루트 기준):

```bash
export APP_ENV=dev
export FASTAPI_SERVER_PORT=18000
export MEETING_MOOD_TRACKER_SUBMODULE_PATH=./MeetingMoodTracker
docker compose up --build
```

`prod` 실행 예시:

```bash
export APP_ENV=prod
export FASTAPI_SERVER_PORT=18000
export MEETING_MOOD_TRACKER_SUBMODULE_PATH=./MeetingMoodTracker
docker compose up --build
```

검증:
- 브라우저에서 `http://localhost:${FASTAPI_SERVER_PORT}/docs` 접근

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
  - `LLM_API_VERSION` (optional, Azure OpenAI API version)
  - `LLM_MODEL_VERSION` (optional, 모델 메타데이터 및 API version fallback)
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

## Topic Extraction Logic

- Analyze는 LLM 기반 2-stage 파이프라인으로 동작합니다.
  - Stage 1: `extract_topics_with_llm` (JSON structured `topics: string[]`, `reasoning_effort=none`)
  - Stage 2: `analyze_sentiment_with_llm` (JSON structured `sentiment.positive/negative/neutral`, `reasoning_effort=minimal`)
- Stage 2는 Stage 1의 topic 리스트와 원문 텍스트를 함께 입력으로 사용합니다.
- 최종 `topic` 응답값은 topic 리스트를 `", "`로 결합한 문자열입니다.
- 최종 `sentiment`는 아래 구조를 사용합니다.
  - `sentiment.positive.confidence`
  - `sentiment.negative.confidence`
  - `sentiment.neutral.confidence`
- 각 confidence는 정수 퍼센트(`0~100`)이며, 세 값의 합은 서버에서 항상 `100`으로 정규화됩니다.
- 두 단계 중 하나라도 LLM 호출/파싱/스키마 검증에 실패하면 `/api/v1/analyze`와 `/api/v1/analyze/inspect`는 `502`를 반환합니다.

## Streamlit 테스트 UI

- 실행 전제:
  - FastAPI 서버 실행: `FASTAPI_SERVER_PORT=8000 ./scripts/run_api.sh`
- Streamlit 실행:
  - `./scripts/run_ui.sh`
  - 또는 `ANALYZE_API_BASE_URL=http://localhost:8000 uv run streamlit run app/ui/analyze_console.py`
- UI 동작:
  - 기본 모드: SSE(`/api/v1/analyze/inspect/stream`) 사용
  - SSE 모드에서 `log` 이벤트 수신 즉시 실행 로그/결과 미리보기를 화면에 실시간 갱신
  - 실패 시 fallback: inspect REST(`/api/v1/analyze/inspect`)
  - `화면 Clear`: 현재 표시 중인 결과/에러를 초기화
  - `히스토리 삭제`: 저장된 요청 히스토리를 전체 삭제
  - 요청 성공 시 최신 30건 히스토리 자동 저장 및 재조회(`표시할 결과 선택`)

## 운영 시 유의사항

- Azure OpenAI 리소스 네트워크 정책(VNet/Firewall)이 닫혀 있으면 감정분류 호출이 실패합니다.
- 자해/자살 관련 문구 등은 Azure Content Filter 정책에 의해 차단될 수 있습니다.
- Azure API 버전은 `LLM_API_VERSION`을 우선 사용하고, 미설정 시에만 `LLM_MODEL_VERSION`으로 fallback합니다.

Use `example.env` as the template. Keep `dev.env` and `prod.env` local only.

## LLM-as-Judge Offline Evaluation

- Script: `scripts/evaluate_sentiment_with_judge.py`
- Input: JSONL with `utterance_text`, `predicted_label` and optional IDs
- Output: JSON report with agreement rate and per-turn judge rationale

## Feature List <-> GitHub Issue Sync

- Script: `scripts/sync_feature_issues.py`
- Purpose: `feature_list.json`의 기능 항목과 GitHub Issue를 `feature_id` 기준으로 동기화합니다.
- Issue 식별 방식:
  - 본문 마커: `<!-- feature_id:feat_xxx -->`
  - 제목 패턴 fallback: `[feat_xxx] ...`
- 선택 확장 필드(`feature_list.json`):
  - `issue_rule.objective`: 이슈의 작업 목표(문단)
  - `issue_rule.in_scope` / `issue_rule.out_of_scope`: 범위/비범위 항목
  - `issue_rule.implementation_checklist`: 구현 체크리스트
  - `issue_rule.verification`: 검증 시나리오
  - `issue_rule.done_criteria`(또는 `acceptance_criteria`): 완료 조건
- `issue_rule`가 존재하면 신규 Issue 본문 생성 시 위 섹션이 자동 삽입됩니다.

대표 실행 예시:

```bash
# 1) 현재 상태 리포트(dry-run)
uv run python scripts/sync_feature_issues.py --create-missing --sync-state

# 2) 실제 적용(이슈 생성/상태 동기화 + feature_list 메타데이터 기록)
export GITHUB_TOKEN=***REDACTED***
uv run python scripts/sync_feature_issues.py \
  --create-missing \
  --sync-state \
  --write-feature-file \
  --apply
```

주의:
- `--apply`로 GitHub 상태를 변경하려면 `GITHUB_TOKEN`이 필요합니다.
- public repo 조회만 할 때는 토큰 없이 dry-run이 가능합니다.
