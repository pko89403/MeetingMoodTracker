# Agent Capability Catalog

이 문서는 프로젝트에서 사용 가능한 agent/skill 자산을 소스별로 인벤토리하고, 선별 복사된 vendor 자산의 기준 경로를 정의합니다.

## Source Inventory

| Source | Type | Name | Status | Destination |
| --- | --- | --- | --- | --- |
| `.agents/agents` | agent | `api-designer`, `backend-developer`, `python-pro`, `test-automator`, `debugger`, `code-reviewer`, `refactoring-specialist`, `nlp-engineer` | Active | `.agents/agents/` |
| `~/.codex/agents` | agent | `api-designer`, `backend-developer`, `python-pro`, `test-automator`, `debugger`, `code-reviewer`, `refactoring-specialist`, `nlp-engineer` | Selected + copied | `.agents/vendor/agents/` |
| `.agents/skills` | skill | `meeting-insights-analyzer`, `meeting-notes-and-actions`, `notion-meeting-intelligence`, `notion-spec-to-implementation` | Selected + copied | `.agents/vendor/skills/` |
| `~/.codex/skills/.system` | skill | `openai-docs` | Selected + copied (harness 보조 문서 리서치) | `.agents/vendor/skills/openai-docs/` |
| `~/.agents/skills` | skill | `microsoft-foundry*` | Discovered only (out of project scope) | N/A |

## Vendor Source of Truth

- 최종 고정 자산 경로: `.agents/vendor/`
- 매니페스트: `.agents/vendor/capability-manifest.json`
- 무결성 검사: `python scripts/validate_capability_manifest.py`

## Selection Policy

- 전략: **Selective Copy**
- 기준: FastAPI/하네스 직접 연관성 + 프로젝트 도메인 적합성
- 제외 원칙: 현재 프로젝트 범위와 무관한 클라우드/배포 특화 스킬은 문서 인벤토리만 유지하고 vendor 고정은 하지 않음
