---
status: template
---

# DB_SCHEMA.md

이 문서는 실제 프로젝트의 데이터 모델 baseline을 정의하기 위한 템플릿이다.

하네스 자체의 DB schema를 작성하지 않는다.
실제 프로젝트를 시작할 때 이 템플릿을 프로젝트 내용으로 채우고 `status: completed`로 변경한다.

이 문서는 프로젝트 전체 데이터 모델의 단일 truth source다.
`DATA_MODEL_DEFINITION` 단계에서는 실제 `schema.prisma` 또는 migration 파일을 생성하지 않는다.
대신 이 문서를 `FEATURE_IMPLEMENTATION` 단계의 `1.6. Baseline DB Deployment`에서 즉시 `schema.prisma`로 변환할 수 있는 수준의 명세로 완성한다.

---

## Core Entities

{{TODO_CORE_ENTITIES}}

| Entity | Purpose | Owner | Lifecycle | Notes |
| --- | --- | --- | --- | --- |
| {{TODO_ENTITY}} | {{TODO_PURPOSE}} | {{TODO_OWNER}} | {{TODO_LIFECYCLE}} | {{TODO_NOTES}} |

---

## Entity Specifications

{{TODO_ENTITY_SPECIFICATIONS}}

각 entity는 Prisma model로 변환 가능하도록 field 단위로 작성한다.

### {{TODO_ENTITY_NAME}}

| Field | Prisma Type | DB Type | Required | Default | Unique | Index | Relation | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| id | {{TODO_PRISMA_TYPE}} | {{TODO_DB_TYPE}} | yes | {{TODO_DEFAULT}} | yes | primary | none | {{TODO_NOTES}} |

필드 작성 규칙:

- `Required`는 `yes` 또는 `no`로 작성한다.
- nullable field는 `Required`를 `no`로 작성한다.
- default 값이 없으면 `none`으로 작성한다.
- unique/index가 없으면 `none`으로 작성한다.
- relation field는 아래 `Relation Specifications`의 relation ID를 참조한다.

---

## Relation Specifications

{{TODO_RELATION_SPECIFICATIONS}}

| Relation ID | From Entity | From Field | To Entity | To Field | Cardinality | Required | onDelete | onUpdate | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| {{TODO_RELATION_ID}} | {{TODO_FROM_ENTITY}} | {{TODO_FROM_FIELD}} | {{TODO_TO_ENTITY}} | {{TODO_TO_FIELD}} | {{TODO_CARDINALITY}} | {{TODO_REQUIRED}} | {{TODO_ON_DELETE}} | {{TODO_ON_UPDATE}} | {{TODO_NOTES}} |

관계 작성 규칙:

- `Cardinality`는 `one-to-one`, `one-to-many`, `many-to-one`, `many-to-many` 중 하나로 작성한다.
- foreign key를 가지는 field를 `From Field`에 명확히 작성한다.
- `onDelete`와 `onUpdate`는 Prisma에서 사용할 값을 명시한다.
- relation name이 필요하면 `Notes`에 Prisma relation name을 작성한다.

---

## Indexes and Constraints

{{TODO_INDEXES_AND_CONSTRAINTS}}

| Entity | Type | Fields | Name | Purpose | Notes |
| --- | --- | --- | --- | --- | --- |
| {{TODO_ENTITY}} | {{TODO_INDEX_OR_UNIQUE_OR_CONSTRAINT}} | {{TODO_FIELDS}} | {{TODO_NAME}} | {{TODO_PURPOSE}} | {{TODO_NOTES}} |

---

## Enums

{{TODO_ENUMS}}

| Enum | Values | Used By | Notes |
| --- | --- | --- | --- |
| {{TODO_ENUM_NAME}} | {{TODO_VALUES}} | {{TODO_USED_BY}} | {{TODO_NOTES}} |

---

## Ownership and Permissions

{{TODO_OWNERSHIP_AND_PERMISSIONS}}

| Entity | Owner Field | Access Rule | Write Rule | Delete Rule | Notes |
| --- | --- | --- | --- | --- | --- |
| {{TODO_ENTITY}} | {{TODO_OWNER_FIELD}} | {{TODO_ACCESS_RULE}} | {{TODO_WRITE_RULE}} | {{TODO_DELETE_RULE}} | {{TODO_NOTES}} |

---

## ID Strategy

{{TODO_ID_STRATEGY}}

ID 작성 규칙:

- 각 entity의 primary key 방식을 명시한다.
- UUID, cuid, autoincrement 등 생성 전략을 명시한다.
- 외부 공개 ID와 내부 DB ID가 다르면 둘 다 명시한다.

---

## Lifecycle Policy

{{TODO_LIFECYCLE_POLICY}}

각 entity의 생성, 수정, soft delete, hard delete, archive 정책을 명시한다.

---

## Common Field Policy

{{TODO_COMMON_FIELD_POLICY}}

공통 field가 있다면 적용 대상과 Prisma 변환 규칙을 명시한다.

| Field | Prisma Type | Default | Applies To | Notes |
| --- | --- | --- | --- | --- |
| {{TODO_FIELD}} | {{TODO_PRISMA_TYPE}} | {{TODO_DEFAULT}} | {{TODO_ENTITIES}} | {{TODO_NOTES}} |

---

## Prisma Mapping Notes

{{TODO_PRISMA_MAPPING_NOTES}}

`FEATURE_IMPLEMENTATION`의 `1.6. Baseline DB Deployment`에서 `schema.prisma`를 생성할 때 적용할 Prisma mapping 규칙을 작성한다.

- model 이름
- field 이름
- relation 이름
- `@map` 또는 `@@map` 필요 여부
- provider별 주의사항
- unsupported type 또는 raw SQL 필요 여부

---

## Migration Notes

{{TODO_MIGRATION_NOTES}}

`DATA_MODEL_DEFINITION` 단계에서는 Prisma 파일이나 migration 파일을 생성하지 않는다.
이 섹션에는 `1.6. Baseline DB Deployment`에서 `schema.prisma`, baseline migration, deploy/verify script를 생성할 때 필요한 주의사항만 기록한다.
