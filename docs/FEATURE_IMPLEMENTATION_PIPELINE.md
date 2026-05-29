---
status: completed
---

# FEATURE_IMPLEMENTATION_PIPELINE.md

`FEATURE_IMPLEMENTATION` 상태에서만 실행하는 기능 단위 구현 파이프라인을 정의한다.

이 문서는 하네스 자체 구현 규칙이 아니라, 하네스를 적용받는 실제 프로젝트에서 기능 하나를 설계하고 구현할 때 따르는 실행 규칙이다.

---

## Overview

기능 단위 구현 파이프라인은 하나의 기능만 대상으로 한다.

프로젝트 전체 상태가 `FEATURE_IMPLEMENTATION`이 아닐 경우 이 문서를 실행 규칙으로 적용하지 않는다.

진행 순서:

```text
0. Preparation
1. Design
1.5 Baseline DB Deployment
2. Branch and Worktree
3. Implementation and Tests
4. Verification
4.5 Quality Scoring
5. Feedback Loop
6. Commit Merge and Cleanup
```

---

## Feature State Directories

기능 구현 상태는 `docs/features/` 내부 디렉토리 위치를 기준으로 판단한다.

```text
docs/features/
  feature-index.md
  backlog/
  ready/
  active/
  blocked/
  review/
  done/
  postponed/
```

각 디렉토리 의미:

- `backlog/`: 설계 대상으로 선택되었지만 아직 `SPEC.md`, `CHECKLIST.md`, `TEST_CASES.md`가 완성되지 않은 기능
- `ready/`: 기능 설계 문서 3개가 작성되어 구현 가능한 기능
- `active/`: 브랜치/워크트리 생성 후 현재 구현 중인 기능
- `blocked/`: 외부 의존성이나 결정 대기로 멈춘 기능
- `review/`: 최초 구현 초안, 검증, 품질 점수 작성이 끝났고 사용자가 확인/수정 중인 기능
- `done/`: 사용자가 최종 완료 승인한 기능
- `postponed/`: 보류 또는 연기된 기능

`docs/features/feature-index.md`는 기능 목록, 우선순위, 요약을 관리한다.
기능의 실제 진행 상태는 디렉토리 위치를 source of truth로 본다.

동시성 규칙:

- `active/` 또는 `review/`에 기능 디렉토리가 있으면 새 기능 구현을 시작하지 않는다.
- `review/`에는 동시에 하나의 기능만 둘 수 있다.
- `review/`에 기능이 하나 있으면 사용자의 수정 요청은 그 기능을 대상으로 간주한다.
- `review/` 기능에는 full feature implementation pipeline을 다시 적용하지 않는다.

---

## 0. Preparation

기능 구현 파이프라인의 대상 기능을 확정하고 기능 디렉토리를 준비한다.

규칙:

- 사용자가 구현하고자 하는 기능을 `docs/features/feature-index.md`에서 확인한다.
- 기능이 존재하지 않으면 `feature-index.md`에 기능 ID, 이름, 요약, 우선순위, 핵심 요구사항을 추가한다.
- 사용자 요청으로 새로 추가된 기능은 기본 우선순위를 `highest`로 지정한다.
- 해당 기능 디렉토리가 없으면 `docs/features/backlog/FEAT-XXX-name/`에 생성한다.
- 이미 `ready/`, `active/`, `blocked/`, `review/`, `done/`, `postponed/` 중 하나에 동일 기능 디렉토리가 있으면 새로 생성하지 않고 기존 디렉토리를 사용한다.
- `active/` 또는 `review/`에 다른 기능이 있으면 새 기능 준비를 시작하지 않고 먼저 해당 기능을 완료하거나 보류할지 사용자에게 확인한다.
- `done/`에 있는 기능의 변경 요청이면 새 기능으로 추가할지 기존 기능 개선으로 처리할지 사용자 확인 후 진행한다.

---

## 1. Design

사용자가 요청한 단위 기능의 상세 설계를 작성한다.

설계 문서는 `docs/features/backlog/FEAT-XXX-name/` 내부에 생성한다.

필수 문서:

- `SPEC.md`: 기능 목표, 범위, 비범위, 흐름, 요구사항, 완료 기준, 제약조건
- `CHECKLIST.md`: 실제 구현 시 진행할 체크리스트
- `TEST_CASES.md`: E2E 테스트 파일 생성 시 참고할 테스트 케이스

DB 변경 규칙:

- DB 변경이 필요한 경우 먼저 `SPEC.md`에 변경 제안을 작성한다.
- `docs/DB_SCHEMA.md`와 충돌 여부를 확인한다.
- 공통 데이터 모델에 영향이 있으면 `docs/DB_SCHEMA.md`를 함께 업데이트한다.
- Prisma schema/migration 반영은 구현 단계에서 수행한다.

설계 완료 조건:

