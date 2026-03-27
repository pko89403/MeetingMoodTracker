# Design Guidelines

## 도메인 목표
회의록(Transcript)과 시뮬레이션 엔진에서 넘어온 대화 스크립트를 분석하여 **의제(Topic)**, **핵심 논의점**, **회의 분위기(Mood - 예: 건설적, 갈등, 지루함 등)**를 도출하는 API를 제공합니다.

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
  - Response: `AnalyzeResponse` (topic, mood, confidence)
- `POST /api/v1/sentiment/turn`:
  - Purpose: 발화 턴 단위 감정 분류 (`POS`/`NEG`/`NEUTRAL`)
  - Request: `TurnSentimentRequest` (meeting_id, turn_id, speaker_id?, utterance_text)
  - Response: `TurnSentimentResponse` (label, confidence, evidence)
  - 특이사항:
    - 한국어 중심 텍스트 + 영어 혼합 입력(code-switching) 대응
    - OpenAI SDK(Azure OpenAI) + `json_schema` 구조화 출력 강제
- `GET /api/env/v1`:
  - Purpose: LLM 연동에 필요한 환경설정 조회 (read-only)
  - Source: `APP_ENV` 기준 `dev.env` 또는 `prod.env` 파일
  - Response: `LLM_API_KEY`, `LLM_ENDPOINT`, `LLM_MODEL_NAME`, `LLM_DEPLOYMENT_NAME`, `LLM_MODEL_VERSION(optional)` 원문 값
  - Errors:
    - `422`: 필수 키 누락
    - `500`: env 파일 누락 또는 `APP_ENV` 값 오류
  - 오류 응답 상세:
    - `detail.error_code` + `message_ko` + `message_en` + 상황별 부가 필드(`missing_keys`, `reason`)
