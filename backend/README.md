# Meeting Mood Tracker

회의 발화 데이터를 분석하여 주제(Topic), 감정 분포(Sentiment), 그리고 회의 특화 정서 시그널(Emotion)을 추출하는 FastAPI 기반 분석 서버입니다.

## 🚀 Quick Start

### 1. 서버 실행 (Docker)
본 저장소를 서브모듈로 포함하는 상위 프로젝트의 루트에서 실행합니다.
```bash
export APP_ENV=dev
export FASTAPI_SERVER_PORT=8000
docker compose up --build
```

### 2. API 검증
서버가 정상적으로 실행되었는지 확인합니다.
```bash
curl http://localhost:8000/healthz
# 응답: {"status":"ok"}
```

---

## 📖 Core API Guide

### 1. 회의록 종합 분석 (Analyze Mood)
회의록 전체 텍스트를 입력받아 주제, 감정, 정서 신호를 한 번에 분석합니다.

- **Endpoint**: `POST /api/v1/analyze`
- **Request**:
  ```json
  {
    "meeting_id": "m_20260401_001",
    "text": "오늘 배포 일정에 대해 논의합시다. 현재 리스크가 좀 있네요."
  }
  ```
- **Response**:
  - `topic`: 핵심 주제 키워드 (쉼표 구분 문자열)
  - `sentiment`: 긍정/부정/중립 분포 (`0~100` 정수 점수)
  - `emotion`: 8개 기본 정서 및 5개 회의 시그널 수치

### 2. 발화 턴 단위 감정 분류 (Turn Sentiment)
단일 발화 문장에 대한 긍/부정/중립 여부를 판단합니다.

- **Endpoint**: `POST /api/v1/sentiment/turn`
- **Request**:
  ```json
  {
    "meeting_id": "m_001",
    "turn_id": "t_014",
    "utterance_text": "이 제안은 정말 획기적이네요! 찬성합니다."
  }
  ```
- **Response**:
  - `label`: `POS`, `NEG`, `NEUTRAL` 중 하나
  - `confidence`: 신뢰도 (`0.0 ~ 1.0`)

### 3. 프로젝트 인지 턴 저장 (Project-aware Turn Storage)
프로젝트/회의 경로 아래 개별 발화를 분석하고 저장하는 엔드포인트입니다.

- **Endpoint**: `POST /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`
- **Request**:
  ```json
  {
    "agent_id": "agent_facilitator",
    "turn_id": "t_014",
    "utterance_text": "배포 전에 QA 리스크를 먼저 정리하고 대응 순서를 확정합시다.",
    "order": 14
  }
  ```
- **Response Example**:
  ```json
  {
    "project_id": "proj_alpha",
    "meeting_id": "m_20260401_001",
    "agent_id": "agent_facilitator",
    "turn_id": "t_014",
    "created_at": "2026-04-03T09:30:00Z",
    "updated_at": "2026-04-03T09:30:00Z",
    "utterance_text": "배포 전에 QA 리스크를 먼저 정리하고 대응 순서를 확정합시다.",
    "order": 14,
    "sentiment": {
      "label": "NEUTRAL",
      "confidence": 0.82,
      "evidence": "QA 리스크"
    },
    "emotion": {
      "emotions": {
        "neutral": { "confidence": 52 },
        "anxiety": { "confidence": 21 },
        "frustration": { "confidence": 9 },
        "anger": { "confidence": 0 },
        "joy": { "confidence": 3 },
        "sadness": { "confidence": 2 },
        "excitement": { "confidence": 4 },
        "confusion": { "confidence": 9 }
      },
      "meeting_signals": {
        "urgency": { "confidence": 78 },
        "clarity": { "confidence": 64 },
        "alignment": { "confidence": 55 },
        "tension": { "confidence": 28 },
        "engagement": { "confidence": 61 }
      },
      "emerging_emotions": []
    }
  }
  ```
