# PRE_COMMIT_PIPELINE_DESIGN.md

이 문서는 하네스 템플릿에서 사용할 source-code pre-commit pipeline 설계를 정의한다.

목표는 하네스/문서 커밋을 방해하지 않으면서, 실제 프로젝트 소스 변경에 대해서만 안전한 사전 검증을 수행하는 것이다.

---

## Goals

- `main`/`master` 브랜치에서 실제 source file 직접 커밋을 차단한다.
- 문서/하네스 파일만 변경된 커밋은 `main`/`master`에서도 허용한다.
- source file 변경 시 `docs/source-layout.yml`을 기준으로 affected package를 찾는다.
- affected package별로 존재하는 script만 실행한다.
- frontend/backend/package가 동시에 변경되면 각 package를 한 번씩만 검사한다.
- pre-commit 판단 로직은 shell이 아니라 Python script로 구현한다.
- `lint-staged`는 source 확장자인 `js`, `jsx`, `ts`, `tsx`만 대상으로 한다.
- 모든 출력 문구는 한국어 친화적이고, 성공/실패/스킵 상태가 눈에 잘 보이도록 작성한다.

---

## Non-goals

- framework scaffold를 자동 생성하지 않는다.
- 모든 프로젝트에 동일한 `app/fe`, `app/be` 구조를 강제하지 않는다.
- 모든 package에 `lint`, `typecheck`, `test` script가 있다고 가정하지 않는다.
- 문서/하네스 파일만 변경된 커밋에는 source package checks와 `lint-staged`를 실행하지 않는다.
- 문서/하네스 확장자인 `md`, `yml`, `yaml`은 package test나 `lint-staged` 대상에 포함하지 않는다.
- merge 정책을 pre-commit에서 처리하지 않는다.

---

## Implementation Refinement Checklist

pre-commit script를 실제 구현하기 전에 다음 항목을 하나씩 확정하고 이 문서에 반영한다.

- [x] 파일 분류 우선순위를 명확히 한다. source root 내부 파일은 root/harness 파일명과 같아도 source file로 우선 판정한다.
- [x] scaffold baseline exception에서 허용할 root package/workspace 설정 파일 범위를 명확히 한다.
- [x] `docs/source-layout.yml`이 `template` 또는 미완성 상태일 때 source commit과 docs/harness commit을 어떻게 처리할지 명확히 한다.
- [x] source file이 staged된 branch가 `feat/`, `fix/`, `refactor/`가 아닌 경우의 차단 규칙을 명확히 한다.
- [x] package manager별 script 실행 명령을 명확히 한다.
- [x] 실제 `.husky/pre-commit`과 root `package.json`의 `lint-staged` 설정 전환 방식을 명확히 한다.
- [x] nested source root가 있을 때 가장 긴 path prefix를 우선하는 affected package 탐지 규칙을 명확히 한다.
- [x] `.flh/runtime/STATE.md`는 frontmatter만 machine-readable state로 읽는다는 구현 규칙을 명확히 한다.

---

## Required Inputs

### Git

- 현재 branch
- staged file 목록

명령:

```sh
git branch --show-current
git diff --cached --name-only
```

### Python

pre-commit 판단 로직은 `python3`로 실행한다.
YAML은 `docs/source-layout.yml`의 제한된 구조만 읽으면 되므로, 외부 의존성 없이 하네스 내부 parser를 사용한다.

`.flh/runtime/STATE.md`는 파일 상단 YAML frontmatter만 machine-readable runtime state로 읽는다.
Markdown body는 사람과 에이전트를 위한 설명이며, pre-commit 판단에 사용하지 않는다.

frontmatter 파싱 규칙:

```text
1. 파일 시작의 첫 번째 --- 를 확인한다.
2. 첫 번째 --- 와 두 번째 --- 사이만 추출한다.
3. 추출한 frontmatter에서 current_state, completed_states, approvals를 읽는다.
4. Markdown body의 예시 YAML, 설명 문구, 문자열은 상태 판단에 사용하지 않는다.
```

금지:

```text
STATE.md 전체 문자열에서 "source_scaffold" 검색
STATE.md 전체 문자열에서 "created: true" 검색
Markdown body의 approval 예시를 실제 approval로 판단
```

