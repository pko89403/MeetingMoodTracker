# Repository Detail

`Meeting Mood Tracker` 저장소를 GitHub Repository 소개, 내부 공유, 온보딩 문서에 재사용할 수 있도록 정리한 상세 설명입니다.

## 한 줄 소개

회의 대화 데이터를 `프로젝트 → 회의 → 에이전트 → 발화 턴` 구조로 저장하고, 감정 흐름·회의 시그널·대화 패턴을 분석 및 시각화하는 conversation intelligence 저장소입니다.

## 상세 소개

Meeting Mood Tracker는 회의록이나 발화 턴 데이터를 입력으로 받아, 단순한 긍/부정 분류를 넘어 다음 정보를 구조화합니다.

- 회의 전체 주제(Topic)
- 감정 분포(Sentiment)
- 기본 정서와 회의 특화 시그널(Emotion / Meeting Signals)
- 에이전트별 패턴과 턴 단위 흐름
- React Flow 및 Timeline 기반 탐색 UI

백엔드는 FastAPI + Pydantic 기반의 계층형 구조를 따르고, 프론트엔드는 React/Vite로 회의 관계도와 시계열 변화를 동시에 보여줍니다. 또한 SSE 기반 inspect 흐름과 Streamlit 콘솔을 통해 분석 과정을 디버깅할 수 있습니다.

## 어떤 문제를 해결하나

- 회의 요약만으로는 드러나지 않는 감정 흐름과 긴장도 변화를 파악합니다.
- 누가 어떤 순간에 대화 흐름을 주도했는지 턴 단위로 추적합니다.
- 프로젝트 단위로 회의 데이터를 축적하고, 이후 조회/대시보드에서 재활용할 수 있게 만듭니다.
- 한국어 중심 회의 데이터와 한/영 혼합 발화(code-switching)를 기본 시나리오로 다룹니다.

## 핵심 기능

- `POST /api/v1/analyze`: 회의록 전체에 대한 topic / sentiment / emotion / correlation 분석
- `POST /api/v1/sentiment/turn`: 발화 턴 단위 감정 라벨 분류
- `POST /api/v1/analyze/inspect`, `.../stream`: 분석 단계 추적 및 SSE 스트리밍
- `POST /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`: project-aware turn 저장
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}`: 회의 overview 조회
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/turns`: timeline/detail용 turn 조회
- `GET /api/v1/projects/{project_id}/meetings/{meeting_id}/agents`: agent aggregate 조회
- React Flow 보드와 Timeline 페이지를 통한 회의 탐색 UI

## 기술 스택

- Backend: FastAPI, Pydantic, Python, uv
- LLM Integration: Azure OpenAI, structured output(JSON schema)
- Frontend: React, Vite, Tailwind, React Flow, ApexCharts
- Storage: JSON repository 기반 project-aware 저장 구조
- Quality Gate: custom harness, Ruff, Pytest, Playwright

## 저장소 구조 관점의 강점

- 아키텍처 계층이 `types -> config -> repo -> service -> runtime -> ui`로 고정되어 있어 유지보수 경계가 명확합니다.
- project/meeting/agent/turn 식별자를 중심으로 저장 및 조회 계약이 정렬되어 있습니다.
- 분석 API, inspect 디버깅 경로, 시각화 UI가 하나의 흐름으로 연결됩니다.
- 한국어 개발자 경험과 한국어 사용자 운영 문구를 기본값으로 유지합니다.

## 대상 사용자

- 회의 분석 SaaS 또는 conversation intelligence 제품을 만들고 싶은 개발자
- 감정/정서 분석 파이프라인과 시각화 대시보드를 함께 다루는 팀
- 한국어 중심 회의 데이터 실험 환경이 필요한 AI/데이터 제품 팀
- project-aware 저장 모델과 FastAPI 계층형 아키텍처 예제가 필요한 개발자

## 현재 저장소 상태

- 백엔드 분석 API, inspect 흐름, project-aware read/write API가 구현되어 있습니다.
- 프론트엔드는 Flow 보드와 Timeline 뷰를 통해 회의 흐름을 탐색할 수 있습니다.
- Docker 기반 실행 경로와 health check가 정리되어 있습니다.
- README, docs, agent 운영 문서가 함께 관리되는 progressive disclosure 구조를 따릅니다.

## Suggested GitHub About

### Short Description (KO)

프로젝트/회의/에이전트/발화 턴 구조로 회의 감정 흐름과 대화 시그널을 분석·시각화하는 FastAPI + React 저장소

### Short Description (EN)

Project-aware meeting conversation intelligence repo for analyzing and visualizing mood flow, signals, and turn-level patterns with FastAPI and React.

### Topics

- `fastapi`
- `react`
- `vite`
- `azure-openai`
- `meeting-analytics`
- `sentiment-analysis`
- `emotion-analysis`
- `conversation-intelligence`
- `react-flow`
- `timeline-visualization`
- `korean-nlp`

## Suggested README / 소개문 첫 문장

Meeting Mood Tracker는 회의 발화 데이터를 project-aware 구조로 저장하고, 감정 흐름과 회의 시그널을 Flow 보드 및 Timeline UI로 탐색할 수 있게 만드는 conversation intelligence 저장소입니다.