- **안정 계약(Stable Contract)**:
  - canonical 식별자는 `project_id + meeting_id + agent_id + turn_id` 조합입니다.
  - `agent_id`가 비어 있으면 API 응답에서는 `null`을 유지하고, 저장 경로에서는 예약 버킷 `__unassigned__`로 안전하게 분리합니다.
  - 응답은 최소한 식별자, `created_at`/`updated_at`, 그리고 분석 결과 축(`sentiment`, `emotion`)을 포함합니다.
  - 동일한 `project_id + meeting_id + agent_id + turn_id` 재전송은 **upsert/idempotent** 정책으로 처리됩니다.

### 4. JSON 저장 구조
issue #26의 1차 저장 전략은 DB가 아닌 JSON 파일 기반 계층 저장입니다.

```text
data/
  projects/
    {project_id}/
      meta.json
      meetings/
        {meeting_id}/
          meta.json
          agents/
            {agent_id}/
              turns.json
          aggregates.json   # 선택
```

- `project_id -> meeting_id -> agent_id -> turn_id` 계층을 canonical 저장 모델로 사용합니다.
- `meta.json`은 project/meeting 수준 메타데이터를 담고, `turns.json`은 agent별 raw turn 및 turn analysis 컬렉션을 담습니다.
- `aggregates.json`은 선택 파일이며, 없는 경우에도 raw turn을 기준으로 재계산 가능해야 합니다.
- 중복/재전송 정책의 기준은 파일명보다 **`project_id + meeting_id + agent_id + turn_id`** 조합입니다.

### 5. 회의 overview 조회 (Project-aware Meeting Overview)
저장된 턴 분석 결과를 바탕으로 회의 개요/집계를 조회합니다.

- **Endpoint**: `GET /api/v1/projects/{project_id}/meetings/{meeting_id}`
- **Response Example**:
  ```json
  {
    "project_id": "proj_alpha",
    "meeting_id": "m_20260401_001",
    "created_at": "2026-04-03T09:30:00Z",
    "updated_at": "2026-04-03T09:35:00Z",
    "turn_count": 12,
    "agent_count": 3,
    "topics": ["배포 일정", "QA 리스크"],
    "sentiment": {
      "positive": { "confidence": 48 },
      "negative": { "confidence": 22 },
      "neutral": { "confidence": 30 }
    },
    "emotions": {
      "joy": { "confidence": 34 },
      "neutral": { "confidence": 28 },
      "anxiety": { "confidence": 18 },
      "frustration": { "confidence": 9 },
      "excitement": { "confidence": 4 },
      "confusion": { "confidence": 4 },
      "anger": { "confidence": 2 },
      "sadness": { "confidence": 1 }
    },
    "signals": {
      "alignment": { "confidence": 71 },
      "urgency": { "confidence": 63 },
      "clarity": { "confidence": 66 },
      "engagement": { "confidence": 69 },
      "tension": { "confidence": 24 }
    },
    "one_line_summary": "12개 발화에서 배포 일정, QA 리스크 중심으로 논의가 진행됐습니다."
  }
  ```
- **특이사항**:
  - `topics`는 저장된 turn transcript를 순서대로 합쳐 **조회 시 계산(on-read)** 합니다.
  - overview 응답은 full turn payload를 포함하지 않고, overview 카드에 필요한 aggregate만 반환합니다.
  - topic aggregate 계산에 실패하면 `502` (`MEETING_READ_LLM_FAILURE`)를 반환합니다.

### 6. 발화 목록 조회 (Meeting Turns)
회의 timeline/detail 패널에 필요한 정렬된 턴 목록을 반환합니다.

