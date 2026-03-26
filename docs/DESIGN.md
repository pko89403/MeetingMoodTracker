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

## 핵심 API
- `POST /api/v1/analyze`:
  - Request: `MeetingAnalyzeRequest` (meeting_id, transcript_text)
  - Response: `MeetingAnalyzeResponse` (overall_mood, topics, severity)
