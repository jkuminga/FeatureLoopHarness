# Feature Loop Harness

![image](https://res.cloudinary.com/dddvvp9de/image/upload/v1780124834/FeatureLoopHarness_zndch9.png)

Feature Loop Harness, 또는 `flh`,는 Codex로 프로젝트를 진행할 때 설계, 문서화, 기능 구현, 리뷰, 커밋 흐름을 일정한 순서로 제한하는 workflow harness다.

핵심은 Codex `UserPromptSubmit` hook, `AGENTS.md`, 문서 템플릿, pre-commit guard를 함께 사용해 “아직 준비되지 않은 작업”이 바로 실행되거나 커밋되는 것을 막는 것이다.

상세 매뉴얼은 [HARNESS_MANUAL.md](HARNESS_MANUAL.md)를 참고한다.

## Install

### Requirements

- `git`
- `node`
- `npm`
- `python3`
- `PyYAML`
- `Codex CLI`

Codex Desktop App을 주로 사용하더라도 project-local hook 승인에는 Codex CLI 사용을 권장한다.

### Clone

```sh
git clone https://github.com/jkuminga/FeatureLoopHarness <PROJECT_DIR>
cd <PROJECT_DIR>
```

새 프로젝트 repo로 사용할 경우 `origin`을 본인 repo로 바꾼다.

```sh
git remote remove origin
git remote add origin <YOUR_PROJECT_REPO_URL>
git push -u origin main
```

기본 브랜치가 `master`라면 `main` 대신 `master`를 사용한다.

### Dependencies

```sh
npm install
```

이 명령은 Husky와 lint-staged를 설치하고 Git pre-commit hook을 연결한다.

### Enable Codex Hook

flh는 사용자 요청이 Codex에 전달되기 전에 `UserPromptSubmit` hook으로 현재 상태와 요청 의도를 검사한다.

Codex CLI를 프로젝트 루트에서 실행한다.

```sh
codex
```

최초 실행 시 CLI가 project-local hook을 감지하고 실행 승인 여부를 물어볼 수 있다. 자동 안내가 나오지 않으면 Codex CLI 안에서 다음 명령을 실행한다.

```text
/hooks
```

`UserPromptSubmit` hook의 설정과 스크립트 경로를 확인한 뒤, Codex가 해당 hook을 실행해도 된다고 승인한다. hook 파일이나 `.codex/hooks.json`을 수정하면 다시 승인해야 할 수 있다.

### Verify

```sh
npm test
printf '아키텍처 설계하자' | .codex/hooks/user-prompt-submit.sh
codex exec '아키텍처 설계하자'
```

설정이 정상이라면 Codex 실행 시 `UserPromptSubmit` hook이 동작하고, 현재 workflow state에 맞지 않는 요청은 block된다.

## Start A Project

처음 상태는 `.flh/runtime/STATE.md`의 `current_state: MVP_DEFINITION`이다.

Codex에서 MVP 정의부터 시작한다.

```text
MVP 정리하자
```

이후 각 단계의 문서를 완성하면 다음 단계 요청을 보낸다. hook은 현재 상태, 요청 의도, 문서 완료 조건을 확인한 뒤 허용 가능한 경우에만 상태를 전이한다.

```text
MVP 정리하자
아키텍처 설계하자
기능 목록 정리하자
데이터 모델 설계하자
API 설계하자
프론트 디자인 정리하자
기능 구현 시작하자
```

## Core Flow

```text
MVP_DEFINITION
-> ARCHITECTURE_DESIGN
-> FEATURE_INDEX_DEFINITION
-> DATA_MODEL_DEFINITION
-> API_DESIGN
-> FRONTEND_DESIGN
-> FEATURE_IMPLEMENTATION
```

주요 파일:

- `.flh/runtime/STATE.md`: 현재 workflow state
- `.flh/workflow/flow.yml`: 상태와 허용 request type
- `.flh/workflow/state-actions.yml`: 상태별 작업 규칙
- `.flh/workflow/docs-spec.yml`: 문서 완료 조건
- `.flh/workflow/transition-guards.yml`: 상태 전이 guard
- `.flh/workflow/request-patterns.yml`: 자연어 요청 분류 패턴
- `AGENTS.md`: Codex 실행 규칙

## Prefix Modes

flh는 사용자 프롬프트 prefix로 작업 의도를 강하게 제한한다.

### `/q`

질문 모드다.

- 답변만 허용한다.
- 파일 생성, 수정, 삭제를 하지 않는다.
- `STATE.md`를 갱신하지 않는다.
- 테스트, 커밋, push, merge, workflow pipeline을 실행하지 않는다.

### `/d`

문서 및 하네스 제어 모드다.

- `docs/`, `.flh/`, `AGENTS.md`, `README.md`, `.codex/`, `tests/hooks/`, `.husky/`, `package.json`, `package-lock.json` 같은 문서/하네스 유지보수 파일만 수정한다.
- source 구현 작업을 하지 않는다.
- 사용자가 명시적으로 요청한 경우에만 커밋 또는 push할 수 있다.
- merge는 하지 않는다.

### No Prefix

일반 작업 모드다.

- 현재 `.flh/runtime/STATE.md`의 `current_state`를 기준으로 동작한다.
- 기능 구현은 `current_state`가 `FEATURE_IMPLEMENTATION`일 때만 진행한다.
- 현재 state에서 허용되지 않는 요청은 hook 또는 agent 규칙에 의해 block된다.

## Must-Know Policies

### 1. `STATE.md`가 기준이다

`.flh/runtime/STATE.md`의 YAML frontmatter가 유일한 machine-readable runtime state다.

에이전트와 hook은 항상 이 값을 기준으로 현재 단계와 허용 작업을 판단한다.

### 2. 문서는 `completed`가 되어야 다음 단계로 간다

각 단계의 문서는 `.flh/workflow/docs-spec.yml` 조건을 만족해야 한다.

필수 섹션, YAML 필드, TODO 제거 조건을 만족하지 못하면 상태 전이가 block될 수 있다.

### 3. `docs/source-layout.yml`은 source 변경의 기준이다

source file 변경이 감지되면 pre-commit guard는 `docs/source-layout.yml`을 기준으로 source root와 package 정보를 판단한다.

이 파일이 `completed` 상태가 아니거나 source root가 맞지 않으면 source 변경 커밋이 막힐 수 있다.

### 4. `active/` 또는 `review/`에 기능이 있으면 새 기능을 시작하지 않는다

기능 상태는 `docs/features/` 아래 디렉토리 위치로 판단한다.

```text
backlog -> ready -> active -> review -> done
```

`docs/features/active/` 또는 `docs/features/review/`에 기능 디렉토리가 있으면 새 기능 구현을 시작하지 않는다.

### 5. source 변경은 허용 브랜치에서만 커밋한다

일반 source 변경은 다음 브랜치 prefix에서만 허용된다.

```text
feat/*
fix/*
refactor/*
```

main/master에서는 일반 source 변경 커밋이 막힌다.

예외는 다음 두 가지뿐이다.

- source scaffold baseline
- database baseline

두 예외 모두 `.flh/runtime/STATE.md`의 approval 기록이 필요하다.

### 6. Review patch는 별도 lightweight flow를 따른다

`docs/features/review/`에 기능이 있으면 사용자 수정 요청은 기본적으로 해당 기능을 대상으로 한다.

Review patch는 `.flh/docs/REVIEW_PATCH_PIPELINE.md`를 따르며, 기능 하나당 하나의 `fix/*` branch/worktree를 `done/` 이동 전까지 재사용한다.

Review patch의 기본 커밋 정책은 사용자 명시 커밋 방식이다. 수정과 검증은 수행할 수 있지만, 커밋은 사용자가 요청했을 때 수행한다.

### 7. DB baseline은 Prisma-only다

DB-backed project의 공식 자동 baseline은 Prisma 기준으로만 수행한다.

DB를 사용하지 않는 프로젝트는 `.flh/runtime/STATE.md`에 다음 approval을 남겨 1.6 DB baseline 단계를 통과한다.

```yaml
approvals:
  database_baseline:
    required: false
    skipped: true
```

DB-backed project는 실제 Prisma baseline 배포와 검증 후 다음 approval이 필요하다.

```yaml
approvals:
  database_baseline:
    required: true
    verified: true
```

### 8. 비밀값은 기록하지 않는다

API key, token, password, DB connection string은 `STATE.md`, 기능 문서, 매뉴얼, README에 기록하지 않는다.

필요한 값은 `.env`, 배포 플랫폼 secret, 또는 사용자가 지정한 안전한 위치에 둔다.

## Useful Commands

```sh
npm test
python3 -m unittest tests/hooks/test_user_prompt_submit.py tests/hooks/test_pre_commit.py
printf '아키텍처 설계하자' | .codex/hooks/user-prompt-submit.sh
git status
```

## Documents

- [HARNESS_MANUAL.md](HARNESS_MANUAL.md): 전체 하네스 매뉴얼
- [.flh/docs/PROJECT_WORKFLOW.md](.flh/docs/PROJECT_WORKFLOW.md): 프로젝트 workflow 설명
- [.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md](.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md): 기능 구현 파이프라인
- [.flh/docs/REVIEW_PATCH_PIPELINE.md](.flh/docs/REVIEW_PATCH_PIPELINE.md): review patch 파이프라인
- [AGENTS.md](AGENTS.md): Codex 실행 규칙
