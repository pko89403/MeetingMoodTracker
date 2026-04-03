# Agent Capability Catalog

이 문서는 프로젝트에서 사용 가능한 agent/skill 자산을 소스별로 인벤토리하고, 선별 복사된 vendor 자산의 기준 경로를 정의합니다.

## Source Inventory

| Source | Type | Name | Status | Destination |
| --- | --- | --- | --- | --- |
| `.github/agents` | agent | `Expert React Frontend Engineer`, `API Architect`, `Python MCP Server Expert`, `UI Designer`, `Product Owner` | Active (Copilot custom agents) | `.github/agents/` |
| `.agents/agents` | agent | `api-designer`, `backend-developer`, `python-pro`, `test-automator`, `debugger`, `code-reviewer`, `refactoring-specialist`, `nlp-engineer` | Active | `.agents/agents/` |
| `~/.codex/agents` | agent | `api-designer`, `backend-developer`, `python-pro`, `test-automator`, `debugger`, `code-reviewer`, `refactoring-specialist`, `nlp-engineer` | Selected + copied | `.agents/vendor/agents/` |
| `.agents/skills` | skill | `branch-pr-workflow`, `commit-push-pr`, `changelog-generator`, `gh-address-comments`, `gh-fix-ci`, `meeting-insights-analyzer`, `meeting-notes-and-actions`, `notion-meeting-intelligence`, `notion-spec-to-implementation` | Active | `.agents/skills/` |
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

## Language Baseline

- 프로젝트 기본 운영 언어는 한국어입니다.
- capability 적용 시 결과 설명/문서화는 한국어를 우선하고, 기술 고유명사만 영어 식별자를 유지합니다.

## Issue #28 Squad Mapping

| Role | Agent Asset | Notes |
| --- | --- | --- |
| FrontEnd 개발 에이전트 | `.github/agents/expert-react-frontend-engineer.agent.md` | 기존 React 전문 에이전트를 재사용 |
| BackEnd 개발 에이전트 | `.github/agents/api-architect.agent.md` | 기존 API 에이전트를 재사용하되 FastAPI/project-aware 문맥을 추가 주입 |
| UI Designer 에이전트 | `.github/agents/ui-designer.agent.md` | 이슈 #28 전용 신규 역할 |
| Product Owner 에이전트 | `.github/agents/product-owner.agent.md` | 이슈 #28 전용 신규 역할 |
