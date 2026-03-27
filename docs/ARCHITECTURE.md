# MeetingMoodTracker Architecture

## System Diagram
MeetingMoodTracker는 인간의 언어로 된 룰이 아닌 "기계적인 하네스"를 통해 코딩 품질을 강제합니다.

### 1. Harness Layer (에이전트 제어 및 검증)

- **Agent Runner (`harness/runner/`)**: `architecture -> fastapi-contract -> linter -> pytest` 순서로 검증하며, pre-commit에서는 `--mode precommit`으로 빠른 로컬 게이트를 수행합니다.
- **Structural Validators (`harness/validators/`)**: AST(Abstract Syntax Tree) 분석을 통해, 허가되지 않은 모듈 간의 의존성 수입을 차단합니다.
- **FastAPI Contract Validator (`harness/validators/fastapi_contract_checker.py`)**: runtime 라우트의 반환 타입, `response_model`, Pydantic I/O 경로(`app/types`) 준수 여부를 강제합니다.
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

## Dependency Rules (단방향 헌법)

- 모듈 의존성은 반드시 **`Types <- Config <- Repo <- Service <- Runtime <- UI`** 의 단방향 논리로만 흘러야 합니다.
- (예: `service`는 `types`, `config`, `repo` 레이어를 자유롭게 의존할 수 있지만, `runtime`이나 `ui` 모듈을 절대 임포트해서는 안 됩니다. 순환 참조 및 아키텍처 위반.)
- 이 강력한 역방향/건너뛰기 의존성 금지 규칙은 `tests/architecture/test_imports.py` 및 `Agent Runner`의 AST 분석에 의해 매번 기계적으로 체크되며, 위반 시 에이전트 작업은 즉결 실패 처리됩니다.
