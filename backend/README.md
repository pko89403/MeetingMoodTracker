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
  - 분석 히스토리 저장 및 재조회
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

---

## ⚠️ 운영 시 유의사항
- **네트워크**: Azure OpenAI 리소스의 방화벽 정책이 허용되어 있어야 합니다.
- **필터링**: 자해/자살/혐오 표현 등은 Azure Content Filter에 의해 차단되어 `502` 에러를 반환할 수 있습니다.
- **한국어 우선**: 모든 시스템 프롬프트 및 데이터 처리는 한국어 및 한/영 혼합 발화에 최적화되어 있습니다.