- `SPEC.md`, `CHECKLIST.md`, `TEST_CASES.md`가 모두 존재한다.
- 기능 범위와 비범위가 명확하다.
- E2E 관점의 수용 기준이 있다.

설계가 완료되면 기능 디렉토리를 `docs/features/backlog/`에서 `docs/features/ready/`로 이동한다.

---

## Baseline DB Deployment

실제 DB 서버 배포는 프로젝트 전체 `DATA_MODEL_DEFINITION` 단계가 아니라, `FEATURE_IMPLEMENTATION` 상태에서 첫 기능 구현을 시작하기 전에 한 번 수행한다.

목적:

- `docs/DB_SCHEMA.md`와 `prisma/schema.prisma`로 확정한 baseline schema를 실제 개발 DB에 반영한다.
- 첫 기능 구현부터 실제 DB 연결을 기준으로 개발할 수 있게 한다.
- DB provider, 환경, 검증 여부를 비밀값 없이 기록한다.

실행 시점:

- `docs/features/active/`로 첫 기능을 이동하기 전
- `codex/runtime/STATE.md`에 `approvals.database_baseline.verified: true`가 없을 때

절차:

1. 사용자에게 사용할 DB provider와 environment를 확인한다.
2. 필요한 환경변수/API key/connection string을 사용자에게 요청한다.
3. 비밀값은 `.env`, 배포 플랫폼 secret, 또는 사용자가 지정한 안전한 위치에만 둔다.
4. 비밀값을 docs, feature 문서, `STATE.md`에 기록하지 않는다.
5. baseline migration을 실제 DB에 적용한다.
6. 실제 DB 연결과 baseline schema 반영 여부를 검증한다.
7. 성공하면 `codex/runtime/STATE.md`에 비밀값 없는 승인 기록만 남긴다.

권장 명령 이름:

```text
npm run db:deploy
npm run db:verify
```

기록 예시:

```yaml
approvals:
  database_baseline:
    provider: supabase
    environment: development
    deployed: true
    verified: true
    verified_at: 2026-05-26T00:00:00Z
```

규칙:

- `db:deploy`는 baseline migration을 실제 DB에 적용한다.
- `db:verify`는 실제 DB 연결, migration 적용 여부, 핵심 테이블 존재 여부를 확인한다.
- `db:verify`가 실패하면 첫 기능 구현을 시작하지 않는다.
- 이미 `approvals.database_baseline.verified: true`면 이 단계는 생략할 수 있다.

---

## 2. Branch and Worktree

구현 시작 전에 baseline DB deployment 상태를 확인하고, 기능 디렉토리를 `docs/features/ready/`에서 `docs/features/active/`로 이동한다.

규칙:

- 모든 구현 작업은 별도 워크트리에서 진행한다.
- 첫 기능 구현 전 `codex/runtime/STATE.md`의 `approvals.database_baseline.verified`가 `true`인지 확인한다.
- 아직 baseline DB가 검증되지 않았다면 먼저 `Baseline DB Deployment`를 수행한다.
- 브랜치 이름은 기능 디렉토리명을 기반으로 한다.
- 워크트리 이름도 기능 디렉토리명을 기반으로 한다.
- 구현 시작 전 `SPEC.md`, `CHECKLIST.md`, `TEST_CASES.md`를 다시 확인한다.

예시:

```text
docs/features/active/FEAT-001-login
branch: feat/001-login
worktree: FEAT-001-login
```

---

## 3. Implementation and Tests

구현은 해당 기능의 `SPEC.md` 범위와 `Non-goals`를 반드시 준수한다.

규칙:

- 구현 작업은 `SPEC.md`의 Scope/Non-goals를 준수하고, `CHECKLIST.md`의 작업 항목을 기준으로 순차 진행한다.
- 구현 중 완료한 작업 항목은 `CHECKLIST.md`에 반영한다.
- `CHECKLIST.md`에 없는 작업이 필요해지면 코드 수정 전에 `SPEC.md`와 `CHECKLIST.md`를 먼저 갱신한다.
- 관련 없는 리팩토링을 하지 않는다.
- 기능 범위를 벗어난 구현을 하지 않는다.
- 프론트엔드 구현 시 `docs/DESIGN.md`를 참고한다.
- DB 변경 시 `docs/DB_SCHEMA.md`와 충돌 여부를 확인한다.
- 단위 테스트 파일은 테스트 대상 파일과 같은 디렉토리에 생성한다.
- E2E 테스트 파일은 `TEST_CASES.md`를 참고하여 `tests/e2e/feat-xxx-feature.e2e.spec.ts`에 생성한다.

요구사항 변경 규칙:

- 구현 중 요구사항 변경이 발생하면 코드 수정 전에 `SPEC.md`, `CHECKLIST.md`, `TEST_CASES.md`를 먼저 갱신한다.
- 변경이 프로젝트 공통 데이터 모델에 영향을 주면 `docs/DB_SCHEMA.md`도 함께 갱신한다.

---

## 4. Verification