### Source Layout

파일:

```text
docs/source-layout.yml
```

필수 조건:

- `status: completed`
- `project.workspace`
- `source_roots.*.path`
- `source_roots.*.package`
- `source_roots.*.framework`
- `source_roots.*.runtime`
- `source_roots.*.language`
- `source_roots.*.module`
- `source_roots.*.testing`
- `source_roots.*.tooling`

`docs/source-layout.yml`의 completed 검증은 source file이 staged된 경우에만 강제한다.
문서/하네스 파일만 staged된 commit에서는 `docs/source-layout.yml`이 `template` 또는 미완성 상태여도 commit을 허용하고, source package checks와 `lint-staged`를 모두 스킵한다.

source file 후보가 staged된 경우에는 `docs/source-layout.yml`의 `status`가 `completed`여야 한다.
`status`가 `completed`가 아니면 source file의 package, package manager, test script를 안정적으로 판단할 수 없으므로 commit을 차단한다.

예시:

```yaml
version: 1
status: completed

project:
  type: web-app
  package_manager: npm
  workspace: true
  runtime: node

source_roots:
  frontend:
    path: app/fe
    role: frontend
    package: true
    stack: react-vite
    framework: vite
    runtime: react
    language: typescript
    module: esm
    testing:
      unit: vitest
      integration: none
      e2e: playwright
      component: testing-library
    tooling:
      lint: eslint
      format: prettier
    scaffold: gitkeep-only
    description: Frontend package.
  backend:
    path: app/be
    role: backend
    package: true
    stack: node-api-prisma
    framework: express
    runtime: node
    language: typescript
    module: esm
    testing:
      unit: vitest
      integration: vitest
      e2e: none
      component: none
    tooling:
      lint: eslint
      format: prettier
    scaffold: gitkeep-only
    description: Backend package.
```

---

## File Classification

pre-commit은 staged file을 먼저 분류한다.

### Source Files

다음 중 하나에 해당하면 source file로 본다.

- `docs/source-layout.yml`의 `source_roots.*.path` 내부 파일
- source layout이 아직 completed가 아닌 상태에서 `app/`, `apps/`, `packages/` 내부에 있는 파일

파일 분류는 파일명보다 경로를 우선한다.
source root 내부에 있는 `package.json`, lockfile, workspace/config 파일은 root/harness 파일명과 같아도 source file로 본다.
예를 들어 `app/be/package.json`은 source file이고, root `package.json`만 documentation/harness file로 본다.

`source_roots`에는 실제 source/package 단위를 기록한다.
`app/` 같은 넓은 부모 디렉토리는 특별한 이유가 없으면 기록하지 않는다.

단, nested source root가 정의된 경우에는 가장 긴 path prefix를 가진 source root를 우선한다.
예를 들어 `app`과 `app/be`가 모두 source root이고 staged file이 `app/be/src/user.ts`라면 `app/be`를 선택한다.

### Documentation and Harness Files

다음 파일은 문서/하네스 파일로 본다.

- `docs/**`
- `.flh/**`
- `.codex/**`
- `AGENTS.md`
- `README.md`
- `tests/hooks/**`
- `.husky/**`
- `package.json`
- `package-lock.json`

단, `docs/source-layout.yml`은 하네스 문서이면서 source file 판정 기준이므로 별도로 읽는다.

### Unknown Files

source file도 아니고 문서/하네스 파일도 아니면 unknown file로 본다.
unknown file이 staged된 경우 pre-commit은 경고를 출력하되, source file이 함께 없으면 차단하지 않는다.

---

## Branch Policy

### Scaffold Baseline Context

source package scaffold baseline은 첫 기능 구현 전에 프로젝트 공통 package 기반을 준비하는 1회성 작업이다.

pre-commit은 scaffold를 생성하지 않는다.
pre-commit은 main/master에서 발생하는 scaffold baseline commit이 허용 범위 안에 있는지만 검증한다.
pre-commit은 database baseline도 생성하지 않는다.
pre-commit은 main/master에서 발생하는 database baseline commit이 허용 범위 안에 있는지만 검증한다.

첫 기능 구현 전 준비 순서는 다음과 같다.

