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

이 파이프라인은 기능의 최초 구현 루프만 다룬다.
커밋, 머지, 후처리 후 기능 디렉토리를 `docs/features/review/`로 이동하면 이 파이프라인은 종료된다.
`review/`에 있는 기능의 사용자 수정 요청은 이 문서가 아니라 `AGENTS.md`의 review 규칙을 따른다.

진행 순서:

```text
0. Preparation
1. Design
1.5 Source Package Scaffold Baseline
1.6 Baseline DB Deployment
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

각 기능 디렉토리는 구현 검증 산출물을 저장하기 위해 `artifacts/` 디렉토리를 포함한다.
비어 있는 `artifacts/` 디렉토리를 유지해야 하면 `artifacts/.gitkeep`을 둔다.

동시성 규칙:

- `active/` 또는 `review/`에 기능 디렉토리가 있으면 새 기능 구현을 시작하지 않는다.
- `review/`에는 동시에 하나의 기능만 둘 수 있다.

---

## 0. Preparation

기능 구현 파이프라인의 대상 기능을 확정하고 기능 디렉토리를 준비한다.

규칙:

- 사용자가 구현하고자 하는 기능을 `docs/features/feature-index.md`에서 확인한다.
- 기능이 존재하지 않으면 `feature-index.md`에 기능 ID, 이름, 요약, 우선순위, 핵심 요구사항을 추가한다.
- 사용자 요청으로 새로 추가된 기능은 기본 우선순위를 `highest`로 지정한다.
- 해당 기능 디렉토리가 없으면 `docs/features/backlog/FEAT-XXX-name/`에 생성한다.
- 기능 디렉토리를 새로 생성할 때 `artifacts/`도 함께 생성한다.
- 비어 있는 `artifacts/`를 git에 남겨야 하면 `artifacts/.gitkeep`을 생성한다.
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

필수 디렉토리:

- `artifacts/`: 구현 검증 산출물을 저장하는 디렉토리

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

## 1.5. Source Package Scaffold Baseline

source package scaffold baseline은 첫 기능 구현 전에 프로젝트 공통 package 기반을 준비하는 단계다.

목적:

- 기능 구현과 프로젝트 기반 설정을 분리한다.
- `docs/source-layout.yml`에 기록된 package, framework, runtime, language, module, testing, lint/format 결정을 실제 package 기반으로 반영한다.
- DB deployment와 기능 구현에서 사용할 package script 기반을 준비한다.

실행 시점:

- 첫 기능 branch/worktree를 만들기 전
- `.flh/runtime/STATE.md`에 `approvals.source_scaffold.created: true`가 없을 때

절차:

1. `docs/source-layout.yml`을 읽고 source root, package manager, workspace, framework, runtime, language, module, testing, tooling 결정을 확인한다.
2. scaffold 생성에 더 필요한 정보가 있는지 확인한다.
3. 추가 정보가 필요하면 사용자에게 질문한다.
4. 추가 정보 없이 기본값 또는 생략으로 진행할 수 있는 경우에도 사용자에게 진행 허락을 받는다.
5. main/master에서 source package scaffold baseline을 생성한다.
6. 생성된 파일이 scaffold baseline 허용 범위 안에 있는지 확인한다.
7. scaffold baseline을 커밋한다.
8. 성공하면 `.flh/runtime/STATE.md`에 비밀값 없는 승인 기록만 남긴다.

허용 범위:

- package-level `package.json`
- package manager/workspace 설정
- lint/typecheck/test script
- TypeScript 또는 runtime config
- lint/format/test runner config
- 최소 entry file
- Prisma를 사용하는 backend package의 기본 연결 구조
- 빈 source directory를 유지하기 위한 `.gitkeep`

금지 범위:

- 실제 기능 화면 구현
- 실제 API route 구현
- 도메인 로직 구현
- 기능 테스트 작성
- 특정 기능 요구사항 반영
- 대규모 UI component 생성

기록 예시:

```yaml
approvals:
  source_scaffold:
    created: true
    based_on: docs/source-layout.yml
    package_manager: npm
    created_at: 2026-06-07T00:00:00Z
