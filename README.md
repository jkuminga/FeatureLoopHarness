# Harness Template

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

프로젝트 상태는 `codex/runtime/STATE.md`에 저장된다.

상태 전이와 guard는 다음 파일이 제어한다.

- `codex/workflow/flow.yml`
- `codex/workflow/docs-spec.yml`
- `codex/workflow/transition-guards.yml`
- `codex/workflow/request-patterns.yml`

## Hook Setup

이 템플릿은 project-local Codex hook을 사용한다.

필수 파일:

```text
.codex/config.toml
.codex/hooks.json
.codex/hooks/user-prompt-submit.sh
hooks/user_prompt_submit.py
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
2. Codex를 project root에서 실행한다.
3. Codex에서 `/hooks`를 연다.
4. `UserPromptSubmit` hook을 review/trust 처리한다.
5. hook 파일이나 `.codex/hooks.json`을 수정했다면 다시 trust 처리한다.

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

`hooks/user_prompt_submit.py`는 요청 시작 전에 프로젝트 전체 workflow를 gate한다.

담당:

- `STATE.md` 읽기
- 사용자 요청을 `request_type`으로 분류
- 현재 state에서 허용되는 요청인지 확인
- 필요한 경우 transition guard 검사
- 전이가 가능하면 `STATE.md` 갱신
- 전이가 불가능하면 요청 block
- `UNKNOWN` 또는 낮은 confidence 요청에는 추가 context 주입

request type 분류 패턴은 `codex/workflow/request-patterns.yml`에서 관리한다.
자연어 alias를 추가할 때는 Python hook script가 아니라 이 설정 파일을 수정한다.

담당하지 않는 것:

- 기능 구현 세부 절차
- 테스트 작성 규칙
- 커밋/푸쉬/머지 세부 절차
- 기능별 품질 판단

## What AGENTS.md Controls

`AGENTS.md`는 hook을 통과한 뒤 Codex가 실제 작업할 때 지켜야 하는 행동 규칙이다.

핵심:

- 항상 `codex/runtime/STATE.md`를 먼저 읽는다.
- `FEATURE_IMPLEMENTATION`이 아니면 기능 구현 파이프라인을 실행하지 않는다.
- `FEATURE_IMPLEMENTATION`이 아니면 파일 수정은 `docs/`, `codex/runtime/`, `codex/workflow/`로 제한한다.
- `FEATURE_IMPLEMENTATION`일 때만 `docs/FEATURE_IMPLEMENTATION_PIPELINE.md`를 따른다.

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

`DATA_MODEL_DEFINITION` 단계는 `docs/DB_SCHEMA.md`, `prisma/schema.prisma`, baseline migration 산출물을 확정하는 단계다.
실제 DB 서버 배포는 첫 기능 구현을 시작하기 전에 한 번 수행한다.

첫 기능을 `active/`로 옮기기 전에 다음을 확인한다.

```yaml
approvals:
  database_baseline:
    deployed: true
    verified: true
```

이 기록이 없으면 사용자에게 DB provider, environment, 필요한 secret/env 설정을 요청한다.
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

외부 `DESIGN.md`는 frontmatter가 없을 수 있으므로, 이 경우 `codex/runtime/STATE.md`에 approval을 기록한다.

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
- `docs/PROJECT_WORKFLOW.md`: 프로젝트 전체 workflow 설명
- `docs/FEATURE_IMPLEMENTATION_PIPELINE.md`: 기능 단위 구현 파이프라인
- `docs/docs-map.md`: 문서/설정 파일 지도
- `OPTIMIZATION_CHECKLIST.md`: 템플릿 배포/운영 전 개선 후보 체크리스트
