# OPTIMIZATION_CHECKLIST.md

하네스 템플릿 배포/운영 전 점검할 최적화 후보 목록이다.

이 문서는 즉시 수정해야 하는 작업 목록이 아니라, 현재 구조를 더 안정적으로 만들기 위한 개선 후보를 기록한다.

---

## High Priority

- [x] `README.md`, `docs/docs-map.md`의 삭제된 문서 참조 제거
  - `DOCUMENTS_TODO.md`, `CODEX_HOOK_FAILURE_ANALYSIS.md`, `CODEX_HOOK_STABILITY_RESEARCH.md`는 정리 과정에서 삭제됐다.
  - 남은 문서에서 해당 파일들을 참조하면 템플릿 사용자가 혼란을 겪을 수 있다.

- [x] 빈 feature 상태 디렉토리 추적 보장
  - `docs/features/ready/`, `active/`, `blocked/`, `review/`에 `.gitkeep`이 필요하다.
  - 빈 디렉토리는 git에 포함되지 않으므로 템플릿 배포 시 누락될 수 있다.

- [x] `package.json`과 `.husky/pre-commit` 정리
  - 현재 `npm test`는 실패하도록 되어 있다.
  - `.husky/pre-commit`은 예전 `src/`, `docs/features/${feature_name}.md` 구조를 기준으로 한다.
  - 현재 하네스 구조에 맞게 다시 작성하거나 제거 여부를 결정해야 한다.

- [x] `docs-spec.yml`의 `required_item_fields` 실제 검증 추가
  - `feature_index.required_item_fields`가 정의되어 있지만 현재 hook은 이 필드들을 검사하지 않는다.
  - `feature-index.md`가 ID, 이름, 우선순위, 핵심 요구사항 없이도 통과할 수 있다.

- [x] `STATE.md` 저장 시 nested `approvals` 구조 보존
  - 현재 `write_state()`는 dict를 inline JSON 형태로 쓸 수 있다.
  - `approvals.design.approved` 같은 계층 구조는 YAML 형태로 안정적으로 보존하는 편이 좋다.

---

## Medium Priority

- [x] request pattern/alias를 설정 파일로 분리
  - 현재 `REQUEST_PATTERNS`, `REQUEST_ALIASES`가 `hooks/user_prompt_submit.py` 안에 직접 들어 있다.
  - 향후 운영자가 쉽게 수정하려면 `codex/workflow/request-patterns.yml` 같은 파일로 분리할 수 있다.

- [ ] `UNKNOWN` / `low confidence` 정책 강화 여부 결정
  - 현재는 additional context를 붙여 allow한다.
  - 실사용 중 오작동이 많으면 low confidence는 block 또는 clarification 전용으로 바꿀 수 있다.
  - 현재는 의도적으로 보류한다. 지금 정책은 유지한다.

- [x] `optional_commands` 처리 방식 결정
  - `transition-guards.yml`에는 실행하지 않는 참고 명령을 `suggested_commands`로 둔다.
  - `DATA_MODEL_DEFINITION`에서는 서버 DB 배포를 강제하지 않고, `suggested_commands`로 로컬 schema 검증 명령만 남긴다.
  - 실제 DB 서버 배포/검증은 첫 기능 구현 전 `Baseline DB Deployment` 단계에서 수행한다.

- [x] 진행 상황 질문 시 참고 범위 확장 검토
  - 현재 `AGENTS.md`는 progress question에서 `active/**`, `review/**`만 참고한다.
  - “다음 할 일” 답변 품질을 높이려면 `ready/**`, `backlog/**`도 참고하도록 조정할 수 있다.

---

## Low Priority

- [x] `docs/QUALITY_SCORE.md` 예시 row 정리
  - 현재 예시 row가 실제 점수처럼 보일 수 있다.
  - 빈 테이블과 작성 예시를 분리하면 템플릿 사용자가 더 이해하기 쉽다.

- [x] README troubleshooting 섹션 추가
  - hook이 block되지 않을 때 확인할 항목을 정리한다.
  - 예: `/hooks` trust 상태, git repo root, wrapper 실행 권한, `.codex/hooks.json` 경로.
