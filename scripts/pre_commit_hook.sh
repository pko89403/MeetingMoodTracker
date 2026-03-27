#!/usr/bin/env bash

# 기계적 하네스(단방향 헌법 및 린터) 개입 훅
echo ""
echo "========================================="
echo "⚙️ 실행 중: MeetingMoodTracker 하네스 훅..."
echo "========================================="

# 단일 진입점: runner precommit 모드
echo "[1/1] 🧭 Runner precommit 모드 실행..."
uv run python harness/runner/agent_runner.py --mode precommit
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
