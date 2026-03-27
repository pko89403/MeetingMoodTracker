# Quality Score & Agent Rules

MeetingMoodTracker 프로젝트의 품질은 자동화된 파이프라인에 의해 엄격하게 관리됩니다. 에이전트는 아래의 규칙을 준수하여 코드를 생성해야 합니다.

## 1. Type Hint 강제
모든 함수 선언부와 반환값에는 반드시 파이썬 타입 힌트를 기재해야 합니다.
- **에러 발생:** Linter가 `AgentWorkflowLinter`를 통해 타입 힌트 누락을 잡아내면 코드 커밋을 거부하고 실패 처리합니다.

## 2. Pydantic 스키마 검증
FastAPI의 모든 입출력 통신은 `app/types` 내의 Pydantic 모델을 통해서만 이루어져야 합니다. (하드코딩된 딕셔너리 리턴은 절대 금지됩니다.)
- `FastAPIContractValidator`가 runtime 라우트의 `response_model` 명시 여부와 `app/types` 경로 준수를 검사합니다.

## 3. 코드 스타일 포매팅
- 본 프로젝트는 코드 포매팅과 정적 분석에 `Ruff`를 사용합니다.
- `uv run ruff check .` 및 `uv run ruff format .` 스크립트를 통해 에이전트의 스타일을 통일합니다.
- 단, 긴글이나 주석 처리 시 발생하는 줄바꿈 에러(`E501`)는 예외로 처리합니다.

## 4. 구조 침해 금지
Service 레이어가 API 컨트롤러 레이어에 접근하려고 하면 즉시 AST 체커에 의해 에러가 발생합니다. 레이어 침범 시 역방향 의존성을 점검하고, 공통 모델 레이어(`types`)만을 참조하도록 구조를 리팩토링해야 합니다.

## 5. Capability Manifest 무결성
- 프로젝트에 고정된 agent/skill vendor 자산은 `.agents/vendor/capability-manifest.json`을 통해 관리합니다.
- manifest는 중복 ID/경로, 파일 존재 여부를 `scripts/validate_capability_manifest.py`로 검사합니다.

## 6. 한국어 개발자 경험(DX) 준수
- `app/`, `scripts/` 내 클래스/함수에는 한국어 docstring을 유지합니다.
- 한국어 발화 및 한/영 혼합 발화 케이스가 테스트/샘플에 유지되어야 합니다.
- 언어 정책 상세는 `.agents/rules/korean-developer-experience.md`를 기준으로 합니다.
