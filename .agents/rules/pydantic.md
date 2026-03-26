# Rule: 모든 데이터 모델은 Pydantic을 사용 (Pydantic Enforcement)

모든 함수나 API 라우터가 통신하며 주고받는 핵심 페이로드(Payload)나 직렬화된 데이터 모델은 자바스크립트스러운 원시 딕셔너리(`dict`) 포맷이 아닌 `pydantic.BaseModel`을 상속받은 정의된 객체여야 합니다.

- Request 및 Response 페이로드 모델은 무조건 사전에 정의되어야 합니다.
- 스키마 객체는 모두 구조상 최하위인 `app/types/` 하위에 위치시켜야 순환 참조를 막을 수 있습니다.
- 파이썬의 타입 힌팅(Type Hinting)을 항상 꼼꼼하게 병기(Strict Typing)해야 합니다.