```text
FEATURE_IMPLEMENTATION request
-> Source Package Scaffold Baseline
-> Baseline DB Deployment
-> Branch and Worktree
-> Feature Implementation Loop
```

scaffold baseline은 `.flh/runtime/STATE.md`의 `approvals.source_scaffold.created: true`를 기준으로 idempotent하게 처리한다.
이미 해당 approval이 있으면 scaffold baseline 예외는 다시 열리지 않는다.

scaffold baseline은 DB 배포를 위한 package/script 기반을 준비할 수 있지만, 실제 DB provider 확인, env/secret 요청, migration 적용, DB 연결 검증은 `Baseline DB Deployment` 단계에서 처리한다.

### Database Baseline Exception

main/master에서 Prisma baseline source file이 staged되어 있어도 다음 조건을 모두 만족하면 commit을 허용한다.

- `.flh/runtime/STATE.md`의 `current_state`가 `FEATURE_IMPLEMENTATION`이다.
- 현재 `.flh/runtime/STATE.md`에 `approvals.source_scaffold.created: true`가 기록되어 있다.
- 이전 커밋의 `.flh/runtime/STATE.md`에 `approvals.database_baseline.verified: true`가 아직 없다.
- 현재 staged/working `.flh/runtime/STATE.md`에는 `approvals.database_baseline.verified: true`가 기록되어 있다.
- `.flh/runtime/STATE.md`가 staged되어 있다.
- staged source files는 Prisma baseline 허용 범위에만 속한다.
- staged root files는 기본 scaffold root category 또는 `docs/source-layout.yml`의 `project.scaffold_extra_root_files`에 명시된 파일에 한정한다.
- 기능 화면, API route, 도메인 로직, 기능 테스트가 포함되지 않는다.

Prisma baseline source 허용 범위:

```text
prisma/schema.prisma
prisma/migrations/**
package.json
```

database baseline commit에는 `schema.prisma`, baseline migration, 필요한 DB script/dependency 변경, `.flh/runtime/STATE.md`의 `approvals.database_baseline.verified: true` 기록이 함께 포함되어야 한다.
이후 main/master database baseline source commit 예외는 다시 열리지 않는다.

### main/master

source file이 staged된 경우 commit을 차단한다.

단, 최초 source package scaffold baseline commit과 최초 database baseline commit은 각각 1회 예외로 허용한다.

문서/하네스 파일만 staged된 경우 commit을 허용한다.

출력 예시:

```text
🚫 커밋 차단

현재 브랜치: main
main/master 브랜치에서는 실제 소스 파일을 직접 커밋할 수 없습니다.

감지된 소스 파일:
- app/fe/src/App.tsx
- app/be/src/user.service.ts

해결 방법:
feat/*, fix/*, refactor/* 브랜치에서 작업한 뒤 머지하세요.
```

### Scaffold Baseline Exception

main/master에서 source file이 staged되어 있어도 다음 조건을 모두 만족하면 commit을 허용한다.

- `.flh/runtime/STATE.md`의 `current_state`가 `FEATURE_IMPLEMENTATION`이다.
- 이전 커밋의 `.flh/runtime/STATE.md`에 `approvals.source_scaffold.created: true`가 아직 없다.
- 현재 staged/working `.flh/runtime/STATE.md`에는 `approvals.source_scaffold.created: true`가 기록되어 있다.
- `.flh/runtime/STATE.md`가 staged되어 있다.
- staged source files가 `docs/source-layout.yml`의 `source_roots.*.path` 내부에만 있다.
- staged source files가 scaffold baseline 허용 범위에만 속한다.
- staged root files는 기본 scaffold root category 또는 `docs/source-layout.yml`의 `project.scaffold_extra_root_files`에 명시된 파일에 한정한다.
- staged harness runtime file은 `.flh/runtime/STATE.md`의 `approvals.source_scaffold` 기록에 한정한다.
- 기능 화면, API route, 도메인 로직, 기능 테스트가 포함되지 않는다.

기본 scaffold root category:

```text
package/workspace:
package.json
package-lock.json
pnpm-lock.yaml
pnpm-workspace.yaml
yarn.lock

shared tooling:
tsconfig.base.json
eslint.config.*
prettier.config.*
.prettierrc*
.prettierignore

repo hygiene:
.gitignore
```

