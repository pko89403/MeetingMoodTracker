#!/usr/bin/env bash

# 기계적 하네스(단방향 헌법 및 린터) 개입 훅
echo ""
echo "========================================="
echo "⚙️ 실행 중: MeetingMoodTracker 하네스 훅..."
echo "========================================="

# 1. AST 아키텍처 체커 강제 실행
echo "[1/2] 🏛️ 아키텍처 의존성(AST) 검증 진행..."
uv run pytest tests/architecture/test_imports.py -q
ARCH_STATUS=$?

if [ $ARCH_STATUS -ne 0 ]; then
    echo ""
    echo "❌ [System Intercept] 에이전트 커밋 차단(exit 2)!"
    echo "🚨 사유: 레이어 간 단방향 의존성 규칙(Types <- Config <- Repo <- Service <- Runtime <- UI) 위반."
    echo "💡 로그를 확인하고 역방향 패키지 임포트를 제거하세요."
    echo "========================================="
    exit 2
fi

# 2. 파이썬 코드 린터(Ruff) 강제 실행
echo "[2/2] 🧹 코드 컨벤션(Ruff) 검증 진행..."
uv run ruff check app/ tests/
RUFF_STATUS=$?

if [ $RUFF_STATUS -ne 0 ]; then
    echo ""
    echo "❌ [System Intercept] 에이전트 커밋 차단(exit 2)!"
    echo "🚨 사유: 파이썬 코드 컨벤션 규칙 위반 (타입 힌트, 미사용 변수 등)."
    echo "💡 로그를 확인하고 경고를 모두 수정하세요. ('uv run ruff check --fix' 이용 가능)"
    echo "========================================="
    exit 2
fi

echo "✅ 모든 시스템 하네스 검증 통과! 커밋을 안전하게 허가합니다."
echo "========================================="
exit 0
