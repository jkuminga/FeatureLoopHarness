# docs-map.md

하네스에서 사용하는 문서와 설정 파일의 목차다.

현재 레포는 특정 제품/서비스 프로젝트를 진행하는 레포가 아니라, 실제 프로젝트 진행을 통제할 하네스 템플릿과 운영 구조를 만드는 레포다.

---

## Runtime

- `.flh/runtime/STATE.md`: 현재 프로젝트 워크플로우 상태, 완료 상태, 승인 기록

---

## Workflow Config

- `.flh/workflow/flow.yml`: 상태 목록, 상태별 허용 request_type, next state
- `.flh/workflow/state-actions.yml`: 현재 상태에서 에이전트가 수행할 짧은 체크리스트와 허용 write 범위
- `.flh/workflow/docs-spec.yml`: 문서별 완료 판정 기준
- `.flh/workflow/transition-guards.yml`: 상태 전이별 guard 조합
- `.flh/workflow/request-patterns.yml`: 사용자 프롬프트를 request_type으로 분류하기 위한 strong/alias 패턴

---

## Hook Runtime

- `.codex/hooks/user-prompt-submit.sh`: Codex가 실행하는 얇은 hook wrapper
- `.flh/hooks/user_prompt_submit.py`: 실제 `UserPromptSubmit` hook 본체

---

## Harness Operation Docs

- `.flh/docs/PROJECT_WORKFLOW.md`: 하네스가 실제 프로젝트에 적용할 프로젝트 전체 워크플로우 설명
- `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`: `FEATURE_IMPLEMENTATION` 상태에서만 실행하는 기능 단위 구현 파이프라인
- `docs/QUALITY_SCORE.md`: 기능별 최종 품질 점수 전역 인덱스
- `AGENTS.md`: 에이전트가 반드시 따라야 하는 전역 안전 규칙

---

## Actual Project Templates

다음 문서들은 하네스가 실제 프로젝트에 제공할 템플릿이다.
현재 하네스 구현 과정에서 실제 프로젝트 내용을 채우지 않는다.

- `docs/MVP.md`: 실제 프로젝트의 MVP 정의 템플릿
- `docs/ARCHITECTURE.md`: 실제 프로젝트의 시스템 아키텍처 템플릿
- `docs/source-layout.yml`: 아키텍처 단계에서 결정한 source directory manifest 템플릿
- `docs/features/feature-index.md`: 실제 프로젝트의 기능 목록 템플릿
- `docs/DB_SCHEMA.md`: 실제 프로젝트의 데이터 모델 baseline 템플릿
- `docs/API.md`: 실제 프로젝트의 API 설계 템플릿
- `docs/DESIGN.md`: 실제 프로젝트의 디자인 지침 산출물. 외부 파일을 가져오거나 하네스 안에서 직접 작성한다.

---

## Feature State Directories

- `docs/features/backlog/`: 설계 대상으로 선택되었지만 아직 설계 문서가 완성되지 않은 기능
- `docs/features/ready/`: 설계 문서 작성 완료 후 구현 대기 중인 기능
- `docs/features/active/`: 현재 구현 중인 기능
- `docs/features/blocked/`: 외부 의존성이나 결정 대기로 멈춘 기능
- `docs/features/review/`: 최초 구현 초안 완료 후 사용자 검토/수정 중인 기능. 동시에 하나만 허용한다.
- `docs/features/done/`: 사용자가 최종 완료 승인한 기능
- `docs/features/postponed/`: 보류 또는 연기된 기능