기본 category에 없는 root file이 scaffold baseline에 필요하면 `docs/source-layout.yml`에 명시한다.

```yaml
project:
  scaffold_extra_root_files:
    - turbo.json
    - playwright.config.ts
```

source root 내부 예외 허용 파일 예시:

```text
package.json
package-lock.json
tsconfig*.json
vite.config.*
vitest.config.*
eslint.config.*
src/index.*
src/main.*
src/app.*
.gitkeep
```

차단 후보 예시:

```text
src/features/**
src/routes/**
src/pages/**
src/components/**
*.test.*
*.spec.*
tests/**
```

scaffold baseline commit에는 `.flh/runtime/STATE.md`의 `approvals.source_scaffold.created: true` 기록이 함께 포함되어야 한다.
이후 main/master source commit 예외는 다시 열리지 않는다.

### Feature Branch

브랜치명이 다음 prefix 중 하나로 시작하면 source commit을 허용한다.

- `feat/`
- `fix/`
- `refactor/`

source file이 staged된 경우 active 또는 review 기능 디렉토리가 있는지 확인한다.

허용되는 기능 디렉토리:

- `docs/features/active/FEAT-XXX-name/`
- `docs/features/review/FEAT-XXX-name/`

둘 다 없으면 commit을 차단한다.

### Other Branches

source file이 staged된 상태에서 현재 branch가 `main`, `master`, `feat/*`, `fix/*`, `refactor/*` 중 어디에도 해당하지 않으면 commit을 차단한다.

문서/하네스 파일만 staged된 경우에는 branch prefix를 검사하지 않고 commit을 허용한다.

출력 예시:

```text
🚫 커밋 차단

현재 브랜치: chore/setup

source file 변경은 다음 브랜치에서만 커밋할 수 있습니다.

허용 브랜치:
- feat/*
- fix/*
- refactor/*

문서/하네스 파일만 변경한 커밋은 브랜치 prefix와 관계없이 허용됩니다.
```

---

## Affected Package Detection

affected package는 staged source file을 기준으로 찾는다.

탐지 순서:

1. `docs/source-layout.yml`의 `source_roots`를 읽는다.
2. staged file이 어떤 `source_roots.*.path` 내부에 있는지 확인한다.
3. 하나의 staged file이 여러 source root에 동시에 속하면 가장 긴 path prefix를 가진 source root를 선택한다.
4. 선택한 source root의 `package: true` 여부를 확인한다.
5. `package: true`이면 affected package 후보로 등록한다.
6. `package: false`이면 source file로는 유지하되 package check 대상에는 포함하지 않는다.
7. 같은 package가 여러 staged file에서 반복 감지되면 한 번만 검사한다.

예시:

```yaml
source_roots:
  app_root:
    path: app
    package: false
  backend:
    path: app/be
    package: true
```

```text
staged file:
- app/be/src/user.ts

matching source roots:
- app
- app/be

selected source root:
- app/be
```

`package: true`인 source root에 `package.json`이 없으면 commit을 차단한다.
이는 검사를 스킵하면 실제 source 변경이 검증 없이 커밋될 수 있기 때문이다.

예시:

```text
staged files:
- app/fe/src/App.tsx
- app/fe/src/Button.tsx
- app/be/src/user.service.ts

affected packages:
- app/fe
- app/be
```

`app/fe`와 `app/be`는 각각 한 번씩만 검사한다.

---

## Package Manager Detection

package manager는 `docs/source-layout.yml`의 `project.package_manager`를 기준으로 결정한다.

지원 package manager:

- `npm`
- `pnpm`
- `yarn`
- `bun`

`package.json.packageManager`는 실행 기준이 아니라 불일치 검증용으로만 사용한다.
affected package 또는 root `package.json`에 `packageManager` 필드가 있고, 그 값이 `docs/source-layout.yml`의 `project.package_manager`와 다르면 commit을 차단한다.
`packageManager` 값에 version이 포함된 경우에는 package manager 이름만 비교한다.
예를 들어 `pnpm@9.0.0`은 `pnpm`, `npm@10.0.0`은 `npm`으로 정규화한 뒤 비교한다.

