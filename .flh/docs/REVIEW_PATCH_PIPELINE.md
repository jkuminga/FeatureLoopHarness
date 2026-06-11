# Review Patch Pipeline

Review Patch Pipeline은 최초 기능 구현이 끝나고 `docs/features/review/`에 위치한 기능에 대해, 사용자의 수정 요청을 처리하는 lightweight pipeline이다.

이 단계는 full feature implementation pipeline을 다시 실행하지 않는다.
이미 구현된 기능을 대상으로 최소 범위의 수정, 검증, 품질 점수 갱신, 최종 완료 처리를 수행한다.

---

## 1. Target Feature

`docs/features/review/`에 기능 디렉토리가 있으면, 사용자의 수정 요청은 기본적으로 해당 기능을 대상으로 한다.

`review/`에는 동시에 하나의 기능만 존재해야 한다.
`review/`에 기능이 있는 동안에는 새 기능 구현을 시작하지 않는다.

수정 요청이 review 대상 기능과 관련 있는지 먼저 확인한다.
요청 범위가 현재 review 기능과 맞지 않거나, 새 기능 구현에 가까운 경우에는 바로 수정하지 말고 사용자에게 확인한다.

---

## 2. Review Branch and Worktree

Review patch가 source file 변경을 포함하는 경우 main/master에서 직접 수정하거나 커밋하지 않는다.

리뷰 대상 기능마다 하나의 `fix/*` branch/worktree를 생성한다.
이 branch/worktree는 해당 기능이 `docs/features/done/`으로 이동하기 전까지 계속 재사용한다.

예시:

```text
feature: docs/features/review/FEAT-001-login
branch: fix/FEAT-001-login-review
worktree: FEAT-001-login-review
```

이미 해당 review branch/worktree가 존재하면 새로 만들지 않고 기존 branch/worktree에서 이어서 작업한다.

source 변경이 없는 docs-only review patch도 review branch/worktree가 이미 있으면 같은 branch/worktree에 포함한다.
이렇게 하면 사용자가 review 중 요청한 변경사항을 하나의 기능 단위 흐름으로 유지할 수 있다.

---

## 3. Patch Scope

수정은 사용자가 요청한 내용에 한정한다.

관련 없는 리팩토링, 기능 추가, 설계 변경은 하지 않는다.
수정 중 요구사항 변경이 필요하다고 판단되면, 코드 수정 전에 해당 기능의 `SPEC.md`, `CHECKLIST.md`, `TEST_CASES.md`를 먼저 갱신한다.

변경 범위가 데이터 모델, API 계약, 공통 디자인 규칙에 영향을 준다면 관련 문서도 함께 확인한다.
단, review patch는 기존 기능을 보정하는 흐름이므로 변경 범위가 커지면 사용자에게 먼저 보고한다.

---

## 4. Patch Log and Artifacts

Review patch 과정에서 생성되는 검증 자료와 실패 기록은 해당 기능 디렉토리의 `artifacts/review-patches/` 아래에 저장한다.

권장 경로:

```text
docs/features/review/FEAT-XXX-name/artifacts/review-patches/YYYY-MM-DD-short-summary/
```

저장할 수 있는 항목:

- 사용자 수정 요청 요약
- 실행한 검증 명령
- Playwright screenshot, trace, report
- 실패 원인과 재시도 기록
- 환경 문제로 검증하지 못한 경우의 blocker 기록

---

## 5. Verification

수정 후 관련 테스트를 실행한다.

UI/UX 변경이 포함된 경우 Playwright 기반 검증을 수행한다.
Playwright 검증이 실패하면 원인을 수정하고 다시 검증한다.

환경, 의존성, 외부 서비스 문제로 검증이 불가능하면 임의로 통과 처리하지 않는다.
해당 blocker와 확인 가능한 증거를 `artifacts/review-patches/` 아래에 기록하고 사용자에게 보고한다.

---

## 6. Quality Score

수정이 기능 품질에 영향을 주면 해당 기능의 `QUALITY_SCORE.md`를 갱신한다.

