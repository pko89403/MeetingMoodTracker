#!/usr/bin/env bash
# create-pr 스킬 스크립트

set -euo pipefail

echo "=== [create-pr] Push Branch and Create PR ==="

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPO_ROOT}"

CURRENT_BRANCH="$(git branch --show-current)"
if [ -z "${CURRENT_BRANCH}" ]; then
    echo "Error: Not currently on any branch."
    exit 1
fi

echo "Pushing branch '${CURRENT_BRANCH}' to origin..."
# Check if branch exists on remote, if not set upstream
git push -u origin "${CURRENT_BRANCH}" || {
    echo "Error: Failed to push branch. Please check your git credentials or network."
    exit 1
}

echo "Creating Pull Request..."

PR_TITLE="feat(copilot): GitHub/awesome-copilot 기반 CLI 하네스 구축"
PR_BODY="## 목적
- Copilot CLI가 프로젝트의 기술 스택에 맞춰 자율적으로 문제를 검증(Linter, Pytest)하고 수정할 수 있도록 \`awesome-copilot\`의 공식 리소스 생태계 이식

## 변경 내용
- \`docs/copilot-harness-setup-guide.html\`: 설정 히스토리 및 명세 리포트 추가
- \`.github/agents/\`: API, React, MCP 등 전문가 에이전트 도입
- \`.github/instructions/\`: Python(FastAPI), TS(React) 자동 적용 코딩 표준 
- \`.github/skills/\`: ruff, pytest, ts-jest 등 검증 스킬 
- \`.github/hooks/\`: secrets-scanner 등 보안 훅
- \`.github/workflows/\`: Agentic PR 리뷰 파이프라인

## 리뷰 요청
- 추가적으로 구성하고 싶은 스킬이나 에이전트 페르소나가 있다면 알려주세요!"

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Please install it or manually create the PR on GitHub."
    exit 1
fi

# Create PR
gh pr create --title "${PR_TITLE}" --body "${PR_BODY}"

echo "=== [create-pr] Finished successfully ==="
