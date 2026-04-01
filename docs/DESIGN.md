# Design Guidelines

## 도메인 목표
회의록(Transcript)과 시뮬레이션 엔진에서 넘어온 대화 스크립트를 분석하여 **토픽(Topic)**, **감성(Sentiment)**, **정서(Emotion)**, **상관도(Correlation)**를 도출하는 API를 제공합니다.

## 시스템 설계 원칙
1. **SDD (Specification Driven Development)**
   모든 개발은 `tests/`에 스펙을 먼저 작성하고, 이를 통과시키는 최소한의 코드를 `app/`에 구현하는 순서로 진행합니다. 에이전트는 테스트 스크립트 작성부터 시작합니다.
2. **단일 목표 원칙**
   에이전트는 린트 에러, 아키텍처 에러, 비즈니스 에러 중 **한 번에 한 가지 에러**만 해결합니다. 에러가 복구되면 다시 Runner를 돌려 다음 에러를 타겟팅합니다.
3. **진실의 원천 업데이트**
   비즈니스 로직이나 시스템 아키텍처를 변경할 경우, 본 `docs/` 리포지토리의 파일들을 함께 최신화하여 점진적 지식 저장소의 최신성을 보장해야 합니다.
4. **한국어 우선 개발자 경험**
   프로젝트 문서화/운영 설명은 한국어를 기본으로 유지합니다. 기술 고유명사(예: `AzureOpenAI`, `chat.completions.create`)는 영어 식별자를 유지하되 한국어 설명을 병기합니다.

## 핵심 API
- `POST /api/v1/analyze`:
  - Request: `AnalyzeRequest` (meeting_id, text)
  - Response: `AnalyzeResponse` (topic, sentiment, emotion, correlation)
- `POST /api/v1/analyze/inspect`:
  - Purpose: Streamlit/디버그 UI 용도로 analyze 결과 + 내부 추적 정보(로직 단계, 실행 로그)를 함께 반환
  - Request: `AnalyzeRequest`
  - Response: `AnalyzeInspectResponse` (request_id, result, logic_steps, logs)
- `POST /api/v1/analyze/inspect/stream`:
  - Purpose: analyze 과정을 SSE로 실시간 표시
  - Content-Type: `text/event-stream`
  - Event Sequence: `start -> log* -> result -> done` (실패 시 `error`)
- `POST /api/v1/sentiment/turn`:
  - Purpose: 발화 턴 단위 감정 분류 (`POS`/`NEG`/`NEUTRAL`)
  - Request: `TurnSentimentRequest` (meeting_id, turn_id, speaker_id?, utterance_text)
  - Response: `TurnSentimentResponse` (label, confidence, evidence)
  - 특이사항:
    - 한국어 중심 텍스트 + 영어 혼합 입력(code-switching) 대응
    - OpenAI SDK(Azure OpenAI) + `json_schema` 구조화 출력 강제
- `GET /healthz`:
  - Purpose: 컨테이너/런타임에서 애플리케이션 프로세스 응답성(liveness) 확인
  - Response: `HealthzResponse` (`status="ok"`)
- `GET /api/env/v1`:
  - Purpose: LLM 연동에 필요한 환경설정 조회 (read-only)
  - Source: `APP_ENV` 기준 `dev.env` 또는 `prod.env` 파일
  - Response: `LLM_API_KEY`, `LLM_ENDPOINT`, `LLM_MODEL_NAME`, `LLM_DEPLOYMENT_NAME`, `LLM_API_VERSION(optional)`, `LLM_MODEL_VERSION(optional)` 원문 값
  - Errors:
    - `422`: 필수 키 누락
    - `500`: env 파일 누락 또는 `APP_ENV` 값 오류
  - 오류 응답 상세:
    - `detail.error_code` + `message_ko` + `message_en` + 상황별 부가 필드(`missing_keys`, `reason`)

## Analyze 알고리즘 일관성 규칙

- `/api/v1/analyze`, `/api/v1/analyze/inspect`, `/api/v1/analyze/inspect/stream`는 반드시 동일한 서비스 메서드(`run_analyze_pipeline`)를 호출해야 합니다.
- 라우트별 차이는 출력 포맷(기본 결과만 반환 vs trace 포함 vs SSE 이벤트 변환)에 한정합니다.

## Topic Extraction 설계

- Analyze는 3개 분기를 병렬 실행하는 fan-out 파이프라인을 사용합니다.
  - Branch Topic: `extract_topics_with_llm`
  - Branch Sentiment: `analyze_sentiment_with_llm`
  - Branch Emotion: `analyze_emotion_with_llm`
- fan-out 결과를 fan-in하여 최종 `AnalyzeResponse(topic, sentiment, emotion, correlation)`를 조합합니다.
- `extract_topics_with_llm`:
  - 입력: 전처리된 회의 텍스트
  - 출력: JSON structured topic 후보 목록(`label`, `confidence`)
  - 모델 추론 강도: `reasoning_effort=none`
  - 출력 토큰 상한: `max_completion_tokens=120`
- `analyze_sentiment_with_llm`:
  - 입력: 원문 텍스트
  - 출력: JSON structured `sentiment.positive/negative/neutral`
  - 모델 추론 강도: `reasoning_effort=minimal`
  - 출력 토큰 상한: `max_completion_tokens=80`
- `analyze_emotion_with_llm`:
  - 입력: 원문 텍스트
  - 출력: JSON structured 기본 8정서 분포
  - 모델 추론 강도: `reasoning_effort=minimal`
  - 출력 토큰 상한: `max_completion_tokens=180`
- 분포 값은 정수 퍼센트(`0~100`)로 정규화되며 합계 100을 보장합니다.
- `correlation`은 topic/sentiment/emotion의 신호를 재조합해 상관도 3축과 요약문을 제공합니다.
- fallback은 사용하지 않으며, 어느 분기에서든 LLM 호출/파싱/검증 실패 시 요청 전체를 502로 실패 처리합니다.