`package.json.packageManager` 필드가 없으면 문제로 보지 않는다.
lockfile은 package manager 추론 기준으로 사용하지 않는다.
하네스에서 사용할 package manager는 아키텍처 단계에서 `docs/source-layout.yml`에 명시되어야 한다.

출력 예시:

```text
🚫 커밋 차단

package manager 설정이 서로 다릅니다.

docs/source-layout.yml: npm
app/be/package.json: pnpm@9.0.0

해결 방법:
docs/source-layout.yml의 project.package_manager 또는 package.json의 packageManager 값을 일치시키세요.
```

package manager 실행 파일을 찾을 수 없으면 검증을 스킵하지 않고 commit을 차단한다.

---

## Script Execution Policy

각 affected package에서 `package.json.scripts`를 읽고 존재하는 script만 실행한다.

package script는 `docs/source-layout.yml`에서 결정한 package manager로 실행한다.

실행 명령:

```text
npm:
  npm --prefix <package_path> run <script>

pnpm:
  pnpm -C <package_path> run <script>

yarn:
  yarn --cwd <package_path> run <script>

bun:
  bun --cwd <package_path> run <script>
```

실행 순서:

```text
1. lint
2. typecheck
3. test
```

없는 script는 실패로 보지 않고 스킵한다.

출력 예시:

```text
🔎 app/fe 검사 시작

✅ lint 통과
✅ typecheck 통과
⏭️ test script 없음 - 스킵
```

하나라도 실패하면 commit을 차단한다.

출력 예시:

```text
🚫 커밋 차단

app/be 패키지의 test script가 실패했습니다.

실행 명령:
npm --prefix app/be run test

오류를 수정한 뒤 다시 커밋하세요.
```

---

## Missing Package Policy

source root가 `package: true`인데 해당 경로에 `package.json`이 없으면 commit을 차단한다.

차단 조건:

- source file이 staged되어 있다.
- staged file이 `source_roots.*.path` 내부에 있다.
- 해당 source root의 `package` 값이 `true`다.
- 해당 source root에 `package.json`이 없다.

출력 예시:

```text
🚫 커밋 차단

app/fe는 package로 표시되어 있지만 package.json이 없습니다.

확인할 파일:
docs/source-layout.yml

해결 방법:
app/fe/package.json을 생성하거나, package가 아닌 디렉토리라면 source-layout.yml에서 package 값을 false로 변경하세요.
```

---

## lint-staged Policy

source file이 staged된 경우에만 affected package 검사가 끝난 뒤 `lint-staged`를 실행한다.
`lint-staged` 설정은 루트 `package.json`에서 관리하고, source 확장자만 대상으로 한다.

`.husky/pre-commit`은 `lint-staged`를 직접 실행하지 않는다.
pre-commit hook은 항상 `.flh/scripts/pre_commit.py`만 실행하고, Python script가 source file 감지 여부에 따라 `lint-staged` 실행 여부를 결정한다.

최종 `.husky/pre-commit` 구조:

```sh
#!/usr/bin/env sh

python3 .flh/scripts/pre_commit.py
```

root `package.json`의 `lint-staged` 설정은 하네스/문서 테스트가 아니라 source 확장자만 대상으로 한다.

최종 `lint-staged` 설정:

```json
{
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

하네스/문서 변경에 대한 hook test 실행은 `lint-staged` 책임이 아니다.
하네스 테스트는 필요 시 직접 실행하거나 CI에서 실행한다.

`lint-staged`는 `docs/source-layout.yml`에서 결정한 package manager 기준으로 실행한다.

실행 명령:

```text
npm:
  npx lint-staged

pnpm:
  pnpm exec lint-staged

yarn:
  yarn lint-staged

bun:
  bunx lint-staged
```

권장 위치:

```text
docs/harness-only commit
-> source package checks 스킵
-> lint-staged 스킵
-> commit

