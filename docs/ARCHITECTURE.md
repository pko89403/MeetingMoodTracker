# MeetingMoodTracker Architecture

## System Diagram
MeetingMoodTracker는 인간의 언어로 된 룰이 아닌 "기계적인 하네스"를 통해 코딩 품질을 강제합니다.

### 1. Harness Layer (에이전트 제어 및 검증)

- **Agent Runner (`harness/runner/`)**: `architecture -> fastapi-contract -> linter -> pytest` 순서로 검증하며, pre-commit에서는 `--mode precommit`으로 빠른 로컬 게이트를 수행합니다.
- **Structural Validators (`harness/validators/`)**: AST(Abstract Syntax Tree) 분석을 통해, 허가되지 않은 모듈 간의 의존성 수입을 차단합니다.
- **FastAPI Contract Validator (`harness/validators/fastapi_contract_checker.py`)**: runtime 라우트의 반환 타입, `response_model`, Pydantic I/O 경로(`app/types`) 준수 여부를 강제하며, 허용 경로의 SSE(`text/event-stream`)만 제한적으로 예외 허용합니다.
- **Custom Linters (`harness/linter/`)**: 에이전트가 작성한 파이썬 코드의 타입 힌트, 들여쓰기 컨벤션을 강제합니다.

### 2. Application Layer (FastAPI 서버 - 6단 고정 계층)
비즈니스 도메인은 에이전트의 구조 침해를 원천 차단하기 위해 아래와 같이 엄격한 고정 계층으로 분리됩니다.

- **`app/types/`**: (최하위) 비즈니스 엔티티 및 Pydantic 데이터 스키마
- **`app/config/`**: 전역 설정 및 환경변수
- **`app/repo/`**: 데이터베이스 접근 및 로컬 캐시 등 영속성 계층
- **`app/service/`**: 코어 비즈니스 로직 및 외부 연동 레이어
- **`app/runtime/`**: FastAPI 컨트롤러 및 API 엔드포인트
- **`app/ui/`**: (최상위) 프론트엔드 연동 및 템플릿 서빙
- **`app/main.py`**: 단지 서버를 구동(Boot)하는 진입점 모듈

### LLM Config Read Flow

- `app/runtime/env_config.py`의 `GET /api/env/v1` 라우트가 진입점입니다.
- `app/service/llm_config_service.py`가 필수 키(`LLM_API_KEY`, `LLM_ENDPOINT`, `LLM_MODEL_NAME`, `LLM_DEPLOYMENT_NAME`) 검증 및 오류 분기(422/500)를 담당합니다.
- `app/config/llm_env.py`가 `APP_ENV(dev|prod)` 기준 env 파일(`dev.env`/`prod.env`)을 선택하고 로드합니다.

### Turn Sentiment Classification Flow

- `app/runtime/sentiment.py`의 `POST /api/v1/sentiment/turn`가 감정 분류 요청 진입점입니다.
- `app/service/sentiment_service.py`가 OpenAI Python SDK의 `AzureOpenAI` 클라이언트를 구성합니다.
- 호출 규약:
  - `chat.completions.create(model=LLM_DEPLOYMENT_NAME, response_format={"type":"json_schema", ...})`
  - API Version: `LLM_MODEL_VERSION`을 우선 사용, 없으면 기본값 `2025-04-01-preview`
- 분류 결과는 `app/types/sentiment.py`의 `TurnSentimentResponse`로 검증 후 반환됩니다.

### Analyze Inspect Flow (REST + SSE)

- `app/service/analyze_service.py`의 `run_analyze_pipeline`이 `/analyze`, `/analyze/inspect`, `/analyze/inspect/stream`이 공통으로 호출하는 단일 알고리즘 메서드입니다.
- `run_analyze_pipeline`은 2-stage LLM 파이프라인을 사용합니다.
  - Stage 1: `extract_topics_with_llm` (`topics: string[]`, `reasoning_effort=none`)
  - Stage 2: `analyze_sentiment_with_llm` (`sentiment.positive/negative/neutral`, `reasoning_effort=minimal`)
  - Stage 2 입력은 원문 텍스트 + Stage 1 topics를 함께 사용합니다.
  - 최종 `topic`은 topics를 `", "`로 결합한 문자열입니다.
  - 최종 `sentiment`는 정수 퍼센트 3축으로 정규화되며(`positive/negative/neutral`), 합계 100을 보장합니다.
- `POST /api/v1/analyze`:
  - 공통 파이프라인 결과에서 `AnalyzeResponse`만 반환해 기존 계약을 유지합니다.
  - LLM 추론 실패 시 `502` (`ANALYZE_LLM_FAILURE`)를 반환합니다.
- `POST /api/v1/analyze/inspect`:
  - 공통 파이프라인 결과에서 `request_id`, `logic_steps`, `logs`, `result`를 함께 반환합니다.
  - LLM 추론 실패 시 `502` (`ANALYZE_LLM_FAILURE`)를 반환합니다.
- `POST /api/v1/analyze/inspect/stream`:
  - 공통 파이프라인 결과를 `start -> log* -> result -> done` SSE 이벤트로 변환해 전달합니다.
- analyze 실행 로그는 서비스 레이어의 메모리 링버퍼(`maxlen=200`)에도 저장됩니다.
- Streamlit UI(`app/ui/analyze_console.py`)는 기본적으로 SSE 경로를 사용하고, 실패 시 REST inspect 경로로 폴백합니다.

## Dependency Rules (단방향 헌법)

- 모듈 의존성은 반드시 **`Types <- Config <- Repo <- Service <- Runtime <- UI`** 의 단방향 논리로만 흘러야 합니다.
- (예: `service`는 `types`, `config`, `repo` 레이어를 자유롭게 의존할 수 있지만, `runtime`이나 `ui` 모듈을 절대 임포트해서는 안 됩니다. 순환 참조 및 아키텍처 위반.)
- 이 강력한 역방향/건너뛰기 의존성 금지 규칙은 `tests/architecture/test_imports.py` 및 `Agent Runner`의 AST 분석에 의해 매번 기계적으로 체크되며, 위반 시 에이전트 작업은 즉결 실패 처리됩니다.

## Korean Developer Experience Notes

- 문서/운영 지침은 한국어를 기본 언어로 유지합니다.
- 코드 식별자/외부 API 명세는 영어 원문을 유지하되, 운영 해설은 한국어로 제공합니다.
- 상세 규칙은 `.agents/rules/korean-developer-experience.md`를 참조합니다.
