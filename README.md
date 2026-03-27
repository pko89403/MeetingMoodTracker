# Meeting Mood Tracker

A FastAPI-based application that analyzes meeting transcripts to accurately identify conversation topics and overall participant moods. Built strictly with Specification-Driven Development (SDD) principles.

## 한국어 우선 개발 가이드

- 본 프로젝트는 한국어 사용자/개발자 경험을 기본값으로 둡니다.
- 회의 발화 입력은 한국어를 우선 지원하며, 한/영 혼합 발화도 지원합니다.
- 코드 식별자는 영어를 유지하고, 문서/설명/docstring은 한국어 중심으로 관리합니다.

## Turn Sentiment API

- Endpoint: `POST /api/v1/sentiment/turn`
- Purpose: classify one meeting turn utterance into:
  - `POS`
  - `NEG`
  - `NEUTRAL`
- Request fields:
  - `meeting_id`
  - `turn_id`
  - `speaker_id` (optional)
  - `utterance_text`
- Response fields:
  - `label`
  - `confidence` (`0.0` - `1.0`)
  - `evidence`

## LLM Environment Config API

- Endpoint: `GET /api/env/v1`
- Reads env file by `APP_ENV`:
  - `APP_ENV=dev` or unset -> `dev.env`
  - `APP_ENV=prod` -> `prod.env`
- Returns raw values:
  - `LLM_API_KEY`
  - `LLM_ENDPOINT`
  - `LLM_MODEL_NAME`
  - `LLM_DEPLOYMENT_NAME`
  - `LLM_MODEL_VERSION` (optional, sentiment service API version source)
- Error behavior:
  - `422` if required keys are missing
  - `500` if env file is missing or `APP_ENV` is invalid
  - 오류 응답 `detail`에는 `error_code`, `message_ko`, `message_en`가 포함됩니다.

## 운영 시 유의사항

- Azure OpenAI 리소스 네트워크 정책(VNet/Firewall)이 닫혀 있으면 감정분류 호출이 실패합니다.
- 자해/자살 관련 문구 등은 Azure Content Filter 정책에 의해 차단될 수 있습니다.

Use `example.env` as the template. Keep `dev.env` and `prod.env` local only.

## LLM-as-Judge Offline Evaluation

- Script: `scripts/evaluate_sentiment_with_judge.py`
- Input: JSONL with `utterance_text`, `predicted_label` and optional IDs
- Output: JSON report with agreement rate and per-turn judge rationale
