# 환경 설정 운영 가이드 (Environment Configuration Guide)

## 개요

백엔드 서버는 LLM 연동에 필요한 설정을 `APP_ENV` 파라미터 기반으로 로드합니다.

```
APP_ENV=dev   →  backend/dev.env  파일 또는 환경변수에서 읽음
APP_ENV=prod  →  backend/prod.env 파일 또는 환경변수에서 읽음
```

파일이 존재하면 파일을 우선합니다. 파일이 없으면 시스템 환경변수(`os.environ`)에서 읽습니다.
이 구조 덕분에 docker-compose `env_file:`로 주입하거나 로컬 파일로 관리하는 두 방식 모두 동작합니다.

---

## 필수 환경변수 목록

| 키 | 설명 | 예시 |
|---|---|---|
| `LLM_API_KEY` | LLM 서비스 API 키 | Azure OpenAI key |
| `LLM_ENDPOINT` | LLM 서비스 엔드포인트 URL | `https://your.openai.azure.com/` |
| `LLM_MODEL_NAME` | 사용할 모델 이름 | `gpt-5-mini` |
| `LLM_DEPLOYMENT_NAME` | 배포 이름 (Azure는 모델명과 다를 수 있음) | `gpt-5-mini` |

## 선택 환경변수

| 키 | 설명 |
|---|---|
| `LLM_API_VERSION` | API 버전 (Azure OpenAI 전용) |
| `LLM_MODEL_VERSION` | 모델 버전 |

---

## 설정 파일 규칙

### `backend/dev.env`
로컬 개발용 실제 값. **절대 git에 커밋하지 않습니다.**

```env
LLM_API_KEY=실제-api-키
LLM_ENDPOINT=https://your-endpoint.openai.azure.com/
LLM_MODEL_NAME=gpt-5-mini
LLM_DEPLOYMENT_NAME=gpt-5-mini
LLM_API_VERSION=2025-04-01-preview
LLM_MODEL_VERSION=2025-08-07
```

### `backend/example.env`
실제 값 없는 템플릿. git에 커밋됩니다. 새 환경 구성 시 이 파일을 복사해 사용합니다.

```bash
cp backend/example.env backend/dev.env
# 이후 backend/dev.env를 실제 값으로 채웁니다.
```

### `backend/prod.env`
프로덕션용. 실제 배포 환경에서는 파일 대신 환경변수 주입을 권장합니다.

---

## 실행 방법

### 로컬 직접 실행

```bash
cd backend
APP_ENV=dev uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

또는 `dev.env` 파일이 있으면 `APP_ENV` 없이도 자동으로 `dev`로 동작합니다.

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### docker-compose 개발 환경

```bash
# 프로젝트 루트에서
docker compose -f docker-compose.dev.yml up --build
```

`docker-compose.dev.yml`은 다음을 수행합니다:
- `env_file: ./backend/dev.env` → dev.env의 모든 키를 컨테이너 환경변수로 주입
- `APP_ENV=dev` → 환경변수 fallback 경로로 읽도록 지정
- 파일 볼륨 마운트 없이도 작동 (환경변수 fallback 덕분)

### Docker 단독 실행 (파일 마운트 방식)

```bash
docker run -d \
  --name meeting-mood-tracker-api \
  -v $(pwd)/backend/dev.env:/app/dev.env:ro \
  -e APP_ENV=dev \
  -e FASTAPI_SERVER_PORT=8000 \
  -p 8000:8000 \
  meeting-mood-tracker-api
```

### Docker 단독 실행 (환경변수 직접 주입 방식)

```bash
docker run -d \
  --name meeting-mood-tracker-api \
  --env-file ./backend/dev.env \
  -e APP_ENV=dev \
  -e FASTAPI_SERVER_PORT=8000 \
  -p 8000:8000 \
  meeting-mood-tracker-api
```

---

## 설정 로딩 흐름

```
서버 시작
  └─ GET /api/v1/env 또는 LLM 호출 시
       └─ get_llm_config(app_env_raw=None)
            └─ os.getenv("APP_ENV")  →  "dev" (기본값)
                 └─ resolve_env_file_path()  →  backend/dev.env
                      ├─ 파일 존재?  →  dotenv_values(dev.env) 읽기
                      └─ 파일 없음?  →  os.environ 전체 읽기 (fallback)
                           └─ REQUIRED_LLM_KEYS 추출 및 검증
                                ├─ 성공  →  LlmConfigResponse 반환
                                └─ 누락  →  HTTP 422 LLM_CONFIG_MISSING_KEY
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `LLM_CONFIG_MISSING_KEY` (422) | 필수 키 누락 | `dev.env` 또는 환경변수에 필수 키 추가 |
| `LLM_CONFIG_LOAD_FAILED` (500) | `APP_ENV` 값이 `dev`/`prod` 외 값 | `APP_ENV` 환경변수 확인 |
| `ANALYZE_LLM_FAILURE` (502) | LLM 서비스 연결 실패 | `LLM_ENDPOINT`, `LLM_API_KEY` 값 확인 |
| 컨테이너에서 `your-api-key` 응답 | 이전 이미지로 실행 중 | `--build` 옵션으로 재빌드 또는 `env_file` + `APP_ENV=dev` 주입 확인 |