- **Endpoint**: `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`
- **Response Example**:
  ```json
  {
    "project_id": "proj_alpha",
    "meeting_id": "m_20260401_001",
    "total_count": 2,
    "turns": [
      {
        "project_id": "proj_alpha",
        "meeting_id": "m_20260401_001",
        "agent_id": "agent_facilitator",
        "turn_id": "t_014",
        "utterance_text": "배포 전에 QA 리스크를 먼저 정리하고 대응 순서를 확정합시다.",
        "created_at": "2026-04-03T09:30:00Z",
        "updated_at": "2026-04-03T09:30:00Z",
        "order": 14,
        "sentiment": {
          "label": "NEUTRAL",
          "confidence": 0.82,
          "evidence": "QA 리스크"
        },
        "emotion": {
          "emotions": {
            "neutral": { "confidence": 52 },
            "anxiety": { "confidence": 21 },
            "frustration": { "confidence": 9 },
            "anger": { "confidence": 0 },
            "joy": { "confidence": 3 },
            "sadness": { "confidence": 2 },
            "excitement": { "confidence": 4 },
            "confusion": { "confidence": 9 }
          },
          "meeting_signals": {
            "urgency": { "confidence": 78 },
            "clarity": { "confidence": 64 },
            "alignment": { "confidence": 55 },
            "tension": { "confidence": 28 },
            "engagement": { "confidence": 61 }
          },
          "emerging_emotions": []
        }
      }
    ]
  }
  ```
- **특이사항**:
  - 응답의 `turns`는 저장소 기준 정렬 순서(`order -> created_at -> turn_id`)를 따릅니다.
  - 저장 시 `agent_id=None`이었던 턴은 조회 응답에서도 `agent_id: null`로 유지됩니다.

### 7. 에이전트 집계 조회 (Meeting Agents)
회의별 화자 카드/agent report용 aggregate를 반환합니다.

- **Endpoint**: `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/agents`
- **Response Example**:
  ```json
  {
    "project_id": "proj_alpha",
    "meeting_id": "m_20260401_001",
    "total_count": 2,
    "agents": [
      {
        "project_id": "proj_alpha",
        "meeting_id": "m_20260401_001",
        "agent_id": "agent_facilitator",
        "turn_count": 6,
        "turn_ids": ["t_001", "t_004", "t_009"],
        "avg_sentiment": {
          "positive": { "confidence": 42 },
          "negative": { "confidence": 18 },
          "neutral": { "confidence": 40 }
        },
        "primary_emotion": "joy",
        "primary_signal": "alignment",
        "emerging_emotions": ["optimism", "relief"],
        "summary": null
      }
    ]
  }
  ```
- **특이사항**:
  - aggregate는 저장 파일이 아니라 raw turn을 기준으로 **조회 시 계산**합니다.
  - unassigned bucket에 저장된 턴은 agent 집계 응답에서 `agent_id: null`로 노출됩니다.

### 8. 관리형 실제 fixture 데이터 (Frontend 연동 준비용)
실제 LLM 호출로 한 번 생성한 짧은 회의 데이터를 **재현 가능한 고정 fixture**로 관리합니다.

- **seed 스크립트**: `backend/scripts/seed_issue27_demo_meeting.py`
- **기본 fixture ID**
  - `project_id`: `project-frontend-demo`
  - `meeting_id`: `meeting-issue27-short-live`
- **구성**
  - agent 3명 (`alice`, `bob`, `carol`)
  - turn 6개
  - QA 리스크, 회귀 테스트 진행률, 결제 플로우 검증, 배포 여부 결정이 포함된 짧은 회의
- **의도**
  - 프론트엔드 개발을 나중에 하더라도, 동일한 실제 분석 결과 기반 데이터를 반복 사용
  - VPN/LLM 상태와 무관하게 항상 같은 `project_id / meeting_id`를 복원

```bash
cd backend
uv run python scripts/seed_issue27_demo_meeting.py
```

필요하면 project/meeting ID를 바꿔서 같은 fixture를 다른 경로로도 넣을 수 있습니다.

```bash
cd backend
uv run python scripts/seed_issue27_demo_meeting.py \
  --project-id project-my-demo \
  --meeting-id meeting-short-demo
```

seed 후 확인 예시:

