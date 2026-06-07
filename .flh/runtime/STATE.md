---
current_state: MVP_DEFINITION
completed_states: []
approvals: {}
last_transition: null
updated_at: null
---

# STATE

이 파일은 하네스가 적용될 실제 프로젝트의 runtime workflow state를 저장한다.
기계가 읽는 데이터는 위 YAML frontmatter뿐이며, 이 Markdown 본문은 Codex와 유지보수자를 위한 작성 가이드다.

## Frontmatter Fields

- `current_state`: 현재 프로젝트 workflow 상태.
- `completed_states`: 완료되었거나 상태 전이 과정에서 통과 처리된 workflow 상태 목록.
- `approvals`: 이후 hook 또는 agent gate에서 재사용할 승인/검증 기록.
- `last_transition`: 마지막 상태 전이.
- `updated_at`: 마지막 runtime state 갱신 시각.

## Approval Recording Policy

`approvals`는 모든 상태 전이마다 기록하는 로그가 아니다.
문서 완료만으로 판단하기 어렵고, 나중에 hook 또는 agent가 gate 조건으로 다시 확인해야 하는 승인/검증 결과만 기록한다.

Codex는 사용자 승인 또는 실제 검증 없이 approval을 임의로 추가하지 않는다.
비밀값, API key, token, password, DB connection string은 절대 `STATE.md`에 기록하지 않는다.

### `approvals.design`

외부 `docs/DESIGN.md`를 프로젝트 디자인 가이드로 사용하기로 사용자가 승인한 경우 기록한다.

```yaml
approvals:
  design:
    source: external
    path: docs/DESIGN.md
    approved: true
```

### `approvals.source_scaffold`

첫 기능 구현 전에 source package scaffold baseline이 생성되고 커밋된 경우 기록한다.

```yaml
approvals:
  source_scaffold:
    created: true
    based_on: docs/source-layout.yml
    package_manager: npm
    created_at: 2026-06-07T00:00:00Z
```

### `approvals.database_baseline`

첫 기능을 `docs/features/active/`로 이동하기 전에 실제 개발 DB baseline 배포와 검증이 성공한 경우 기록한다.

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