품질 점수 변경이 필요한 경우:

- 요구사항 충족 범위가 바뀐 경우
- 테스트 또는 검증 결과가 바뀐 경우
- UI/UX 안정성이 개선되거나 악화된 경우
- 에러 처리, 접근성, edge case 대응이 바뀐 경우

단순 문구 수정이나 품질 판단에 영향을 주지 않는 작은 정리는 품질 점수를 갱신하지 않을 수 있다.

---

## 7. Commit Policy

Review patch의 기본 커밋 정책은 사용자 명시 커밋 방식이다.

에이전트는 review patch 요청을 받으면 수정, 검증, 필요한 artifacts 기록, 품질 점수 갱신까지 수행할 수 있다.
다만 커밋은 사용자가 명시적으로 커밋을 요청했을 때 해당 review branch에서 수행한다.

사용자가 커밋을 요청하기 전까지는 같은 review branch/worktree에 변경사항을 유지할 수 있다.
사소한 수정 요청이 여러 번 이어지는 경우, 사용자가 커밋을 요청하는 시점에 하나의 커밋으로 묶을 수 있다.
변경 목적이 서로 다르거나 사용자가 분리를 요청한 경우에는 여러 커밋으로 나눌 수 있다.

main/master에는 source 변경을 직접 커밋하지 않는다.
커밋 범위는 review 대상 기능에 한정한다.

커밋 전에는 다음을 확인한다.

- 변경이 사용자 요청 범위 안에 있는지
- 관련 테스트 또는 검증을 실행했는지
- 필요한 artifacts가 feature directory 아래에 기록되었는지
- 품질 점수 갱신이 필요한지

---

## 8. Completion

사용자가 명시적으로 해당 기능의 검토 완료를 승인하기 전까지 기능 디렉토리는 `docs/features/review/`에 유지한다.

완료 승인으로 볼 수 있는 표현은 명확해야 한다.
예를 들어 "완료", "done으로 이동", "최종 승인", "이 기능 끝"처럼 review 종료 의도가 분명해야 한다.

사용자가 완료를 승인하면 다음을 수행한다.

1. 최종 검증을 실행한다.
2. 필요한 품질 점수와 feature index를 갱신한다.
3. 기능 디렉토리를 `docs/features/review/`에서 `docs/features/done/`으로 이동한다.
4. 아직 커밋되지 않은 review 변경사항이 있으면 review branch에서 커밋한다.
5. review branch를 main/master로 merge한다.
6. review worktree와 branch를 정리한다.

완료 승인이 없다면 review branch/worktree는 유지하고, 이후 같은 review 기능에 대한 수정 요청은 같은 branch/worktree에서 이어서 처리한다.

---

## 9. Conflict Handling

Review patch 중 충돌이 발생하면 관련 파일과 충돌 이유를 먼저 파악한다.

충돌 해결이 단순하고 review 요청 범위 안에 있으면 최소 수정으로 해결한다.
충돌 원인이 요구사항 변경, 데이터 모델 변경, API 계약 변경처럼 review 범위를 넓히는 경우에는 임의로 해결하지 말고 사용자에게 보고한다.

---

## 10. Rules Summary

- `docs/features/review/`에 있는 기능이 review patch의 기본 대상이다.
- review patch는 full feature implementation pipeline을 다시 실행하지 않는다.
- source 변경이 있으면 main/master에서 직접 커밋하지 않는다.
- 하나의 review 기능은 `done/`으로 이동하기 전까지 하나의 `fix/*` branch/worktree를 재사용한다.
- review patch commit은 사용자가 명시적으로 커밋을 요청했을 때 수행한다.
- 수정 범위는 사용자가 요청한 내용에 한정한다.
- UI/UX 변경은 Playwright 기반 검증을 수행한다.
- 검증 자료와 blocker는 `artifacts/review-patches/` 아래에 기록한다.
- 품질에 영향이 있으면 `QUALITY_SCORE.md`를 갱신한다.
- 사용자가 명시적으로 완료를 승인하기 전까지 `review/`에서 `done/`으로 이동하지 않는다.