source package checks
-> lint-staged
-> commit
```

이유:

- package-level `lint/typecheck/test`는 실제 source package의 안정성을 본다.
- `lint-staged`는 staged source file 중심의 format/lint를 처리한다.
- 문서/하네스 파일만 staged된 경우에는 source 검증 대상이 아니므로 `lint-staged`도 실행하지 않고 commit을 허용한다.
- `md`, `yml`, `yaml`은 설계/하네스 문서 확장자이므로 lint-staged 대상에서 제외한다.

---

## Output Rules

모든 pre-commit 출력은 한국어 친화적으로 작성한다.

출력 문구는 다음 정보를 명확히 포함해야 한다.

- 현재 branch
- staged file 분류 결과
- source file 감지 여부
- affected package 목록
- 실행한 script
- 스킵한 script와 이유
- 실패한 명령
- 사용자가 다음에 해야 할 일

출력 상태는 다음 prefix를 사용한다.

```text
✅ 성공
🚫 차단
⚠️ 경고
🔎 검사
⏭️ 스킵
```

---

## Pre-commit Flow

```text
1. 현재 branch 확인
2. staged file 목록 확인
3. staged file이 없으면 종료
4. staged file을 docs/harness, source candidate, unknown으로 1차 분류
5. source candidate가 없으면 source-layout completed 검증 없이 source package checks와 lint-staged를 모두 스킵하고 commit 허용
6. source candidate가 있으면 docs/source-layout.yml의 status가 completed인지 확인
7. source-layout이 completed가 아니면 source commit 차단
8. completed source-layout 기준으로 staged file을 source file로 확정 분류
9. main/master에서 source file이 있으면 scaffold baseline exception 여부 확인
10. scaffold baseline exception이면 허용 파일 범위만 확인하고 commit 허용
11. scaffold baseline exception이 아니면 database baseline exception 여부 확인
12. database baseline exception이면 허용 파일 범위만 확인하고 commit 허용
13. baseline exception이 모두 아니면 main/master source commit 차단
14. branch가 feat/fix/refactor prefix가 아니면 source commit 차단
15. feature/fix/refactor branch에서 source file이 있으면 active/review 기능 디렉토리 확인
16. affected package 목록 생성
17. `package: true`인데 package.json이 없으면 차단
18. docs/source-layout.yml의 project.package_manager 확인
19. package.json.packageManager가 있으면 source-layout.yml과 일치하는지 검증
20. package manager 실행 파일이 없으면 차단
21. package별 lint/typecheck/test script 실행
22. lint-staged 실행
23. 모든 검증 통과 시 commit 허용
```

---

## Pseudocode

```python
branch = git("branch --show-current")
staged_files = git("diff --cached --name-only")

if not staged_files:
    exit(0)

load docs/source-layout.yml
classify staged files

if no source candidates:
    print docs/harness-only skip message
    exit(0)

if source_layout.status != "completed":
    print Korean block message
    exit(1)

classify source files from completed source_layout

if branch is main or master:
    current_state = load STATE.md frontmatter from working tree
    committed_state = load STATE.md frontmatter from HEAD
    if is_scaffold_baseline_exception(
        staged_files,
        current_state,
        committed_state,
        source_layout,
    ):
        print scaffold baseline exception message
        exit(0)
    if is_database_baseline_exception(
        staged_files,
        current_state,
        committed_state,
        source_layout,
    ):
        print database baseline exception message
        exit(0)
    print Korean block message
    exit(1)

if branch does not start with ("feat/", "fix/", "refactor/"):
    print Korean block message
    exit(1)

if no docs/features/active/* and no docs/features/review/*:
    print Korean block message
    exit(1)

affected_packages = unique source roots from staged source files

pm = source_layout.project.package_manager
if pm not in supported_package_managers:
    print Korean block message
    exit(1)

if package_manager_binary_is_missing(pm):
    print Korean block message
    exit(1)

for package in affected_packages:
    if package is marked package=true and package.json is missing:
        print Korean block message
        exit(1)

    if package_json_package_manager_conflicts(package, pm):
        print Korean block message
        exit(1)

    for script in ["lint", "typecheck", "test"]:
        if script exists:
            run script with source_layout package manager
        else:
            print skip message

run lint-staged
```

---

## Recommended File Structure

초기 구현은 단순하게 유지한다.

```text
.husky/pre-commit
.flh/scripts/pre_commit.py
```

`.husky/pre-commit`은 얇게 유지한다.

```sh
#!/usr/bin/env sh

python3 .flh/scripts/pre_commit.py
```

실제 로직은 `.flh/scripts/pre_commit.py`에 둔다.
이 스크립트는 하네스 전용 로직이므로 일반 application source와 분리한다.
