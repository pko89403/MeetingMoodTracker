#!/usr/bin/env bash

set -euo pipefail

if command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
elif [[ -x "${HOME}/.local/bin/uv" ]]; then
    UV_BIN="${HOME}/.local/bin/uv"
elif [[ -x "/opt/homebrew/bin/uv" ]]; then
    UV_BIN="/opt/homebrew/bin/uv"
else
    echo "❌ uv 실행 파일을 찾지 못했습니다. (PATH / ~/.local/bin / /opt/homebrew/bin 확인 필요)"
    exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPO_ROOT}"

# pre-commit 훅 실행 시 PATH가 축소되는 환경을 대비해 uv 경로를 선반영한다.
export PATH="$(dirname "${UV_BIN}"):${PATH}"

# 기계적 하네스(단방향 헌법 및 린터) 개입 훅
echo ""
echo "========================================="
echo "⚙️ 실행 중: MeetingMoodTracker 하네스 훅..."
echo "========================================="

# 단일 진입점: runner precommit 모드
echo "[1/1] 🧭 Runner precommit 모드 실행..."
"${UV_BIN}" run python harness/runner/agent_runner.py --mode precommit
RUNNER_STATUS=$?

if [ $RUNNER_STATUS -ne 0 ]; then
    echo ""
    echo "❌ [System Intercept] 에이전트 커밋 차단(exit 2)!"
    echo "🚨 사유: Runner precommit 하네스 검증 실패."
    echo "💡 runner 출력의 단일 Next Action부터 수정하세요."
    echo "========================================="
    exit 2
fi

echo "✅ 모든 시스템 하네스 검증 통과! 커밋을 안전하게 허가합니다."
echo "========================================="
exit 0
