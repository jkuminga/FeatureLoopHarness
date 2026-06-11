# Harness Template

![image](https://res.cloudinary.com/dddvvp9de/image/upload/v1780124834/FeatureLoopHarness_zndch9.png)

Codex `UserPromptSubmit` hook과 `AGENTS.md` 규칙으로 실제 프로젝트의 진행 흐름을 제한하는 하네스 템플릿이다.

이 레포는 특정 제품/서비스를 구현하는 레포가 아니라, 실제 프로젝트를 진행할 때 사용할 워크플로우/문서/훅 구조를 제공한다.

## Core Flow

프로젝트 전체 워크플로우:

```text
MVP_DEFINITION
-> ARCHITECTURE_DESIGN
-> FEATURE_INDEX_DEFINITION
-> DATA_MODEL_DEFINITION
-> API_DESIGN
-> FRONTEND_DESIGN
-> FEATURE_IMPLEMENTATION
```

프로젝트 상태는 `.flh/runtime/STATE.md`에 저장된다.

상태 전이와 guard는 다음 파일이 제어한다.

- `.flh/workflow/flow.yml`
- `.flh/workflow/state-actions.yml`
- `.flh/workflow/docs-spec.yml`
- `.flh/workflow/transition-guards.yml`
- `.flh/workflow/request-patterns.yml`

## Hook Setup

이 템플릿은 project-local Codex hook을 사용한다.

필수 파일:

```text
.codex/config.toml
.codex/hooks.json
.codex/hooks/user-prompt-submit.sh
.flh/runtime/STATE.md
.flh/workflow/*.yml
.flh/hooks/user_prompt_submit.py
docs/source-layout.yml
.flh/docs/*.md
```

`.codex/config.toml`:

```toml
[features]
hooks = true
```

`.codex/hooks.json`은 상대경로 wrapper를 호출한다.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".codex/hooks/user-prompt-submit.sh",
            "statusMessage": "Checking harness workflow state",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

템플릿 배포를 위해 절대경로를 사용하지 않는다.

## First-Time Use

이 단계는 실제 애플리케이션 의존성을 설치하는 과정이 아니라, flh가 Git, Codex hook, Husky pre-commit hook을 통해 정상 동작하기 위한 최초 설정 과정이다.

### Requirements

- `git`
- `node`
- `npm`
- `python3`
- `PyYAML`
- `Codex CLI`

확인:

```sh
git --version
node --version
npm --version
python3 --version
python3 -c "import yaml; print('PyYAML OK')"
codex --version
```

### Clone and Connect Your Repository

flh는 Git branch, staged file, pre-commit hook을 기준으로 동작하므로 반드시 Git repo 안에서 사용한다.

```sh
git clone https://github.com/jkuminga/FeatureLoopHarness <PROJECT_DIR>
cd <PROJECT_DIR>
```

클론 직후에는 `origin`이 flh 템플릿 저장소를 바라볼 수 있다.
새 프로젝트로 사용하려면 기존 remote를 제거하고 본인 프로젝트 repo를 연결한다.

```sh
git remote -v
git remote remove origin
git remote add origin <YOUR_PROJECT_REPO_URL>
git remote -v
```

초기 상태를 본인 repo로 push한다.

```sh
git push -u origin main
```

현재 기본 브랜치가 `master`라면 아래 명령을 사용한다.

```sh
git push -u origin master
```

### Install Dependencies

Husky pre-commit hook과 lint-staged를 사용하기 위해 npm 의존성을 설치한다.

```sh
npm install
```

### Enable Codex Hook

flh는 사용자 의도 검사와 프로젝트 상태 전이를 위해 Codex `UserPromptSubmit` hook을 사용한다.

이 hook은 최초 사용 시 사용자가 실행을 승인해야 한다. 여기서 승인한다는 것은 hook 설정과 스크립트 경로를 확인한 뒤, Codex가 해당 hook을 실행해도 된다고 허용하는 것을 의미한다.

현재 project-local hook의 실행 승인 작업은 Codex CLI의 `/hooks` 흐름을 기준으로 진행한다. Codex Desktop App을 주로 사용하더라도, hook 활성화를 위해서는 최초 설정 단계에서 Codex CLI를 사용하는 것을 권장한다.

프로젝트 루트에서 Codex CLI를 실행한다.

```sh
codex
```

flh를 clone한 뒤 Codex CLI를 최초로 실행하면, CLI가 project-local hook을 감지하고 사용자에게 실행 승인 여부를 물어볼 수 있다.
만약 이 안내가 자동으로 표시되지 않거나 나중에 다시 확인해야 한다면, Codex CLI 안에서 다음 명령을 실행한다.

```text
/hooks
```

`UserPromptSubmit` hook이 표시되면 내용을 확인하고, Codex가 해당 hook을 실행해도 된다고 승인한다.
hook 파일이나 `.codex/hooks.json`을 수정한 경우에는 hook hash가 바뀔 수 있으므로 다시 `/hooks`에서 승인해야 할 수 있다.

hook 승인 이후에는 Codex CLI와 Codex Desktop App 모두에서 하네스 구조와 파이프라인을 사용할 수 있다.

### Check Script Permissions

hook script 실행 권한이 누락되면 hook이 실행되지 않을 수 있다.

확인:

```sh
ls -l .codex/hooks/user-prompt-submit.sh
ls -l .flh/hooks/user-prompt-submit.sh
ls -l .flh/scripts/pre_commit.py
```

실행 권한이 없다면 아래 명령을 실행한다.

```sh
chmod +x .codex/hooks/user-prompt-submit.sh
chmod +x .flh/hooks/user-prompt-submit.sh
chmod +x .flh/scripts/pre_commit.py
```

검증:

```sh
npm test
printf '아키텍처 설계하자' | .codex/hooks/user-prompt-submit.sh
codex exec '아키텍처 설계하자'
```

정상적으로 설정됐다면 마지막 명령에서 다음이 보여야 한다.

```text
hook: UserPromptSubmit
hook: UserPromptSubmit Blocked
```

## Troubleshooting

hook이 실행되지 않거나 block되지 않으면 다음 순서로 확인한다.

1. 프로젝트가 git repo 안에서 열렸는지 확인한다.
   ```sh
   git rev-parse --show-toplevel
   ```

2. Codex CLI에서 `/hooks`를 열고 `UserPromptSubmit` hook이 승인된 상태인지 확인한다.
   hook 파일이나 `.codex/hooks.json`을 수정했다면 다시 승인해야 할 수 있다.

3. wrapper가 직접 실행되는지 확인한다.
   ```sh
   printf '아키텍처 설계하자' | .codex/hooks/user-prompt-submit.sh
   ```

4. `.codex/hooks.json`의 command가 상대경로인지 확인한다.
   ```json
   "command": ".codex/hooks/user-prompt-submit.sh"
   ```

5. wrapper 실행 권한을 확인한다.
   ```sh
   ls -l .codex/hooks/user-prompt-submit.sh
   chmod +x .codex/hooks/user-prompt-submit.sh
   ```

6. hook unit test를 실행한다.
   ```sh
   npm test
   ```

## What The Hook Controls

`.flh/hooks/user_prompt_submit.py`는 요청 시작 전에 프로젝트 전체 workflow를 gate한다.

담당:

- `STATE.md` 읽기
- 사용자 요청을 `request_type`으로 분류
- 현재 state에서 허용되는 요청인지 확인
- 필요한 경우 transition guard 검사
- 전이가 가능하면 `STATE.md` 갱신
- 전이가 불가능하면 요청 block
- `UNKNOWN` 또는 낮은 confidence 요청에는 추가 context 주입

request type 분류 패턴은 `.flh/workflow/request-patterns.yml`에서 관리한다.
자연어 alias를 추가할 때는 Python hook script가 아니라 이 설정 파일을 수정한다.

`QUESTION_OR_CONFIRMATION_REQUEST`는 `flow.yml`의 상태 전이 request type이 아니라 hook 내부에서만 사용하는 예외 타입이다.
질문/확인형 요청은 파일 변경 없는 답변으로 처리하고, 질문/확인형 표현과 실행 의도가 함께 있으면 낮은 confidence로 분류해 사용자 확인을 요구한다.

명시 prefix:

- `/q`: 질문 모드. 답변만 허용하고 파일 변경, `STATE.md` 변경, 커밋/푸쉬/머지, 파이프라인 실행을 금지한다.
- `/d`: 문서 및 하네스 제어 모드. 프로젝트 문서 작업을 기본 허용하고, 사용자가 하네스 유지보수나 workflow 상태 제어를 명시한 경우에만 `.flh/`, `.codex/`, hook test, package 설정, `STATE.md` 같은 하네스 파일 수정을 허용한다. 사용자가 명시적으로 요청했고 변경 파일이 허용 범위 안에 있을 때만 커밋/푸쉬를 허용한다. 머지는 허용하지 않는다.

Manual step skip:

- 사용자는 `/d`를 사용해 프로젝트 workflow 단계를 명시적으로 skip 처리할 수 있다.
- 하네스는 skip이 도메인상 올바른지 자동 판정하지 않는다. skip은 사용자가 책임지는 수동 운영 결정이다.
- `MVP_DEFINITION`, `ARCHITECTURE_DESIGN`, `FEATURE_INDEX_DEFINITION`은 이후 workflow의 기반이므로 skip하지 않는다.
- skip된 단계의 산출물은 completed artifact로 가정하지 않는다.

담당하지 않는 것:

- 기능 구현 세부 절차
- 테스트 작성 규칙
- 커밋/푸쉬/머지 세부 절차
- 기능별 품질 판단

## What AGENTS.md Controls

`AGENTS.md`는 hook을 통과한 뒤 Codex가 실제 작업할 때 지켜야 하는 행동 규칙이다.

핵심:

- 항상 `.flh/runtime/STATE.md`를 먼저 읽는다.
- 프로젝트 workflow 작업은 현재 상태에 해당하는 `.flh/workflow/state-actions.yml` 항목만 읽는다.
- 현재 상태의 `actions`, `allowed_extra_writes`, `ask_user_when`을 따른다.
- `FEATURE_IMPLEMENTATION`이 아니면 기능 구현 파이프라인을 실행하지 않는다.
- `/d` 문서 모드에서는 `docs/`, `.flh/`, `AGENTS.md`, `README.md`, `.codex/`, `tests/hooks/`, `.husky/`, `package.json`, `package-lock.json` 같은 문서/하네스 유지보수 파일만 수정한다.
- `FEATURE_IMPLEMENTATION`일 때만 `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`를 따른다.

## Feature Implementation

기능 구현 상태 디렉토리:

```text
docs/features/
  feature-index.md
  backlog/
  ready/
  active/
  blocked/
  review/
  done/
  postponed/
```

기능 구현 흐름:

```text
backlog
-> ready
-> active
-> review
-> done
```

`active/` 또는 `review/`에 기능이 있으면 새 기능 구현을 시작하지 않는다.

`review/`에는 동시에 하나의 기능만 둔다.

`review/`에 있는 기능은 full implementation pipeline을 다시 실행하지 않고 lightweight review patch flow로만 수정한다.

`done/` 이동은 사용자가 명시적으로 완료를 승인했을 때만 수행한다.

### Review Patch Flow

Review patch는 `docs/features/review/`에 있는 기능을 대상으로 하는 lightweight 수정 흐름이다.
세부 절차는 `.flh/docs/REVIEW_PATCH_PIPELINE.md`를 따른다.

source 변경이 포함된 review patch는 main/master에서 직접 커밋하지 않는다.
리뷰 대상 기능마다 하나의 `fix/*` branch/worktree를 만들고, 사용자가 해당 기능의 완료를 명시적으로 승인할 때까지 같은 branch/worktree를 재사용한다.

예시:

```text
feature: docs/features/review/FEAT-001-login
branch: fix/FEAT-001-login-review
worktree: FEAT-001-login-review
```

UI/UX 변경은 Playwright 기반으로 검증하고, 검증 자료나 blocker는 해당 기능의 `artifacts/review-patches/` 아래에 기록한다.

### Baseline DB Deployment

`DATA_MODEL_DEFINITION` 단계는 실제 Prisma 파일을 만들지 않고, `docs/DB_SCHEMA.md`를 Prisma-ready 데이터 모델 명세로 확정하는 단계다.
첫 기능 구현을 시작하기 전 `FEATURE_IMPLEMENTATION`의 `1.6. Baseline DB Deployment`는 먼저 `docs/source-layout.yml`의 `project.persistence.database_required` 값을 확인한다.
`database_required: false`인 프로젝트는 DB 배포를 실행하지 않고 skip approval만 기록한다.
`database_required: true`인 프로젝트는 `app/be/prisma/schema.prisma`, baseline migration, DB deploy/verify script를 생성하고 실제 DB에 반영한다.
DB-backed 프로젝트의 공식 자동 baseline은 Prisma 기준으로만 수행하며, Prisma baseline은 기본적으로 backend package인 `app/be` 안에서 관리한다.
DB 배포 전에 source package scaffold baseline을 먼저 완료해 package/script 기반을 준비한다.

첫 기능을 `active/`로 옮기기 전에 다음을 확인한다.

DB 미사용 프로젝트:

```yaml
approvals:
  database_baseline:
    required: false
    skipped: true
```

Prisma DB-backed 프로젝트:

```yaml
approvals:
  database_baseline:
    required: true
    deployed: true
    verified: true
```

이 기록이 없으면 사용자에게 DB provider 또는 Prisma-compatible database, environment, 필요한 secret/env 설정을 요청한다.
비밀값은 문서나 `STATE.md`에 기록하지 않는다.

권장 명령 이름:

```sh
npm run db:deploy
npm run db:verify
```

`db:verify`가 실패하면 첫 기능 구현을 시작하지 않는다.

## Design Guide

`FRONTEND_DESIGN` 단계의 산출물은 `docs/DESIGN.md`다.

사용자는 둘 중 하나를 선택한다.

1. 외부에서 사용 중인 `DESIGN.md`를 가져온다.
2. 하네스 흐름 안에서 `DESIGN.md`를 직접 작성한다.

외부 `DESIGN.md`는 frontmatter가 없을 수 있으므로, 이 경우 `.flh/runtime/STATE.md`에 approval을 기록한다.

```yaml
approvals:
  design:
    source: external
    path: docs/DESIGN.md
    approved: true
```

## Quality Score

`docs/QUALITY_SCORE.md`는 전역 점수 인덱스다.

기능별 상세 점수는 각 기능 디렉토리에 둔다.

```text
docs/features/active/FEAT-XXX-name/QUALITY_SCORE.md
```

작성 시점:

```text
구현
-> Unit/Integration/E2E
-> 기능별 QUALITY_SCORE.md 작성
-> docs/QUALITY_SCORE.md 요약 반영
-> 70점 미만이면 수정/재검증
-> 70점 이상이면 커밋 가능
```

치명 조건이 있으면 점수와 관계없이 커밋하지 않는다.

## Main Documents

- `AGENTS.md`: Codex 작업 규칙
- `.flh/docs/PROJECT_WORKFLOW.md`: 프로젝트 전체 workflow 설명
- `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`: 기능 단위 구현 파이프라인
- `.flh/docs/REVIEW_PATCH_PIPELINE.md`: review 상태 기능의 lightweight 수정 파이프라인
- `docs/docs-map.md`: 문서/설정 파일 지도