```

규칙:

- scaffold baseline은 특정 기능 산출물이 아니라 프로젝트 공통 기반이다.
- scaffold baseline이 완료되기 전에는 기능 branch/worktree를 만들지 않는다.
- 이미 `approvals.source_scaffold.created: true`면 이 단계는 생략할 수 있다.
- 비밀값, API key, token, DB connection string은 `STATE.md`에 기록하지 않는다.

---

## 1.6. Baseline DB Deployment

실제 Prisma schema 생성, baseline migration 생성, DB 서버 배포는 프로젝트 전체 `DATA_MODEL_DEFINITION` 단계가 아니라, `FEATURE_IMPLEMENTATION` 상태에서 첫 기능 구현을 시작하기 전에 한 번 수행한다.

목적:

- `docs/DB_SCHEMA.md`의 Prisma-ready 명세를 기준으로 `app/be/prisma/schema.prisma`를 반드시 생성한다.
- 생성한 `schema.prisma`에서 baseline migration을 만들고 실제 개발 DB에 반영한다.
- 첫 기능 구현부터 실제 DB 연결을 기준으로 개발할 수 있게 한다.
- migration tool, database, environment, 검증 여부를 비밀값 없이 기록한다.

실행 시점:

- `docs/features/active/`로 첫 기능을 이동하기 전
- `.flh/runtime/STATE.md`에 `approvals.source_scaffold.created: true`가 기록된 뒤
- `.flh/runtime/STATE.md`에 `approvals.database_baseline.verified: true`가 없을 때

절차:

1. `docs/source-layout.yml`과 `docs/DB_SCHEMA.md`를 확인한다.
2. DB-backed project인지 확인한다.
3. `docs/DB_SCHEMA.md`의 Entity Specifications, Relation Specifications, Indexes and Constraints, Enums, Prisma Mapping Notes, Migration Notes를 기준으로 `app/be/prisma/schema.prisma`를 생성한다.
4. `schema.prisma` 생성에 필요한 정보가 `docs/DB_SCHEMA.md`에 부족하면 임의 추론하지 말고 사용자에게 질문하고, 필요하면 먼저 `docs/DB_SCHEMA.md`를 보강한다.
5. 생성한 `schema.prisma`가 `docs/DB_SCHEMA.md`의 entity, field, relation, enum, index, constraint를 빠짐없이 반영하는지 대조한다.
6. backend package에 Prisma CLI, `@prisma/client`, DB deploy/verify script가 없으면 source scaffold baseline 범위 안에서 추가한다.
7. 사용자에게 사용할 DB provider 또는 Prisma-compatible database, environment를 확인한다.
8. 필요한 환경변수/API key/connection string을 사용자에게 요청한다.
9. 비밀값은 `.env`, 배포 플랫폼 secret, 또는 사용자가 지정한 안전한 위치에만 둔다.
10. 비밀값을 docs, feature 문서, `STATE.md`에 기록하지 않는다.
11. baseline migration을 생성하고 실제 DB에 적용한다.
12. 실제 DB 연결과 baseline schema 반영 여부를 검증한다.
13. 성공하면 `.flh/runtime/STATE.md`에 비밀값 없는 승인 기록만 남긴다.

권장 명령 이름:

```text
npm run db:deploy
npm run db:verify
```

기록 예시:

```yaml
approvals:
  database_baseline:
    migration_tool: prisma
    database: postgresql
    environment: development
    deployed: true
    verified: true
    verified_at: 2026-05-26T00:00:00Z
```

규칙:

- Prisma baseline은 backend package인 `app/be/prisma/`를 기준으로 이 단계에서 생성한다.
- `DATA_MODEL_DEFINITION` 단계는 `schema.prisma`를 만들지 않는다. 이 단계에서는 반드시 `docs/DB_SCHEMA.md`를 실행 가능한 Prisma schema로 변환한다.
- 루트 `db:*` script는 필요하면 `app/be`의 Prisma script로 위임한다.
- DB SaaS 이름은 필수값이 아니다. Prisma migration과 verify command가 충분히 동작하면 `DATABASE_URL` 같은 env만으로 진행할 수 있다.
- Supabase, Neon, RDS처럼 서비스 특성에 따라 direct URL, pooler URL, SSL, migration 권한이 달라지는 경우에는 사용자에게 서비스 정보를 질문한다.
- `db:deploy`는 baseline migration을 실제 DB에 적용한다.
- `db:verify`는 실제 DB 연결, migration 적용 여부, 핵심 테이블 존재 여부를 확인한다.
- 필요한 env가 없으면 사용자에게 필요한 값을 안내하고 중단한다. 사용자가 env를 채운 뒤 같은 구현 요청을 다시 보내면 현재 파일과 `STATE.md` 기준으로 다시 판단한다.
- `db:verify`가 실패하면 첫 기능 구현을 시작하지 않는다.
- 이미 `approvals.database_baseline.verified: true`면 이 단계는 생략할 수 있다.

---

## 2. Branch and Worktree

구현 시작 전에 source scaffold baseline과 baseline DB deployment 상태를 확인하고, 기능 디렉토리를 `docs/features/ready/`에서 `docs/features/active/`로 이동한다.

규칙:

- 모든 구현 작업은 별도 워크트리에서 진행한다.
- 첫 기능 구현 전 `.flh/runtime/STATE.md`의 `approvals.source_scaffold.created`가 `true`인지 확인한다.
- 아직 source scaffold baseline이 완료되지 않았다면 먼저 `Source Package Scaffold Baseline`을 수행한다.
- DB-backed project라면 첫 기능 구현 전 `.flh/runtime/STATE.md`의 `approvals.database_baseline.verified`가 `true`인지 확인한다.
- DB-backed project인데 아직 baseline DB가 검증되지 않았다면 먼저 `Baseline DB Deployment`를 수행한다.
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

기능 디렉토리를 `docs/features/review/`로 이동하면 최초 구현 파이프라인은 종료된다.
이후 사용자 검토/수정 요청은 `AGENTS.md`의 review 규칙을 따른다.

---

## Non-goals

기능 단위 구현 파이프라인은 다음을 하지 않는다.

- 프로젝트 전체 워크플로우 상태 전이 판단
- MVP/아키텍처/API/프론트엔드 프로젝트 문서의 최초 완료 판단
- 여러 기능을 한 번에 구현
- 사용자가 요청하지 않은 리팩토링
- 실패한 검증을 무시한 커밋
