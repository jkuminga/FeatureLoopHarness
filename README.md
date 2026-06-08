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

1. 이 템플릿을 git repo 안에서 사용한다.
2. `npm install`을 실행해 Husky와 lint-staged를 설치하고 Git hook을 연결한다.
3. Codex를 project root에서 실행한다.
4. Codex에서 `/hooks`를 연다.
5. `UserPromptSubmit` hook을 review/trust 처리한다.
6. hook 파일이나 `.codex/hooks.json`을 수정했다면 다시 trust 처리한다.

검증:

```sh
python3 -m unittest tests/hooks/test_user_prompt_submit.py
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

2. Codex에서 `/hooks`를 열고 `UserPromptSubmit` hook이 trusted 상태인지 확인한다.
   hook 파일이나 `.codex/hooks.json`을 수정했다면 다시 trust 처리해야 할 수 있다.

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

### Baseline DB Deployment

`DATA_MODEL_DEFINITION` 단계는 실제 Prisma 파일을 만들지 않고, `docs/DB_SCHEMA.md`를 Prisma-ready 데이터 모델 명세로 확정하는 단계다.
`app/be/prisma/schema.prisma`, baseline migration, DB deploy/verify script 생성은 첫 기능 구현을 시작하기 전 `FEATURE_IMPLEMENTATION`의 `1.6. Baseline DB Deployment`에서 수행한다.
Prisma baseline은 기본적으로 backend package인 `app/be` 안에서 관리한다.
DB 배포 전에 source package scaffold baseline을 먼저 완료해 package/script 기반을 준비한다.

첫 기능을 `active/`로 옮기기 전에 다음을 확인한다.

```yaml
approvals:
  database_baseline:
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
- `docs/docs-map.md`: 문서/설정 파일 지도
