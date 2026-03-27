# Agent Operations Guide

AGENTS.md의 인덱스 원칙을 유지하기 위해, 실제 운영 규칙은 이 문서에서 상세 관리합니다.

## Capability Priority

1. 프로젝트 로컬 자산(`.agents/rules`, `.agents/workflows`, `.agents/agents`, `.agents/skills`)
2. 프로젝트에 고정된 vendor 자산(`.agents/vendor`)
3. 사용자 홈 경로(`~/.codex`, `~/.agents`)는 직접 참조하지 않고, 선별 복사 후 vendor로 고정

## Task Routing Matrix

| Task Type | Primary Agent | Supporting Skill/Workflow |
| --- | --- | --- |
| FastAPI API 계약 설계 | `api-designer` | `.agents/workflows/new-api-endpoint.md` |
| FastAPI 구현/버그 수정 | `backend-developer`, `python-pro` | `.agents/rules/architecture.md`, `.agents/rules/pydantic.md` |
| 테스트/회귀 강화 | `test-automator`, `debugger` | `.agents/workflows/test-and-deploy.md` |
| 구조 개선/리팩토링 | `refactoring-specialist`, `code-reviewer` | `docs/ARCHITECTURE.md`, `docs/QUALITY_SCORE.md` |
| 회의 도메인 분석 로직 | `nlp-engineer` | `meeting-*`, `notion-*` skills |

## FastAPI Standard Execution Order

로컬 하네스 표준 순서는 아래와 같습니다.

1. Architecture Validator
2. FastAPI Contract Validator
3. Linter (Custom + Ruff)
4. Pytest (`full` 모드에서만)

실행 명령:

- pre-commit 게이트: `uv run python harness/runner/agent_runner.py --mode precommit`
- 전체 게이트: `uv run python harness/runner/agent_runner.py --mode full`

## Vendor Capability Management

- manifest 파일(`.agents/vendor/capability-manifest.json`)에는 `source_path`, `destination_path`, `version`, `copied_at`를 반드시 기록합니다.
- vendor 자산 변경 시 반드시 manifest를 동시 갱신합니다.
- 변경 후 `python scripts/validate_capability_manifest.py`를 실행하여 중복 ID/경로 및 파일 존재 여부를 검증합니다.