```bash
curl http://localhost:8000/api/v1/projects/project-frontend-demo/meetings/meeting-issue27-short-live
curl http://localhost:8000/api/v1/projects/project-frontend-demo/meetings/meeting-issue27-short-live/turns
curl http://localhost:8000/api/v1/projects/project-frontend-demo/meetings/meeting-issue27-short-live/agents
```

---

## 📊 분석 항목 상세 정의 (Analysis Items)

사용자는 분석 결과로 반환되는 각 수치를 아래와 같은 의미로 해석할 수 있습니다.

### 1. 주제 (Topic)
- 회의록 전체에서 논의된 핵심 의제를 추출합니다. 여러 주제가 있을 경우 쉼표(`,`)로 구분됩니다.

### 2. 감정 분포 (Sentiment)
회의의 전반적인 분위기를 3가지 축으로 수치화합니다. (합계 100)
- **Positive**: 긍정적, 낙관적, 또는 생산적인 분위기
- **Negative**: 부정적, 비판적, 또는 냉소적인 분위기
- **Neutral**: 감정이 배제된 중립적, 사실 전달 위주의 분위기

### 3. 통합 정서 분석 (Emotion)
회의 도메인에 특화된 상세 정서와 신호를 분석합니다.

#### **8개 기본 정서 (Base Emotions)**
화자의 발화에 내포된 보편적인 심리 상태를 측정합니다.
- **Anger (분노)**: 강한 불만, 거부감, 또는 공격적인 태도가 포착되는 상태
- **Joy (기쁨)**: 만족감, 성취감, 또는 긍정적인 유대감이 나타나는 상태
- **Sadness (슬픔)**: 실망, 상실감, 또는 침체된 분위기가 느껴지는 상태
- **Neutral (중립)**: 감정적 동요 없이 객관적 사실이나 정보를 전달하는 상태
- **Anxiety (불안)**: 우려, 걱정, 또는 결과에 대한 초조함이 포착되는 상태
- **Frustration (좌절)**: 진행의 장애로 인한 답답함이나 무력감이 나타나는 상태
- **Excitement (흥분)**: 높은 기대감, 열정, 또는 고양된 에너지가 감지되는 상태
- **Confusion (혼란)**: 정보의 부족이나 모순으로 인해 이해가 어려운 당혹스러운 상태

#### **5개 회의 시그널 (Meeting Signals)**
회의의 역동성과 생산성을 측정하는 핵심 지표입니다.
- **Tension (긴장도)**: 의견 대립, 갈등, 또는 심리적 압박의 정도
- **Alignment (합의도)**: 의견 일치, 방향성 공유, 또는 상호 동의의 수준
- **Urgency (긴급도)**: 사안의 시급성, 마감 압박, 또는 빠른 실행 요구 정도
- **Clarity (명확도)**: 논의 주제나 결론의 구체성 및 참석자들의 이해 수준
- **Engagement (참여도)**: 대화의 활발함, 적극적인 피드백, 또는 협력적 태도

#### **추가 발굴 정서 (Emerging Emotions)**
기본 8정서 외에 회의 맥락에서 중요하게 포착될 수 있는 **12가지 추가 정서 후보군(Set)** 중 가장 두드러지는 항목을 최대 3개까지 선별하여 추출합니다.

- **부정적/방어적 시그널**:
  - `resentment`(억울함/원망): 부당한 처우나 상황에 대한 불만
  - `skepticism`(회의감): 실효성이나 가능성에 대한 냉소적인 태도
  - `discouragement`(낙담): 의욕 상실이나 무력감을 느끼는 상태
  - `resignation`(체념): 상황 개선을 포기하고 받아들이는 상태
  - `defensiveness`(방어적 태도): 비판에 대해 책임을 회피하거나 자기를 보호하려는 태도
  - `distrust`(불신): 타인의 의도나 정보의 신뢰성에 대한 의심
