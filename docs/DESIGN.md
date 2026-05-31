---
status: template
---

# DESIGN.md

이 문서는 실제 프로젝트의 프론트엔드 디자인 지침을 저장하는 산출물이다.

하네스 자체의 디자인 지침을 작성하지 않는다.
실제 프로젝트 진행 시 다음 두 방식 중 하나를 선택한다.

- 외부에서 사용 중인 `DESIGN.md`를 이 경로에 가져오고 `.flh/runtime/STATE.md`의 `approvals.design.approved`를 `true`로 기록한다.
- 이 하네스 흐름 안에서 직접 `DESIGN.md`를 작성하고 `status: completed`로 변경한다.

외부 `DESIGN.md`는 frontmatter가 없을 수 있다.
그 경우 문서 형식 검증 대신 사용자 승인 기록을 전이 조건으로 사용한다.

---

## Layout Principles

{{TODO_LAYOUT_PRINCIPLES}}

---

## Component Principles

{{TODO_COMPONENT_PRINCIPLES}}

---

## State Loading and Error

{{TODO_STATE_LOADING_AND_ERROR}}

---

## Form Rules

{{TODO_FORM_RULES}}

---

## Responsive Rules

{{TODO_RESPONSIVE_RULES}}

---

## Accessibility

{{TODO_ACCESSIBILITY}}
