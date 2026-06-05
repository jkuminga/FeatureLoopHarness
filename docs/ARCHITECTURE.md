---
status: template
---

# ARCHITECTURE.md

이 문서는 실제 프로젝트의 시스템 아키텍처를 정의하기 위한 템플릿이다.

하네스 자체의 아키텍처를 작성하지 않는다.
실제 프로젝트를 시작할 때 이 템플릿을 프로젝트 내용으로 채우고 `status: completed`로 변경한다.

---

## System Overview

{{TODO_SYSTEM_OVERVIEW}}

---

## Tech Stack

{{TODO_TECH_STACK}}

---

## Source Layout

{{TODO_SOURCE_LAYOUT}}

이 섹션의 결정은 `docs/source-layout.yml`에도 기계가 읽을 수 있는 형태로 기록한다.

---

## Package Layout

{{TODO_PACKAGE_LAYOUT}}

---

## Testing Strategy

{{TODO_TESTING_STRATEGY}}

단위, 통합, E2E, 컴포넌트 테스트 도구를 source package별로 결정한다.
이 결정은 `docs/source-layout.yml`의 `source_roots.*.testing`에도 기계가 읽을 수 있는 형태로 기록한다.

---

## Modules

{{TODO_MODULES}}

---

## Data Flow

{{TODO_DATA_FLOW}}

---

## External Dependencies

{{TODO_EXTERNAL_DEPENDENCIES}}

---

## Runtime Environment

{{TODO_RUNTIME_ENVIRONMENT}}

---

## Scaffold Policy

{{TODO_SCAFFOLD_POLICY}}

아키텍처 단계에서는 필요한 source directory와 `.gitkeep`만 생성한다.
프레임워크 scaffold와 실제 구현 코드는 기능 구현 단계에서 다룬다.

---

## Constraints

{{TODO_CONSTRAINTS}}
