---
status: template
---

# QUALITY_SCORE.md

기능별 최종 품질 점수를 한눈에 보기 위한 전역 인덱스다.

이 파일에는 상세 평가 내용을 쓰지 않는다.
상세 평가는 각 기능 디렉토리의 `QUALITY_SCORE.md`에 기록한다.

전역 인덱스의 목적은 리팩토링, 수정, 개선이 필요한 기능을 빠르게 찾는 것이다.

---

## Score Index

| Feature ID | Feature | Score | Grade | Last Evaluated | Notes | Detail |
| --- | --- | ---: | --- | --- | --- | --- |

첫 기능 평가가 완료되면 이 표에 행을 추가한다.

예시:

```md
| FEAT-001 | Login | 82 | B | 2026-05-26 | E2E stable, minor UX improvement candidate | docs/features/review/FEAT-001-login/QUALITY_SCORE.md |
```

---

## Grade Rule

| Score | Grade | Meaning |
| ---: | --- | --- |
| 90-100 | A | Stable and polished |
| 80-89 | B | Good, minor improvements possible |
| 70-79 | C | Acceptable, improvement candidate |
| 0-69 | D | Rework required |

---

## Gate Rule

- `70`점 이상이면 커밋 가능하다.
- `70`점 미만이면 수정 후 재검증한다.
- 치명 조건이 있으면 점수와 관계없이 커밋하지 않는다.

치명 조건:

- E2E failure
- SPEC scope violation
- DB_SCHEMA conflict
- Security risk
- Broken primary user flow