검증은 다음 순서로 진행한다.

```text
1. Lint / Typecheck
2. Unit Test
3. Integration Test
4. E2E Test
```

규칙:

- 검증을 통과하지 못하면 커밋하지 않는다.
- 특정 검증 명령이 프로젝트에 없으면 생략하지 말고 누락 사실을 기록한다.
- E2E 결과는 기능의 실제 동작 판단에 우선적으로 참고한다.

---

## Quality Scoring

E2E 검증 이후, 커밋 전에 구현된 기능의 품질 점수를 기록한다.

작성 위치:

- 상세 점수: `docs/features/active/FEAT-XXX-name/QUALITY_SCORE.md`
- 전역 요약: `docs/QUALITY_SCORE.md`

상세 점수 파일에는 다음 항목을 100점 기준으로 기록한다.

| Category | Points |
| --- | ---: |
| Requirement fit | 30 |
| Test result and coverage | 25 |
| E2E user flow stability | 20 |
| Architecture and scope compliance | 15 |
| UX, error, and edge case handling | 10 |

판정 기준:

- `90-100`: 우수
- `80-89`: 양호
- `70-79`: 통과 가능, 개선 후보
- `0-69`: 재작업 필요

규칙:

- 총점이 `70`점 미만이면 커밋하지 않고 수정 후 재검증한다.
- E2E 실패, `SPEC.md` scope 위반, `docs/DB_SCHEMA.md` 충돌, 보안 위험, 주요 사용자 플로우 파손은 점수와 관계없이 커밋 금지다.
- 기능 디렉토리를 `review/`로 이동할 때 상세 `QUALITY_SCORE.md`도 함께 이동한다.
- `docs/QUALITY_SCORE.md`에는 기능 ID, 기능명, 점수, 등급, 평가일, 상세 점수 파일 경로만 요약한다.

---

## Review Patch Flow

`docs/features/review/`에 있는 기능은 사용자 검토/수정 단계다.

규칙:

- full feature implementation pipeline을 다시 실행하지 않는다.
- `review/`에 있는 단일 기능을 현재 수정 대상으로 본다.
- 사용자 수정 요청은 요청된 변경만 최소 범위로 수행한다.
- 관련 문서, 관련 코드, 관련 테스트만 수정한다.
- 필요한 경우 관련 테스트만 실행한다.
- 변경이 품질 판단에 영향을 주면 기능 디렉토리의 `QUALITY_SCORE.md`와 `docs/QUALITY_SCORE.md`를 갱신한다.
- 커밋, 머지, `done/` 이동은 사용자가 명시적으로 요청한 경우에만 수행한다.

`review/`에 기능이 여러 개 있으면 작업하지 말고 사용자에게 하나만 남기도록 요청한다.

완료 승인 예시:

```text
이 기능 완료해줘
done으로 옮겨줘
최종 승인
이제 끝
```

사용자가 완료를 승인하면 기능 디렉토리를 `docs/features/review/`에서 `docs/features/done/`으로 이동하고 관련 인덱스를 갱신한다.

---

## 5. Feedback Loop

검증 실패 시 다음 루프를 따른다.

```text
검증 실패
-> 원인 수정
-> 관련 테스트 재실행
-> 전체 검증 재실행
```

규칙:

- 문법 오류를 제외한 대부분의 수정은 E2E 테스트 결과와 `TEST_CASES.md`를 기준으로 판단한다.
- 수정이 `SPEC.md` 범위를 벗어나면 구현을 멈추고 설계 문서를 먼저 갱신한다.
- 외부 의존성이나 결정 대기로 진행할 수 없으면 기능 디렉토리를 `blocked/`로 이동한다.

---

## 6. Commit Merge and Cleanup

검증을 통과한 경우에만 커밋한다.

커밋 메시지:

```text
feat(scope): description
```

머지 이후 후처리:

1. 메인 브랜치에 정상 머지 여부를 확인한다.
2. 로컬 브랜치와 동기화 상태를 확인한다.
3. 머지가 완료된 워크트리와 브랜치를 삭제한다.
4. 관련 임시/테스트/디버그 파일을 정리한다.
5. 해당 기능 디렉토리를 `docs/features/review/`로 이동한다.
6. `docs/features/feature-index.md`에 review 상태, 요약, 참조 경로를 갱신한다.
7. `docs/QUALITY_SCORE.md`의 해당 기능 점수와 상세 점수 파일 경로를 갱신한다.
8. 사용자의 최종 완료 승인이 있기 전까지 `done/`으로 이동하지 않는다.

---

## Non-goals

기능 단위 구현 파이프라인은 다음을 하지 않는다.

- 프로젝트 전체 워크플로우 상태 전이 판단
- MVP/아키텍처/API/프론트엔드 프로젝트 문서의 최초 완료 판단
- 여러 기능을 한 번에 구현
- 사용자가 요청하지 않은 리팩토링
- 실패한 검증을 무시한 커밋
