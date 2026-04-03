# MoodTracker Frontend

## 실행

```bash
npm i
npm run dev
```

## 대시보드 진입

프론트엔드는 이제 `project_id` + `meeting_id` 조합으로 회의를 조회합니다.

- 입력 폼에서 두 값을 모두 입력
- 또는 URL query params 사용:

```text
/?project_id=project-frontend-demo&meeting_id=meeting-issue27-short-live
```

기본 API 주소는 `http://localhost:8000`이며, 필요하면 `VITE_API_URL`로 변경할 수 있습니다.
