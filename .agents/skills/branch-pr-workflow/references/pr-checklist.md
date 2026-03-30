# PR Checklist

## Pre-push
- 대상 브랜치 확인: `git branch --show-current`
- 변경 범위 점검: `pr_scope_report.sh` 결과 재확인
- 테스트/린트/하네스 실행 결과 확보
- 커밋 메시지/단위 재확인

## Push
- `git push -u origin <branch>`

## PR 본문 템플릿
제목:
- `<area>: <핵심 변경>`

본문:
- 목적:
  - 이번 변경이 해결하는 문제
- 주요 변경:
  - 항목 2~5개
- 검증:
  - 실행한 명령/결과
- 리스크/롤백:
  - 예상 영향과 되돌리는 방법
- 제외 범위:
  - 이번 PR에 의도적으로 넣지 않은 항목
