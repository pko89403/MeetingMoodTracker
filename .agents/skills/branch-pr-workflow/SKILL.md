---
name: branch-pr-workflow
description: Create a clean git branch, define PR commit scope, and prepare push/PR execution; use when users ask to move from working-tree changes to safe branch creation, scoped commits, and ready-to-open pull requests.
---

# Branch To PR Workflow

작업 트리 변경사항을 안정적으로 브랜치/커밋/PR 단위로 정리한다.

## Quick start
1. 커밋 범위 진단 리포트 생성:
   - `./.agents/skills/branch-pr-workflow/scripts/pr_scope_report.sh origin/main`
2. 브랜치 생성/전환:
   - `./.agents/skills/branch-pr-workflow/scripts/create_branch.sh "sse-stream-fix"`
3. 범위를 기준으로 파일 스테이징 및 커밋.
4. 테스트/린트 통과 확인 후 `git push -u origin <branch>`.
5. PR 본문 작성은 `references/pr-checklist.md` 템플릿을 사용.

## Workflow

### 1) 범위 확정
- 리포트에서 `staged/unstaged/untracked`를 구분한다.
- 이번 PR 목표와 무관한 파일은 제외 후보로 표시한다.
- 범위 판단 규칙은 `references/scope-rules.md`를 따른다.

### 2) 브랜치 정리
- `detached HEAD`거나 타 브랜치에서 작업 중이면 새 브랜치로 전환한다.
- 브랜치명은 `codex/<slug>`를 기본으로 사용한다.
- 브랜치 생성은 `scripts/create_branch.sh`를 사용해 일관되게 처리한다.

### 3) 커밋 단위 구성
- 서로 다른 목적의 변경은 커밋을 분리한다.
- 한 커밋은 한 문장으로 설명 가능한 논리 단위를 유지한다.
- 스테이징 전에 불필요한 파일 포함 여부를 다시 확인한다.

### 4) PR 준비
- 테스트/린트/하네스 결과를 확인한다.
- PR 제목/본문에는 목적, 검증, 리스크, 제외 범위를 포함한다.
- 체크리스트는 `references/pr-checklist.md`를 사용한다.

## Resources
- `scripts/create_branch.sh`: `codex/<slug>` 브랜치 생성/전환 자동화
- `scripts/pr_scope_report.sh`: 커밋 범위 진단 리포트 생성
- `references/scope-rules.md`: 범위 포함/제외 판단 기준
- `references/pr-checklist.md`: PR 전송 전 체크리스트/본문 템플릿