- **불안/긴박 시그널**:
  - `concern`(우려): 잠재적 리스크나 문제에 대한 걱정
  - `fatigue`(피로): 장기화된 논의나 업무 과중으로 인한 지친 상태
  - `doubt`(의구심): 확신이 부족하고 주저하는 상태
  - `impatience`(조급함): 빠른 결론이나 성과를 독촉하는 심리 상태
- **긍정적/해소 시그널**:
  - `relief`(안도): 리스크 해소나 합의 도달 후 느끼는 안심
  - `optimism`(낙관): 향후 진행 방향에 대한 긍정적인 기대감

---

### Streamlit 분석 콘솔
API를 직접 호출하지 않고 웹 화면에서 텍스트를 분석하고 결과를 시각화할 수 있습니다.

- **실행**: `./scripts/run_ui.sh` (기본 포트: 8501)
- **주요 기능**:
  - 분석 로그 실시간 스트리밍 (SSE)
  - 세션 내 분석 히스토리 저장 및 재조회 (브라우저 세션 메모리 기반)
  - 감정 분포 차트 시각화

---

## 🛠️ For Developers (Internal)

### 1. 분석 아키텍처 (Analyze Fan-out)
`/analyze` 엔드포인트는 성능 최적화를 위해 3개의 독립적인 LLM 브랜치를 병렬로 실행합니다.
- **Topic Branch**: 의제 추출 (`reasoning_effort=none`)
- **Sentiment Branch**: 감정 분포 추출 (`reasoning_effort=none`)
- **Emotion Branch**: **1-stage 통합 추론** (8정서 + 5시그널, `reasoning_effort=none`)
- **최적화**: 모든 분석은 `evidence`(근거 문장) 생성을 제외하고 수치 데이터만 즉시 추출하도록 튜닝되어 있습니다.

### 2. 환경 설정 (ENV)
`example.env`를 복사하여 `dev.env` 또는 `prod.env`를 생성해 사용합니다.
- `LLM_API_KEY`: Azure OpenAI API 키
- `LLM_ENDPOINT`: Azure OpenAI 엔드포인트 URL
- `LLM_DEPLOYMENT_NAME`: 모델 배포 이름

### 3. 개발 도구
- **Worktree Setup**: `./scripts/setup_worktree.sh`
- **Issue Sync**: `uv run python scripts/sync_feature_issues.py`
- **Offline Evaluation**: `scripts/evaluate_sentiment_with_judge.py`

### 4. 저장 모델 로드맵 (Issue #26)
- 영속 저장의 canonical 식별자는 `project_id -> meeting_id -> agent_id -> turn_id` 계층입니다.
- 저장소 책임은 `app/repo/` 레이어에 배치하며, 초기 구현은 JSON 파일 기반 repository를 기준으로 설계합니다.
- JSON 경로 초안:
  - `data/projects/{project_id}/meta.json`
  - `data/projects/{project_id}/meetings/{meeting_id}/meta.json`
  - `data/projects/{project_id}/meetings/{meeting_id}/agents/{agent_id}/turns.json`
  - `data/projects/{project_id}/meetings/{meeting_id}/aggregates.json` (선택)
- 기본 정책은 **raw turn result 우선 보존 + aggregate는 조회 시 계산**입니다.
- 현재 공개된 project-aware 저장 경로는 `POST /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`입니다.
- `POST /api/v1/analyze`, `POST /api/v1/sentiment/turn` 요청 본문은 아직 `meeting_id` 중심이지만, turn 계열 request는 canonical 명칭 `agent_id`를 우선 사용하고 `speaker_id`는 호환 입력(alias)로만 허용합니다.

---

## ⚠️ 운영 시 유의사항
- **네트워크**: Azure OpenAI 리소스의 방화벽 정책이 허용되어 있어야 합니다.
- **필터링**: 자해/자살/혐오 표현 등은 Azure Content Filter에 의해 차단되어 `502` 에러를 반환할 수 있습니다.
- **한국어 우선**: 모든 시스템 프롬프트 및 데이터 처리는 한국어 및 한/영 혼합 발화에 최적화되어 있습니다.
