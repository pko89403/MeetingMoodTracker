# Meeting Mood Tracker

A FastAPI-based application that analyzes meeting transcripts to accurately identify conversation topics and overall participant moods. Built strictly with Specification-Driven Development (SDD) principles.

## LLM Environment Config API

- Endpoint: `GET /api/env/v1`
- Reads env file by `APP_ENV`:
  - `APP_ENV=dev` or unset -> `dev.env`
  - `APP_ENV=prod` -> `prod.env`
- Returns raw values:
  - `LLM_API_KEY`
  - `LLM_ENDPOINT`
  - `LLM_MODEL`
- Error behavior:
  - `422` if required keys are missing
  - `500` if env file is missing or `APP_ENV` is invalid

Use `example.env` as the template. Keep `dev.env` and `prod.env` local only.
