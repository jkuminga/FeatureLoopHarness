# PROJECT_WORKFLOW.md

하네스가 실제 프로젝트에 적용할 프로젝트 전체 워크플로우를 정의한다.

이 문서는 하네스 자체의 MVP, 아키텍처, DB, API, 프론트엔드 설계를 기록하는 문서가 아니다.
이 문서는 앞으로 하네스를 적용받는 실제 프로젝트가 어떤 순서로 문서를 완성하고 기능 구현 단계로 진입해야 하는지를 설명한다.

---

## Purpose

하네스의 핵심 목적은 실제 구현을 기능 단위로 통제하는 것이다.

이를 위해 기능 구현에 들어가기 전 실제 프로젝트는 다음 산출물을 순서대로 준비해야 한다.

- MVP 정의
- 시스템 아키텍처 정의
- 기능 목록 정의
- 데이터 모델 baseline 정의
- API 경계 정의
- 디자인 지침 정의
- 기능 단위 구현 진입

프로젝트 레벨 상태 전이는 `.flh/runtime/STATE.md`와 `.flh/workflow/*` 설정으로 관리한다.
기능 단위 구현은 `FEATURE_IMPLEMENTATION` 상태에서만 `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`를 기준으로 진행한다.

---

## Runtime Files

프로젝트 전체 워크플로우는 다음 파일들이 제어한다.

- `.flh/runtime/STATE.md`: 현재 상태, 완료 상태, 승인 기록
- `.flh/workflow/flow.yml`: 상태 목록, 상태별 허용 request_type, next state
- `.flh/workflow/state-actions.yml`: 현재 상태에서 에이전트가 수행할 짧은 체크리스트와 허용 write 범위
- `.flh/workflow/docs-spec.yml`: 문서별 완료 판정 기준
- `.flh/workflow/transition-guards.yml`: 상태 전이별 guard 조합

사람이 읽는 설명은 이 문서에 둔다.
훅이 파싱하는 규칙은 `.flh/workflow/*.yml`에 둔다.

---

## State Flow

```text
MVP_DEFINITION
-> ARCHITECTURE_DESIGN
-> FEATURE_INDEX_DEFINITION
-> DATA_MODEL_DEFINITION
-> API_DESIGN
-> FRONTEND_DESIGN
-> FEATURE_IMPLEMENTATION
```

상태 전이는 기본적으로 순차적으로만 진행한다.
현재 상태와 요청이 요구하는 상태 사이에 여러 단계가 있으면, 중간 transition guard를 모두 통과해야 한다.

---

## Manual Step Skip

사용자는 `/d` 문서 및 하네스 제어 모드를 사용해 프로젝트 workflow 단계를 명시적으로 skip 처리할 수 있다.

skip은 하네스가 자동 판정하지 않는다.
특정 단계가 현재 프로젝트에 필요 없는지 여부는 사용자가 책임지는 수동 운영 결정이다.

단, 다음 기반 단계는 이후 workflow 신뢰도를 크게 좌우하므로 skip하지 않는다.

- `MVP_DEFINITION`
- `ARCHITECTURE_DESIGN`
- `FEATURE_INDEX_DEFINITION`

skip된 단계의 산출물은 completed artifact로 가정하지 않는다.
필요하면 `.flh/runtime/STATE.md`에 skip한 상태와 이유를 기록한다.

---

## 1. MVP Definition

실제 프로젝트의 MVP 범위를 정의하는 단계다.

템플릿 문서:

- `docs/MVP.md`

이 문서는 하네스 패키지에서 템플릿으로 제공된다.
실제 프로젝트가 시작되면 사용자가 해당 프로젝트의 내용으로 채운다.

완료 기준은 `.flh/workflow/docs-spec.yml`의 `mvp` 항목을 따른다.

---

## 2. Architecture Design

실제 프로젝트의 시스템 아키텍처를 정의하는 단계다.

템플릿 문서:

- `docs/ARCHITECTURE.md`
- `docs/source-layout.yml`

포함해야 하는 대표 항목:

- 시스템 개요
- 기술 스택
- source layout
- package layout
- testing strategy
- 주요 모듈
- 데이터 흐름
- 외부 의존성
- 실행 환경
- scaffold 정책
- 아키텍처 제약사항

`docs/source-layout.yml`은 아키텍처 단계에서 결정한 source directory, package별 framework/runtime/language/module, testing tool, lint/format tooling을 기계가 읽을 수 있게 기록하는 manifest다.
에이전트는 이 파일을 아키텍처 단계의 필수 결정 체크리스트로 사용하고, TODO 또는 누락 필드가 있으면 사용자에게 먼저 질문한다.
에이전트는 이 파일에 적힌 source directory만 생성하고, 빈 디렉토리에는 `.gitkeep`만 둔다.
아키텍처 단계에서는 framework scaffold나 실제 구현 코드를 생성하지 않는다.
테스트 도구 설치와 설정은 최초 기능 구현 전에 수행하는 source package scaffold baseline에서 다룬다.

완료 기준은 다음을 따른다.

- `.flh/workflow/docs-spec.yml`의 `architecture` 항목
- `.flh/workflow/docs-spec.yml`의 `source_layout` 항목
- `.flh/workflow/transition-guards.yml`의 `ARCHITECTURE_DESIGN_TO_FEATURE_INDEX_DEFINITION` 항목

---

## 3. Feature Index Definition

실제 프로젝트의 기능 후보 목록과 우선순위를 정의하는 단계다.

템플릿 문서:

- `docs/features/feature-index.md`

