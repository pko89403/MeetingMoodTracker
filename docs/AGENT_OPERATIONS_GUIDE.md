# Agent Operations Guide

AGENTS.md의 인덱스 원칙을 유지하기 위해, 실제 운영 규칙은 이 문서에서 상세 관리합니다.

## Capability Priority

1. 프로젝트 로컬 자산(`.agents/rules`, `.agents/workflows`, `.agents/agents`, `.agents/skills`)
2. 프로젝트에 고정된 vendor 자산(`.agents/vendor`)
3. 사용자 홈 경로(`~/.codex`, `~/.agents`)는 직접 참조하지 않고, 선별 복사 후 vendor로 고정

## Korean-First Execution Policy

- 기본 커뮤니케이션/문서 언어는 한국어입니다.
- 상세 규칙은 `.agents/rules/korean-developer-experience.md`를 우선 참조합니다.
- 코드 식별자와 외부 API 파라미터명은 영어를 유지하고, 설명/문서화는 한국어를 기본으로 작성합니다.

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

## Codex Worktree Setup Policy

- Codex worktree의 초기화는 `scripts/setup_worktree.sh`를 단일 진입점으로 사용합니다.
- 가상환경은 worktree 루트 `.venv`를 사용하며, 전역/공유 venv를 사용하지 않습니다.
- `UV_CACHE_DIR`(기본 `~/.cache/uv`)를 재사용하여 의존성 설치 비용을 줄입니다.
- `.codex/environments/environment.toml`의 `[setup].script`는 위 스크립트를 가리켜야 합니다.

## Vendor Capability Management

- manifest 파일(`.agents/vendor/capability-manifest.json`)에는 `source_path`, `destination_path`, `version`, `copied_at`를 반드시 기록합니다.
- vendor 자산 변경 시 반드시 manifest를 동시 갱신합니다.
- 변경 후 `python scripts/validate_capability_manifest.py`를 실행하여 중복 ID/경로 및 파일 존재 여부를 검증합니다.
