---
status: template
---

# DB_SCHEMA.md

이 문서는 실제 프로젝트의 데이터 모델 baseline을 정의하기 위한 템플릿이다.

하네스 자체의 DB schema를 작성하지 않는다.
실제 프로젝트를 시작할 때 이 템플릿을 프로젝트 내용으로 채우고 `status: completed`로 변경한다.

---

## Core Entities

{{TODO_CORE_ENTITIES}}

---

## Relationships

{{TODO_RELATIONSHIPS}}

---

## Ownership and Permissions

{{TODO_OWNERSHIP_AND_PERMISSIONS}}

---

## ID Strategy

{{TODO_ID_STRATEGY}}

---

## Lifecycle Policy

{{TODO_LIFECYCLE_POLICY}}

---

## Common Fields

{{TODO_COMMON_FIELDS}}

---

## Prisma Baseline

{{TODO_PRISMA_BASELINE}}

이 단계에서는 `app/be/prisma/schema.prisma`와 baseline migration 산출물을 준비한다.
Prisma CLI와 `@prisma/client`는 backend package인 `app/be/package.json`에서 관리한다.
루트 `package.json`은 필요할 경우 `app/be`의 DB script를 호출하는 forwarding script만 둔다.
실제 DB 서버 배포와 검증은 첫 기능 구현을 시작하기 전에 `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`의 `Baseline DB Deployment` 단계에서 수행한다.