이 단계에서는 기능별 상세 구현 문서를 만들지 않는다.
기능 목록, 요약, 우선순위, 핵심 요구사항만 정리한다.

기능의 실제 진행 상태는 `feature-index.md`가 아니라 `docs/features/*/` 디렉토리 위치를 기준으로 판단한다.

완료 기준은 `.flh/workflow/docs-spec.yml`의 `feature_index` 항목을 따른다.

---

## 4. Data Model Definition

실제 프로젝트의 데이터 모델 baseline을 정의하는 단계다.
이 단계는 Prisma 파일을 생성하는 단계가 아니라, 프로젝트 전체 DB schema의 단일 truth source인 `docs/DB_SCHEMA.md`를 완성하는 단계다.

템플릿 문서:

- `docs/DB_SCHEMA.md`

금지되는 작업:

- `app/be/prisma/schema.prisma` 생성/수정
- `app/be/prisma/migrations/**` 생성/수정
- `app/be/package.json` 생성/수정
- 루트 `package.json`의 DB forwarding script 생성/수정
- 실제 DB 서버 배포

목표는 `docs/DB_SCHEMA.md`를 `schema.prisma`로 즉시 변환할 수 있는 Prisma-ready 명세로 확정하는 것이다.
entity field, Prisma type, DB type, nullable, default, unique, index, relation, enum, constraint, ownership, lifecycle, Prisma mapping note, migration note가 문서 안에 충분히 구체적으로 있어야 한다.

실제 `schema.prisma`, baseline migration, DB deploy/verify script 생성과 실제 DB 서버 배포/검증은 `FEATURE_IMPLEMENTATION` 상태의 `1.6. Baseline DB Deployment`에서 수행한다.
그 결과는 `.flh/runtime/STATE.md`의 `approvals.database_baseline`에 기록한다.

완료 기준은 다음을 따른다.

- `.flh/workflow/docs-spec.yml`의 `db_schema` 항목
- `.flh/workflow/transition-guards.yml`의 `DATA_MODEL_DEFINITION_TO_API_DESIGN` 항목

---

## 5. API Design

실제 프로젝트의 API 경계와 공통 규칙을 정의하는 단계다.

템플릿 문서:

- `docs/API.md`

포함해야 하는 대표 항목:

- API 영역
- endpoint 초안
- 인증/인가 원칙
- request/response 규칙
- 에러 응답 규칙

완료 기준은 `.flh/workflow/docs-spec.yml`의 `api` 항목을 따른다.

---

## 6. Frontend Design

실제 프로젝트의 디자인 지침을 확정하는 단계다.

산출물:

- `docs/DESIGN.md`

이 단계에 처음 진입하면 사용자에게 다음 중 하나를 선택하게 한다.

1. 외부에서 사용 중인 `DESIGN.md`를 가져와 사용한다.
2. 이 하네스 흐름 안에서 `DESIGN.md`를 함께 작성한다.

외부 `DESIGN.md`를 사용하는 경우 해당 파일은 frontmatter나 하네스 템플릿 섹션을 갖지 않을 수 있다.
이 경우 `.flh/runtime/STATE.md`의 `approvals.design.approved`가 `true`이면 완료 조건을 통과할 수 있다.

직접 작성하는 경우 완료 기준은 `.flh/workflow/docs-spec.yml`의 `design` 항목을 따른다.

전이 조건은 `docs/DESIGN.md` 완료 또는 `approvals.design.approved` 중 하나를 허용한다.

---

## 7. Feature Implementation

프로젝트 전체 워크플로우가 완료되어 기능 단위 구현으로 진입 가능한 상태다.

이 상태 이후 실제 구현은 다음 기준을 따른다.

- `AGENTS.md`
- `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`
- `docs/features/feature-index.md`
- `docs/features/*/FEAT-XXX-*` 내부 기능 문서

첫 기능 구현을 시작하기 전에는 baseline DB deployment를 확인한다.
아직 실제 DB 서버에 baseline schema가 배포/검증되지 않았다면 필요한 환경값을 사용자에게 요청하고 배포/검증을 수행한다.

프로젝트 레벨 훅은 기능 구현 세부사항을 판단하지 않는다.
훅은 프로젝트가 기능 구현 상태에 진입 가능한지만 판단한다.

---

## Template Document Rule

하네스 패키지는 주요 프로젝트 문서를 템플릿 상태로 제공할 수 있다.

템플릿 문서는 존재만으로 완료된 것으로 보지 않는다.
훅의 전이 검증은 다음 기준을 함께 확인한다.

- frontmatter status
- 필수 섹션 존재 여부
- placeholder 제거 여부
- 최소 내용 충족 여부

현재 하네스 구현 과정에서는 실제 프로젝트의 MVP, 아키텍처, DB, API, 디자인 내용을 작성하지 않는다.

---

## Non-goals

프로젝트 레벨 훅은 다음을 하지 않는다.

- 기능 구현 코드 작성
- 기능별 테스트 작성
- 기능별 체크리스트 수행
- 기능별 설계 세부 판단
- 일반 workflow 전이 과정에서의 커밋/푸쉬/머지 수행
- 리팩토링 범위 판단

위 작업은 `FEATURE_IMPLEMENTATION` 상태에서 기능 단위 구현 파이프라인이 관리한다.
단, `/d` 문서 모드에서 사용자가 명시적으로 요청한 문서/하네스 변경 커밋과 푸쉬는 `AGENTS.md`의 `/d` 예외 규칙을 따른다. 머지는 `/d`에서도 허용하지 않는다.
