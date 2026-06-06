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

### main/master

source file이 staged된 경우 commit을 차단한다.

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

---

## Affected Package Detection

affected package는 staged source file을 기준으로 찾는다.

탐지 순서:

1. `docs/source-layout.yml`의 `source_roots`를 읽는다.
2. staged file이 어떤 `source_roots.*.path` 내부에 있는지 확인한다.
3. 해당 source root의 `package: true` 여부를 확인한다.
4. 해당 source root를 affected package 후보로 등록한다.
5. 같은 package가 여러 staged file에서 반복 감지되면 한 번만 검사한다.

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

package manager는 다음 순서로 결정한다.

1. `docs/source-layout.yml`의 `project.package_manager`
2. affected package의 `package.json.packageManager`
3. root `package.json.packageManager`
4. lockfile 기반 추론
   - `pnpm-lock.yaml` -> `pnpm`
   - `yarn.lock` -> `yarn`
   - `package-lock.json` -> `npm`
5. 기본값 `npm`

package별로 package manager가 다를 가능성은 낮지만, package-local `packageManager`가 있으면 그 값을 우선한다.

---

## Script Execution Policy

각 affected package에서 `package.json.scripts`를 읽고 존재하는 script만 실행한다.

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
npm run test --prefix app/be

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

권장 설정:

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
4. docs/source-layout.yml 상태 확인
5. staged file 분류
6. source file이 없으면 source package checks와 lint-staged를 모두 스킵하고 commit 허용
7. main/master에서 source file이 있으면 차단
8. source file이 있으면 active/review 기능 디렉토리 확인
9. affected package 목록 생성
10. `package: true`인데 package.json이 없으면 차단
11. affected package별 package manager 탐지
12. package별 lint/typecheck/test script 실행
13. lint-staged 실행
14. 모든 검증 통과 시 commit 허용
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

if no source files:
    print docs/harness-only skip message
    exit(0)

if branch is main or master:
    print Korean block message
    exit(1)

if no docs/features/active/* and no docs/features/review/*:
    print Korean block message
    exit(1)

affected_packages = unique source roots from staged source files

for package in affected_packages:
    if package is marked package=true and package.json is missing:
        print Korean block message
        exit(1)

    pm = detect_package_manager(package)
    for script in ["lint", "typecheck", "test"]:
        if script exists:
            run script
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
