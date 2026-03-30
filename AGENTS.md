# 🤖 Project Constitution & Table of Contents (AGENTS.md)

MeetingMoodTracker 프로젝트에 새로 진입한 에이전트를 위한 **최상위 길잡이(Index) 파일**입니다.
이 문서는 전체 룰을 나열하지 않으며, 상황에 따라 필요한 지식이 위치한 경로로 안내합니다. 에이전트는 무작정 전체 파일을 읽지 않고(점진적 공개 원칙), 필요한 정보만 **해당 경로**에서 찾아 읽어야 합니다.

## 🇰🇷 0. 한국인 개발자 우선 원칙 (필수)
이 프로젝트는 한국어 사용자/개발자 경험을 기본값으로 둡니다. 아래 원칙을 모든 변경에 적용하십시오.
- **문서/가이드 언어 우선순위**: 한국어를 기본으로 작성하고, 필요 시 영어 용어를 괄호로 병기합니다.
- **코드 문서화**: `app/` 및 `scripts/`의 클래스/함수에는 목적과 입력/출력을 이해할 수 있는 한국어 docstring을 유지합니다.
- **에러 메시지/운영 문구**: API/운영 문구는 한국어 사용자 관점에서 이해 가능해야 하며, 외부 연동 제약(Azure 정책 등)은 한국어로 명확히 설명합니다.
- **테스트 데이터 로컬리티**: 한국어 발화를 우선하고, 한/영 혼합(code-switching) 케이스를 함께 포함합니다.
- **변경 동기 기록**: 한국어 개발자 DX에 영향을 주는 변경은 `docs/`와 `README.md`에 함께 남깁니다.

## 📍 1. 현황 및 진행 컨텍스트 파악 
세션 진입 시 다음 파일들을 가장 먼저 확인하여 방향을 잡으십시오:
- **`agent-progress.txt`**: 이전 에이전트들이 수행한 작업 내역, 성공/실패 기록, 현재 맥락.
- **`feature_list.json`**: 점진적으로 완수해야 할 단일 기능 명세서. 반드시 `"passes": false`인 1개의 기능 구현 및 통과에만 집중하십시오. 전체를 한 번에 리팩토링하지 마십시오.
- **`init.sh`**: 프로젝트 셋업, E2E 기본 테스트 실행 및 로컬 서버를 즉시 구동하는 스크립트.

## ⚙️ 1-1. Codex Worktree Setup 규칙 (필수)
모든 Codex worktree는 아래 동일한 방식으로 셋업합니다.
- **실행 파일**: `scripts/setup_worktree.sh`
- **환경 등록 파일**: `.codex/environments/environment.toml`의 `[setup].script`
- **가상환경 정책**: 전역/공유 venv를 사용하지 않고, worktree 루트의 `.venv`만 사용
- **캐시 정책**: `UV_CACHE_DIR`는 홈 캐시(`~/.cache/uv`)를 재사용하여 설치 비용 최소화
- **실행 순서**: worktree 진입 직후 setup script를 먼저 실행한 뒤 개발/테스트를 진행

## 🔄 1-2. `feature_list.json` ↔ GitHub Issue 동기화 규칙 (필수)
기능 진행상태는 로컬 파일과 GitHub Issue를 함께 맞춰 관리합니다.
- **원칙**: worktree setup 단계에서 feature-issue 동기화를 기본 수행합니다.
- **상세 운영 규칙/명령어/예외**: `docs/AGENT_OPERATIONS_GUIDE.md`의
  `Codex Worktree Setup Policy`, `Feature-Issue Sync Operations` 섹션을 참조하십시오.
- **구현 진입점**: `scripts/setup_worktree.sh`, `scripts/sync_feature_issues.py`

## 📖 2. 시스템 룰 및 기록 (`docs/` - System of Record)
하네스 원칙, 아키텍처 제약, 설계안을 파악할 때 확인하십시오:
- **`docs/ARCHITECTURE.md`**: 하네스(린터/러너) 및 모듈 간의 의존성 구조 제약 조건.
- **`docs/DESIGN.md`**: 도메인 목적 및 스펙 주도 개발(SDD) 원칙.
- **`docs/QUALITY_SCORE.md`**: AST 리뷰어 및 린터(`AgentWorkflowLinter`)를 통과하기 위한 에이전트 코딩 가이드라인.
- **`docs/AGENT_OPERATIONS_GUIDE.md`**: agent/skill/workflow 선택 우선순위와 FastAPI 표준 실행 순서.
- **`docs/AGENT_CAPABILITY_CATALOG.md`**: `.agents`, `~/.codex`, `~/.agents` 기반 capability 인벤토리와 vendor 고정 현황.
- **`docs/exec-plans/`**: 이전 스텝별 실행(리팩토링) 계획 이력.

## 🛠️ 3. 에이전트 역할 및 스킬 (`.agents/`)
본인의 권한이나 특정 작업을 수행할 때 필요한 매뉴얼이 필요할 때 참조하십시오:
- **`.agents/rules/`**: (상시 제약) 어떤 상황에서도 무조건 지켜야 하는 프롬프트 레벨의 고정 헌법 (아키텍처 강제, Pydantic 룰 등).
- **`.agents/workflows/`**: (순차 절차) API 생성, 테스트 배포 등 복잡한 태스크를 오류 없이 처리하기 위한 Step-by-step 궤적(Trajectory) 가이드.
- **`.agents/agents/`**: 프로젝트 내 역할별(Backend, Tester 등) 시스템/브라우저 접근 권한 및 제약 사항.
- **`.agents/skills/`**: 주요 도메인 스킬 매뉴얼 및 에이전트가 자주 범하는 실수들을 방지하기 위한 `Gotchas(주의사항)`.
- **`.agents/vendor/`**: 선별 복사로 고정한 외부 capability 스냅샷 및 manifest.

> **[필수 제약]**: 아키텍처나 기능에 중대한 변경이 발생하면 반드시 연관된 `docs/` 시스템 문서를 함께 최신화(업데이트)해야 합니다.
