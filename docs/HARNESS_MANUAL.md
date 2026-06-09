# Feature Loop Harness Manual

<br>
<br>

# Part 1. 개요와 구조 이해

<br>
<br>

## 1. 이 매뉴얼의 목적

이 문서는 Feature Loop Harness의 구조와 운영 방식을 이해하기 위한 내부 매뉴얼이다.

해당 매뉴얼에서는 프로젝트 전역의 작업 흐름, 훅/Husky를 통한 제어, AGENTS.md 규칙, 문서 산출물 , 구현 파이프라인 등이 각각 어떤 책임을 가지는지 설명하는 것을 목표로 한다.

<br>
<br>

## 2. 하네스의 핵심 개념

<br>
<br>

## 3. 전체 구조 지도

```text
.
├── .codex/    
│   ├── config.toml # Codex 프로젝트 설정 및 훅 연결 파일
│   ├── hooks.json  # hook 활성화 설정 파일
│   └── hooks/
│       └── user-prompt-submit.sh  # UserPromptSubmit hook에서 실행하는 wrapper script
├── .flh/        # FeatureLoopHarness의 런타임/정책 디렉토리
│   ├── docs/    # 운영 및 지침 관련 문서 디렉토리
│   │   ├── FEATURE_IMPLEMENTATION_PIPELINE.md  # 기능 단위 구현 파이프라인
│   │   └── PROJECT_WORKFLOW.md                 # 프로젝트 전체 파이프라인
│   ├── hooks/
│   │   └── user_prompt_submit.py               # 사용자 요청 분석 및 워크플로우를 제어하는 훅 스크립트
│   ├── runtime/
│   │   └── STATE.md  # 프로젝트 전역 상태 기록 및 제어 문서
│   ├── scripts/  
│   │   └── pre_commit.py   # pre-commit 실제 스크립트 
│   └── workflow/           # 훅이 읽는 워크플로우 관련 문서
│       ├── docs-spec.yml   # 문서별 완료 기준을 담은 문서
│       ├── flow.yml        # 프로젝트 전체 상태 목록 및 상태 별 허용하는 요청 타입을 정의
│       ├── request-patterns.yml  # 사용자 프롬프트의 요청 타입을 분류하기 위한 패턴을 정의
│       ├── state-actions.yml     # 상태별 진행 해야 할 에이전트 행동 규칙
│       └── transition-guards.yml # 상태 전이 시 필요한 guards 조건
├── .husky/
│   ├── pre-commit   # git-hook 실행을 위한 Husky pre-commit 파일
├── app/             # 프로젝트의 실제 소스코드가 들어갈 디렉토리
├── docs/            # 프로젝트 진행에 필요한 기능 및 설계 문서 디렉토리
│   ├── API.md       # API 설계 관련 문서
│   ├── ARCHITECTURE.md  # 아키텍쳐 설계 관련 문서
│   ├── DB_SCHEMA.md     # 데이터 스키마 관련 문서, 해당 파일은 prisma Schema 생성 시 사용됨
│   ├── DESIGN.md        # 프론트앤드 디자인 지침 문서
│   ├── MVP.md           # 프로젝트 MVP 정의 문서
│   ├── QUALITY_SCORE.md # 기능별 품질 점수 문서
│   ├── docs-map.md      # docs/ 및 ./flh 내부 문서들의 인덱스 파일 
│   ├── source-layout.yml  # app/ 내부 디렉토리 구조를 나타내는 파일
│   ├── features/        # 기능 목록 디렉토리
│   │   ├── feature-index.md   # 구현할 기능 목록 및 우선순위에 대한 인덱스 파일 
│   │   ├── active/      # 현재 에이전트가 구현을 진행 중인 기능이 위치하는 디렉토리
│   │   ├── backlog/     # 아직 설계가 시작되지 않았거나 설계 중인 기능이 위치하는 디렉토리
│   │   ├── blocked/     # 이슈로 인해 작업이 중단된 기능이 위치하는 디렉토리
│   │   ├── done/        # 사용자가 최종 승인한 기능이 위치하는 디렉토리
│   │   ├── postponed/   # 보류된 기능이 위치하는 디렉토리
│   │   ├── ready/       # 설계가 완료되어 구현을 대기중인 기능이 위치하는 디렉토리
│   │   └── review/      # 에이전트가 구현은 완료하였으나, 사용자의 최종 검토를 기다리는 기능이 위치하는 디렉토리
│   ├── generated/       # 위의 문서 이외에도 에이전트가 생성한 기타 문서들이 위치하는 디렉토리
│   └── references/      # 에이전트가 참조하면 좋은 문서들이 위치하는 디렉토리
├── scripts/             # 프로젝트 보조 스크립트가 위치하는 디렉토리
├── tests/               
│   ├── e2e/             # 개별 기능의 E2E 테스트 파일이 위치하는 디렉토리
│   └── hooks/           # 훅 테스트 디렉토리
│       ├── test_pre_commit.py          # Pre-commit 테스트 스크립트
│       └── test_user_prompt_submit.py  # UserPromptSubmit Hook 테스트 스크립트
├── .gitignore  
├── AGENTS.md          # 전역 에이전트 작업 규칙
├── HARNESS_MANUAL.md  # flh 운영 매뉴얼
├── README.md
├── package-lock.json
└── package.json
```

<br>
<br>

## 4. 제어 계층

해당 하네스 구조에서는 Codex를 통해 사용자 요청이 들어오는 순간부터 여러 제어 계층들이 아래 순서대로 작동한다.

1. Codex UserPromptSubmit hook
- 사용자 프롬프트의 요청 의도를 분석하여, 현재 프로젝트 진행 상태에서 허용하는 요청인지 확인 및 제어한다.
- 현재 프로젝트 진행 상태에서 허용하는 요청이면 Codex에게 프롬프트를 전달한다.
- 허용하지 않는 요청에 대해서 hook 차원에서 요청을 반환하고 사용자에게 반환 이유를 설명한다.

2. AGENTS.md : 실제 작업 시 반드시 지켜야 할 핵심 지침들을 제시한다.

3. .flh/workflow/ 내부 문서 
- 프로젝트 전체 파이프라인에 대해 각 상태에서 진행해야 할 작업 목록 및 상태 제어를 수행한다.

4. .flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md
- 모든 설계 및 구조화 작업이 끝난 후 실제 구현 시 작동하는 파이프라인

5. Git pre-commit hook(Husky)
- 구현 작업 이후 발생하는 커밋에 대해 검사하는 과정이다.
- 해당 커밋이 하네스 구조가 요구하는 대로 진행되었는지 기계적인 방식으로 확인한다.

<br>
<br>

# Part 2. 프로젝트 런타임 및 워크플로우

<br>
<br>

## 5. 프로젝트 전체 워크플로우

flh는 구현 단계의 하네스 뿐만 아니라, 설계, 지침 생성, DB 배포 등 구현 이외의 원활한 프로젝트 진행을 위해 아래와 같은
파이프라인을 수행한다.

```text
# (p)는 사용자에 의해 생략 가능한 단계

MVP_DEFINITION
-> ARCHITECTURE DESIGN
-> FEATURE_INDEX_DEFINITION
-> DATA_MODEL_DEFINITION(p)
-> API_DESIGN(p)
-> FRONTEND_DESIGN(p)
-> FEATURE_IMPLEMENTATION
```

### 각 단계별 목적 및 산출물
1. MVP_DEFINITION
- 목적 : 전체 프로젝트에 대한 MVP 지침을 생성
- 산출물 : docs/MVP.md

2. ARCHITECTURE_DESIGN
- 목적 : 프로젝트 전체 아키텍쳐 디자인을 수행
- 세부 목표
    - 프로젝트 종류, 패키지 매니져, 세부 스택, 테스팅 도구, 데이터베이스 프로바이더 및 사용여부 등을 결정
    - MVP 문서 기반 아키텍쳐 문서 생성
    - source-layout.yml 기반 app/ 내부 디렉토리 구조 생성(단순 디렉토리 생성만 수행)
- 산출물
    - docs/ARCHITECTURE.md    : 전역 아키텍쳐 문서
    - docs/source-layout.yml  : 소스 레이아웃 및 스택 관련 문서

3. FEATURE_INDEX_DEFINITION
- 목적 : MVP 및 아키텍쳐 문서에 따른 필요한 기능 목록을 생성
- 산출물 : docs/features/feature-index.md   : 기능 목록 인덱스 파일

4. DATA_MODEL_DEFINITION
- 목적 : 프로젝트 전역의 데이터베이스 스키마를 생성하는 과정
- 해당 단계는 프로젝트가 데이터베이스를 필요로 하지 않으면 생략할 수 있음
- 산출물 : docs/DB_SCHEMA.md  -  프로젝트 전역에 대한 DB 스키마 문서

5. API_DESIGN
- 목적 : API 영역 및 앤드포인트 초안을 생성
- 해당 단계는 프로젝트에서 백앤드 영역을 필요로 하지 않으면 생략될 수 있음
- 산출물 : docs/API.md

6. FRONTEND_DESIGN
- 목적 : 프론트앤드 구현 시 참고할 디자인 지침 문서를 생성
- 해당 단계 이전에 에이전트는 사용자에게 선택을 요청한다.
    1. 직접 디자인 지침 문서를 생성할 것인지
    2. 외부에서 디자인 지침 문서(DESIGN.md)를 가져올 것인지
    -> 이 경우 해당 단계는 생략
- 해당 단계는 프로젝트에서 프론트앤드 영역을 필요로 하지 않으면 생략할 수 있음
- 산출물 : docs/DESIGN.md

7. FEATURE_IMPLEMENTATION
- 목적 : 기능 목록에 따른 기능 단위 구현을 진행한다.
- 해당 단계에서는 모든 작업을 .flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md 에 따라 수행한다.

<br>
<br>

## 6. STATE.md

STATE.md는 하네스가 현재 프로젝트 진행 상태를 기억하는 파일이다.
.flh/runtime/STATE.md에 기록되며, Codex Hook과 에이전트는 작업 시작하기 전에 반드시 해당 파일을 읽어 현재 프로젝트 상태를 확인한다.

### STATE.md 구조
```markdown
---
current_state: MVP_DEFINITION
completed_states: []
approvals: {}
last_transition: null
updated_at: null
---
```

해당 파일은 마크다운 형식으로 작성되어 있으나, 해당 파일에서 기계가 읽는 부분은 ---로 둘러 쌓인 YAML frontmatter 뿐이다. 

나머지 본문 내용은 에이전트가 프로젝트 상태 변경을 위해 해당 파일을 수정할 때 참조할 설명과 예시로 구성되어 있다.

### Frontmatter 필드 설명
- `current_state` : 현재 프로젝트 상태
- `completed_states` : 완료되었거나 전이 과정에서 통과한 단계 목록
- `last_transition` : 마지막으로 발생한 상태 전이
- `updated_at` : 마지막 상태 갱신 시각 

### Approvals
해당 필드는 하네스가 "이 일은 사용자가 승인했거나 실제로 검증됐다" 라고 기억해야 하는 항목만 저장하는 공간이다.

프로젝트 전체 진행에 있어서 approvals에 기록해야 하는 작업은 3가지이다.

1. `design`: 프론트엔드 디자인 지침 문서를 외부에서 가져올지, 하네스 흐름 안에서 직접 작성할지를 결정한 뒤 그 승인 내용을 기록하는 필드다.

2. `source_scaffold`: 최초 기능 구현 전에 프로젝트의 기본 스캐폴딩 작업이 완료되고, 해당 변경사항이 커밋까지 진행되었음을 기록하는 필드다.

3. `database_baseline`: 최초 기능 구현 전에 DB baseline이 처리되었는지를 기록하는 필드다. DB가 필요 없는 프로젝트는 skip 기록을 남기고, DB가 필요한 프로젝트는 Prisma baseline 배포와 검증 결과를 남긴다.

<br>
<br>

## 7. 워크플로우 설정 파일

하네스의 워크플로우 관련 정책 문서들은 `.flh/workflow` 내부에 정의되어 있다.
해당 문서들은 사람이 읽는 설명 문서가 아닌, 훅과 에이전트가 실제로 참고하는 설정 문서들이다.

프로젝트 전반의 진행 상황을 이해하고자 한다면 `.flh/docs/PROJECT_WORKFLOW.md` 를 참고하자.

### 7.1. flow.yml
```yaml
# flow 예시
states:
  MVP_DEFINITION:
    description: "Define the actual project's MVP using docs/MVP.md."
    allowed_request_types:
      - MVP_DESIGN_REQUEST
      - STATE_STATUS_REQUEST
      - STATE_TRANSITION_REQUEST
      - UNKNOWN
    next_states:
      - ARCHITECTURE_DESIGN
    ...
```
전체 워크플로우의 상태 목록과 각 상태에서 허용하는 request_type(사용자 요청 의도)를 정의한다.

각 상태에 대한 설명과 허용하는 요청 타입, 그리고 다음 진행할 상태에 대해서 정의하고 있다.


### 7.2. state-actions.yml
```yaml
# state-actions 예시
MVP_DEFINITION:
    required_outputs:
      - docs/MVP.md
    actions:
      - Clarify MVP goal, target users, core problem, scope, non-goals, and success criteria.
      - Update docs/MVP.md.
      - Mark docs/MVP.md as completed only when the MVP scope is clear.
    allowed_extra_writes: []
    ask_user_when:
      - MVP scope is broad, conflicting, or unclear.
```

프로젝트 파이프라인의 각 단계에서 수행해야 할 행동, 필수 추출물, 허용되는 파일 수정 영역, 사용자에게 질문할 때 등을 정의하고 있다.


### 7.3. docs-spec.yml
```yaml
documents:
  mvp:
    path: docs/MVP.md
    purpose: "Template completed by the actual project to define MVP scope."
    required_sections:
      - "MVP Goal"
      - "Target Users"
      - "Core Problem"
      - "In Scope"
      - "Out of Scope"
      - "Success Criteria"
```

프로젝트 파이프라인에서 필요로 하는 각 문서들의 완성 기준에 대해 정의하고 있다.

각 문서들의 완료 여부는 훅에서 상태 전이 시 참조한다.


### 7.4. request-patterns.yml
사용자 프롬프트를 어떤 request type으로 분류할지 결정하는 패턴을 정의한다.


### 7.5. transition-guards.yml
```yaml
transitions:
  MVP_DEFINITION_TO_ARCHITECTURE_DESIGN:
    from: MVP_DEFINITION
    to: ARCHITECTURE_DESIGN
    required_docs:
      - mvp
```
프로젝트가 특정 상태에서 다음 상태로 넘어갈 떄 반드시 확인해야 하는 조건을 정의하는 파일이다.

다음 상태로 전이하기 위해 완료되어 있어야 할 문서, 디렉토리, 명령 등을 정의하고 있다.

<br>
<br>

## 8. 문서 산출물과 완료 기준
하네스에서는 개별 단계마다 필요한 문서 산출물을 정해두고, 해당 문서가 완료되었는지 검사한 후 다음 단계로 넘어간다.

문서 완료 기준은 `.flh/workflow/docs-spec.yml`에 정의되어 있다.

문서들의 기본 완료 조건은 다음과 같다.
- 문서의 `status`가 completed 여야 한다.
- `TODO`, `TBD`, `PLACEHOLDER` 같은 placeholder 문구가 남아 있으면 안 된다.
- 필수 섹션이 모두 존재해야 한다.
- 각 필수 섹션에는 최소한의 내용이 작성되어 있어야 한다.
- YAML 문서의 경우 필수 필드가 모두 채워져 있어야 한다.

예를 들어 `docs/MVP.md`는 `MVP Goal`, `Target Users`, `Core Problem`, `In Scope`, `Out of Scope`, `Success Criteria` 섹션이 모두 있어야 한다.

`docs/source-layout.yml`처럼 기계가 읽는 YAML 문서의 경우에는 섹션이 아니라 `project.type`, `project.package_manager`, `source_roots` 같은 필수 필드가 채워져 있는지를 검사한다.

<br>
<br>

## 9. UserPromptSubmit Hook 동작

해당 하네스에서는 Codex의 `UserPromptSubmit hook`를 통해 매 사용자의 요청에 대해서 프롬프트를 검증하고 있다.

해당 훅의 목적은 사용자의 요청이 현재 프로젝트 상태에서 허용되는 요청인지 확인하는 것이다.
즉 Codex에게 실제 작업을 인가하기 전에 "지금 이 요청을 진행해도 되는 것인가?" 를 기계적으로 판단하는 역할을 한다.

해당 훅의 실행 흐름은 다음과 같다.

```markdown
1. 사용자 프롬프트 입력
2. .codex/hooks/user-prompt-submit.sh 실행
3. 3번의 script가 실제 hook 본체인 .flh/hooks/user_prompt_submit.py를 실행함
4. 사용자 프롬프트의 의도를 분석함
5. 현재 프로젝트 진행 상태를 STATE.md에서 불러옴
6. 현재 상태에서 사용자 요청 의도가 허용되는지 확인함
    6.1. 허용되는 요청이면 Codex에게 프롬프트를 그대로 전달함
    6.2. 허용되지 않는 요청이면, 해당 요청을 처리할 수 있는 상태로 전이 가능한지 확인함
        6.2.A. 전이가 가능하면 STATE.md를 갱신하고 Codex에게 작업을 허용함
        6.2.B. 전이가 불가능하면 hook 단계에서 요청을 차단함
```

이러한 흐름을 통해 하네스는 각 프로젝트 단계에서 필요한 사전 작업이 완료되었는지 확인하고, 준비되지 않은 작업이 임의로 실행되는 것을 방지한다.

<br>
<br>

## 10. 요청 분류 시스템

UserPromptSubmit Hook의 첫번째 단계로, 훅에서 사용자 프롬프트를 받으면 해당 프롬프트의 `request_type`를 분류하는 작업을 수행한다.

### 프롬프트 요청 패턴 확인
요청 분류에 대한 기준은 `.flh/workflow/request-patterns.yml`에서 정의하고 있다.
해당 파일을 통해 표현의 명확도에 따라 패턴을 나누어 사용한다.

- `strong` : 특정 요청 의도를 거의 확실하게 판단할 수 있는 표현
- `alias` : 같은 의도로 해석할 수 있는 비슷한 표현
- `question_or_confirmation_patterns` : 실행 요청이 아니라 질문이나 확인으로 봐야 하는 표현

예를 들어, 사용자 프롬프트가 "MVP 범위 정리해줘" 라고 하면, 'MVP'라는 키워드가 strong 패턴이므로 해당 프롬프트는 `MVP_DESIGN_REQUEST`로 분류된다.

만약 사용자가 보기에 요청이 과하게 차단되거나 반대로 너무 쉽게 허용된다면, `request-patterns.yml`의 패턴을 수정해 요청 분류 기준을 조정할 수 있다.


### 정확도 분석 
요청이 분류되면 동시에 `confidence` 값도 계산한다.
해당 값은 하네스가 해당 분류를 얼마나 확실하게 판단하였는지를 나타낸다.

confidence는 패턴 분석 결과에 따라 아래와 같이 결정된다.
- `high` : 질문 요청 패턴, `/q(질문 모드)`, `/d(문서 모드)`, 혹은 한 개의 정확한 `strong` 과 매칭된 경우
- `medium` : 하나의 `alias`와 매칭된 경우
- `low` : 질문형 표현과 명령형 표현이 섞여있거나, 여러 요청 패턴에 동시에 매칭된 경우
- `unknown` : 어떤 패턴에도 매칭되지 않은 경우

각 confidence에 대해 hook은 다음과 같이 동작한다.
- `high` : 그대로 작업 진행
- `medium` : '사용자가 정정하지 않으면 이 해석대로 진행하라' 라는 내용의 컨텍스트를 추가하여 Codex에게 작업 인가
- `low` : '바로 작업하지 말고 사용자에게 의도를 명확히 할 것을 요청하라' 라는 내용의 컨텍스트를 추가하여 codex에게 작업 전가
- `unknown` : 추가 컨텍스트를 통해서 다음과 같은 추가 지침을 포함하여 Codex에게 인가한다.
  - 파일 변경 없는 설명, 분석, 상태 확인 등의 작업은 진행 가능
  - 코드, 테스트, DB 마이그레이션, 수정 등의 작업은 진행을 엄격히 금지
  - `STATE.md` 변경 금지


<br>
<br>

## 11. Prefix Mode 정책
모든 종류의 사용자 요청을 자연어 패턴만으로 엄격하게 제어하면, 특정 단어가 포함된 질문이나 문서 작업까지 의도치 않게 차단될 수 있다.
예를 들어 “구현”이라는 단어가 들어간 설명 요청이 실제 구현 요청으로 오해되거나, “커밋 정책을 문서에 정리해줘” 같은 문서 작업이 커밋 요청으로 잘못 분류될 수 있다.
Prefix Mode는 이런 애매한 상황에서 사용자가 요청의 성격을 명확히 지정할 수 있도록 제공되는 우회 경로다.

현재 하네스에서 사용할 수 있는 입력 모드는 `/d` 와 `/q` 두 가지이다.
사용자는 프롬프트 맨앞에 prefix를 추가하여 모드를 선택할 수 있다.

### `/q` : 질문 모드
설명, 확인, 의견, 문장 정리 처럼 답변만 필요한 요청을 할 때 사용한다.

질문 모드에서 하지 않는 것
- 파일 생성/수정/삭제
- STATE.md 수정
- 커밋, 푸쉬, 머지 

### `/d` : 문서 및 하네스 제어 모드
프로젝트 내부 문서 및 하네스 문서들을 수정할 떄 사용한다.

해당 모드에서는 다음 범위의 파일만 수정할 수 있다.
- `docs/`
- `.flh/`
- `AGENTS.md`
- `README.md`
- `.codex/`
- `tests/hooks/`
- `.husky/`
- `package.json`
- `package-lock.json`

변경사항이 위의 범위 내애 존재하고, 사용자가 명시적으롤 커밋을 요청한 경우, 커밋을 허용한다.
단, 머지는 허용하지 안흔다.

문서 및 하네스 제어 모드에서 진행하지 않는 것
- 소스 코드 구현/수정/삭제 
- 테스트 생성 및 진행

또한 `/d` 모드에서는 사용자는 프롬프트에 명시함으로써 워크플로우의 다음 상태로 스킵할 수 있다.
단, 프로젝트의 기반이 되는 MVP 설계, 아키텍쳐 설계, 기능 목록 생성 단계는 생략할 수 없다.


<br>
<br>

## 12. 상태 전이 Guard
상태 전이 guard는 프로젝트가 다음 워크플로우 단계로 넘어가기 전에 필요한 조건이 준비되었는지 확인하는 장치다.

하네스는 사용자의 프롬프트를 먼저 요청 타입으로 분류한다.
그리고 현재 상태에서 해당 요청 타입이 허용되지 않으면, 그 요청을 처리할 수 있는 workflow 상태가 있는지 찾는다.
만약 요청을 처리할 수 있는 다음 상태가 존재한다면, 하네스는 `.flh/workflow/transition-guards.yml`에 정의된 조건을 확인하여 전이 가능성을 확인한다.

예를 들어 현재 상태가 `MVP_DEFINITION`인데 사용자가 아키텍처 설계를 요청했다면, 하네스는 `ARCHITECTURE_DESIGN`으로 전이 가능한지 검사한다.
이때 `MVP_DEFINITION_TO_ARCHITECTURE_DESIGN` guard에 따라 `docs/MVP.md`가 완료되어 있어야 한다.

Guard에서 확인하는 대표 조건은 다음과 같다.

- `required_docs`: 반드시 완료되어 있어야 하는 문서
- `required_docs_any`: 여러 문서 중 하나만 완료되어도 되는 조건
- `required_approvals_any`: 여러 approval 중 하나만 있어도 되는 조건
- `required_directories`: 반드시 존재해야 하는 디렉토리
- `required_source_layout_directories`: `docs/source-layout.yml`에 정의된 source directory가 실제로 생성되어 있는지 확인하는 조건

또한 요청 의도를 처리하기 위해 현재 상태보다 여러 단계 뒤의 상태로 전이해야 하는 경우에도, 하네스는 그 사이에 있는 모든 단계의 guard를 순서대로 검사한다.
따라서 중간 단계의 산출물이나 조건이 준비되지 않았다면 뒤 단계 작업으로 바로 넘어갈 수 없다.



<br>
<br>

## 13. AGENTS.md 운영 계약

AGENTS.md에는 훅을 통과한 사용자의 요청에 대해서 Codex가 작업하는 동안 지켜야 할 필수 지침들이 기록되어 있다.

해당 AGENTS.md는 프로젝트 전역에서 에이전트가 반드시 지켜야 할 필수 지침, 매 요청마다 수행해야 할 작업 목록, 참고할 문서 등이 기록되어 있다.

참고할 만한 핵심 지침들은 다음과 같다.
1. 전역 핵심 지침 
- 작업 시작 전 항상 `STATE.md`를 읽어 현재 프로젝트 진행 상태를 불러온다.
- 현재 상태에서 해야할 일들을 `state-actions.yml`에서 불러온다.
- 현재 상태가 `FEATURE_IMPLEMENTATION`이 아니면 절대 구현을 수행하지 않는다.


2. 기능 구현 관련 지침
- 현재 상태가 `FEATURE_IMPLEMENTATION`이고, 사용자가 구현할 것을 명시적으로 요청한 경우 `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`를 기반으로 구현을 수행한다.
- 해당 파이프라인을 통해 구현이 완료된 기능은 사용자의 승인이 있어야 최종적으로 완료 상태에 들어갈 수 있다.
- 모든 구현은 한 번에 하나의 기능에 대한 구현만 수행한다.

3. 사용자 리뷰 관련
- `/review` 디렉토리에 있는 기능에 대한 수정 시 에이전트는 최소 범위의 수정만 진행한다.
- 단, UI/UX 관련 수정이 요청되면, playwright 기반 테스트를 통해 검증을 수행한다.
- 수정사항이 기능의 품질에 변화를 주었다고 판단하면, 해당 기능의 품질 점수를 수정한다.

정리하면 `AGENTS.md`는 Codex가 하네스 안에서 작업할 때 지켜야 하는 행동 규칙이다.
hook이 요청을 통과시켰더라도, Codex는 `AGENTS.md`에 정의된 상태별 작업 범위와 금지 규칙을 계속 따라야 한다.

<br>
<br>

# Part 3. 기능 구현 운영

<br>
<br>

## 14. Feature Implementation Pipeline

- 프로젝트 진행 단계가 '구현' 단계이고, 사용자가 명시적으로 특정 기능에 대한 구현을 요구하면, 에이전트는
`기능 단위 구현 파이프라인`을 통해서 해당 기능에 대한 구현을 진행한다.

- 기능 단위 구현 시 지켜야할 지침은 다음과 같다.
  - 한 번에 단 하나의 기능만 구현한다. 즉 하나의 기능이 완료되기 전에 다른 기능의 구현을 시작하지 않는다.
  - 기능 단위 구현 파이프라인 적용을 위해 `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`를 참고한다.
  - 개별 기능의 완료 기준은 해당 파이프라인의 종료가 아닌, 사용자의 최종 허용이다.

### 기능 단위 파이프라인 구성
개별 기능에 대한 구현은 아래과 같은 순서로 진행된다.

0. Preparation - 준비
1. Design - 설계
1.5 Source Package Scaffold Baseline - 스카폴딩
1.6 Baseline DB Deployment - DB 배포
2. Branch and Worktree - 브랜치 및 워크트리 생성
3. Implementation and Tests - 구현 및 테스트 생성
4. Verification - 검증
4.5 Quality Scoring - 품질 점수 생성 
5. Feedback Loop - 수정 피드백
6. Commit Merge and Cleanup - 머지 및 후처리

이 때 1.5 스카폴딩과 1.6 DB 배포는 프로젝트 전체에 있어서 단 한 번만 수행되는 작업이다.
자세한 내용은 아래의 섹션 16, 17을 참고하자.

### 과정별 작업 내용
#### 0. Preparation - 준비 

해당 단계에서는 구현할 기능의 대상을 확정하고 기능 디렉토리를 준비한다.
준비 단계에서 수행하는 작업은 아래와 같다.

```markdown
1. 사용자가 요청한 기능을 `feature-index.md`에서 찾는다.
2. `feature-index.md` 기능이 존재하지 않으면 해당 문서에 요청된 기능의 정보를 추가한다.
3. 해당 기능 디렉토리를 `docs/features/backlog/FEAT-XXX-name/`에 생성한다.
4. 해당 기능 디렉토리 내부에 `artifacts/` 디렉토리를 생성한다.
   단, `review/`, `active/` 내부에 기능 디렉토리가 하나라도 존재하면 파이프라인을 중단한 후 아직 완료되지 않은 기능이 있음을 사용자에게 알린다.
```

#### 1. Design - 설계

사용자가 요청한 단위 기능의 상세 설계를 작성한다.

설계문서는 준비 과정에서 생성한 기능 디렉토리 내부에 생성한다.

생성해야 할 문서는 다음과 같다:
- `SPEC.md`: 기능 목표, 범위, 비범위, 흐름, 요구사항, 완료 기준, 제약조건
- `CHECKLIST.md`: 실제 구현 시 진행할 체크리스트
- `TEST_CASES.md`: E2E 테스트 파일 생성 시 참고할 테스트 케이스

설계 과정에서 데이터 모델의 변경이 필요한 경우:
- 먼저 `SPEC.md`에 변경 제안을 작성한다.
- `docs/DB_SCHEMA.md`와 충돌 여부를 확인한 후 해당 문서를 업데이트 한다.

설계가 완료된 기능 디렉토리의 구조는 아래와 같아야 한다.
```text
docs/features/backlog/
  FEAT-001-LOGIN/
    SPEC.md
    CHECKLIST.md
    TEST_CASES.md
    artifacts/
```


모든 설계 작업이 종료되면, 해당 기능 디렉토리를 `backlog/`에서 `ready/`로 이동한다.

#### 1.5. Source Package Scaffold Baseline

소스 디렉토리인 app/ 내부의 스카폴딩을 수행하는 단계이다.

자세한 내용은 섹션 16을 참고하자.

#### 1.6. Baseline DB Deployment

`docs/source-layout.yml`의 persistence 설정을 확인해 DB baseline이 필요한지 먼저 판단한다.
DB가 필요 없는 프로젝트는 DB 배포를 실행하지 않고 skip approval을 기록한다.
DB가 필요한 프로젝트는 Prisma schema를 생성하고, 해당 baseline을 실제로 사용할 DB 서버에 배포한다.

자세한 내용은 섹션 17을 참고하자.

#### 2. Branch and Worktree

main/master 브랜치에서 직접 구현하는 것을 막기 위해서 모든 기능 작업 시 해당 기능만을 위한 브랜치/워크트리를 생성한다.

해당 단계에서 진행하는 작업은 다음과 같다.
```markdown
1. `STATE.md`의 approvals를 참고하여 스카폴딩 및 DB baseline 처리 여부가 기록되었는지 확인한다.
2. 완료되었다면 구현할 기능 디렉토리를 `active/`로 이동한다.
3. 브랜치를 생성한다. 해당 브랜치의 이름은 해당 기능 디렉토리의 이름과 같게한다.
4. 워크트리를 생성한다. 워크트리의 이름 또한 해당 기능 디렉토리의 이름과 같게한다.
```

#### 3. Implementation and test - 구현 및 테스트 생성

실제 소스의 구현을 진행하고, 구현된 소스의 테스트 파일을 생성하는 과정이다.

구현 관련 규칙
- 구현 작업은 `SPEC.md`의 범위 및 목표를 준수하며, `CHECKLIST.md`의 작업 항목을 기준으로 수행한다.
- `CHECKLIST.md`에 없는 작업이 필요해지면 작업 전에 먼저 `SPEC.md` 와 `CHECKLIST.md`를 수정한다.
- 프론트엔드 구현 시 `docs/DESIGN.md`를 참고한다.

테스트 파일 생성 관련 규칙
- 단위 테스트 파일은 테스트 대상 파일과 같은 디렉토리에 생성한다.
- E2E 테스트 파일은 `TEST_CASES.md`를 참고하여 `tests/e2e/feature-xxx-feature.e2e.spec.ts`에 생성한다.

요구사항 변경 규칙
- 구현 중 요구사항 변경이 발생하면 코드 수정 전에 설계 문서를 먼저 갱신한다.
- 변경사항이 프로젝트 공통 데이터 모델에 영향을 주면 `docs/DB_SCHEMA.md`도 함께 수정한다.

#### 4. Verification - 검증

검증은 아래와 같은 순서로 진행된다.

1. Lint / Typecheck
2. Unit Test
3. Integration Test
4. E2E Test

규칙
- 검증을 통과하지 못하면 다음 단계로 넘어가지 않는다.
- E2E 결과는 기능의 실제 동작 판단에 우선적으로 참고한다.
- E2E 테스트 중 발생하는 아티팩트들은 해당 기능 디렉토리 내부의 artifacts/ 에 저장한다.

#### 4.5 Quality Scoring
E2E 검증 까지 완료되면, 커밋 전에 구현된 기능의 품질 점수를 기록한다.

작성 위치는 다음과 같다:
- 전역 요약 기록 : `docs/QUALITY.md`
- 개별 상세 점수 : `docs/features/active/FEAT-XXX-name/QUALITY_SCORE.md`

개별 상세 점수 기록 시 다음 기준을 참고하여 진행한다.
- 요구사항 충족 여부 - 30점 만점
- 테스트 겨과 및 커버리지 - 25점 만점
- E2E 결과 및 UX 안정성 - 20점 만점
- 설계 및 범위 충족 - 15점 만점 
- 에러 및 엣지 케이스 핸들링 - 10점 만점

이 때 해당 기능에 대한 품질 점수가 70점을 넘지 못하면 해당 기능에 대한 재작업을 수행한다.
단, 70점을 넘더라도 구현 범위를 과하게 위반하거나 데이터 모델과 충돌하는 등 심각한 위반사항이 존재한다고 판단되면 커밋을 수행하지 않는다.

해당 품질 점수는 이후 리팩토링 과정에서 우선순위를 결정하는 데 사용된다.


#### 5. Feedback Loop - 피드백 루프

검증을 실패하는 경우 다음 루프를 통해 수정을 진행한다.

```
검증 실패
-> 원인 수정 
-> 관련 테스트 재실행
-> 전체 검증(4번) 재실행
```

- 수정사항이 `SPEC.md` 를 벗어나면, 구현을 멈추고 설계 문서를 먼저 수정한다.
- 외부 의존성, 결정 대기 등의 이슈로 진행이 불가능하다고 판단되면 해당 기능 디렉토리를 `blocked/` 로 이동한다.

#### 6. Commit Merge and Cleanup - 머지 및 후처리

검증을 마친 기능에 대해서 커밋 및 머지를 수행한다.

커밋 메시지는 다음과 같다 : feat(scope): description

머지 이후 후처리 목록
1. 메인 브랜치에 정상 머지 여부를 확인한다.
2. 로컬 브랜치와 동기화 상태를 확인한다.
3. 머지가 완료된 워크트리와 브랜치를 삭제한다.
4. 관련 임시/테스트/디버그 파일을 정리한다.
5. 해당 기능 디렉토리를 `docs/features/review/`로 이동한다.
6. `docs/features/feature-index.md`에 review 상태, 요약, 참조 경로를 갱신한다.
7. `docs/QUALITY_SCORE.md`의 해당 기능 점수와 상세 점수 파일 경로를 갱신한다.
8. 사용자의 최종 완료 승인이 있기 전까지 `done/`으로 이동하지 않는다.

기능 디렉토리를 `docs/features/review/`로 이동하면 최초 구현 파이프라인은 종료된다.
이후 사용자 검토/수정 요청은 `AGENTS.md`의 review 규칙을 따른다.

<br>
<br>

## 15. Feature State Directories

기능 구현 상태는 `docs/features/` 내부 디렉토리 위치를 기준으로 판단한다.

### 상태 목록 및 디렉토리 구조
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

각 디렉토리 의미:

- `backlog/`: 설계 대상으로 선택되었지만 아직 `SPEC.md`, `CHECKLIST.md`, `TEST_CASES.md`가 완성되지 않은 기능
- `ready/`: 기능 설계 문서 3개가 작성되어 구현 가능한 기능
- `active/`: 브랜치/워크트리 생성 후 현재 구현 중인 기능
- `blocked/`: 외부 의존성이나 결정 대기로 멈춘 기능
- `review/`: 최초 구현 초안, 검증, 품질 점수 작성이 끝났고 사용자가 확인/수정 중인 기능
- `done/`: 사용자가 최종 완료 승인한 기능
- `postponed/`: 보류 또는 연기된 기능


<br>
<br>

## 16. Source Package Scaffold Baseline

Source Package Scaffold Baseline은 첫 기능 구현을 시작하기 전에 프로젝트의 기본 소스 디렉토리와 패키지 구조를 준비하는 단계다.

이 단계에서는 `docs/source-layout.yml`에 정의된 구조를 기준으로 필요한 package 설정, 기본 script, 테스트/린트 설정, 최소 실행 파일 등을 준비한다.

목적은 기능 구현이 시작된 뒤에 패키지 구조나 기본 설정이 없어 흐름이 끊기는 일을 막는 것이다.
즉, 이후 기능 구현, 테스트 실행, 커밋 훅 검증이 같은 기준 위에서 자연스럽게 이어질 수 있도록 프로젝트의 기본 개발 기반을 먼저 맞춰두는 단계다.

### 스카폴딩 실행 조건
- 프로젝트 전체에 대한 첫번째 기능 구현 시
- `.flh/runtime/STATE.md`에 `approvals.source_scaffold.created:true`가 없을 때

### 절차
1. `docs/source-layout.yml` 을 읽고, source roots, 패키지 매니저, 워크스페이스, 프레임웤, 런타임, 언어, 모듈 타입, 테스팅 도구 등을 결정한다. 
2. 해당 문서에 누락된 정보가 있거나, 스카폴딩을 위해 더 필요한 정보가 있다고 판단되면 사용자에게 요청한다.
3. main/master 브랜치에서 스카폴딩 과정을 수행한다.
4. 생성된 파일이 허용 범위 안에 있는지 확인한다.
5. `.flh/runtime/STATE.md`에 `approvals.source_scaffold.created:true`를 기록한다.
6. 생성된 베이스라인 파일과 `STATE.md` 를 함꼐 커밋한다.

### 허용 범위 
- package-level `package.json`
- package manager/workspace 설정
- lint/typecheck/test script
- TypeScript 또는 runtime config
- lint/format/test runner config
- 최소 entry file
- Prisma를 사용하는 backend package의 기본 연결 구조
- 빈 source directory를 유지하기 위한 `.gitkeep`


<br>
<br>

## 17. Baseline DB Deployment

Baseline DB Deployment는 첫 기능 구현 전에 DB baseline 처리 여부를 확정하는 단계다.

### 판단 기준
- `docs/source-layout.yml`의 `project.persistence.database_required` 값을 먼저 확인한다.
- `database_required: false`이면 DB를 사용하지 않는 프로젝트로 보고, DB 배포를 수행하지 않는다.
- `database_required: true`이면 DB-backed 프로젝트로 보고, Prisma 기준의 baseline 생성을 수행한다.
- persistence 값이 없거나 애매하면 에이전트가 임의로 판단하지 않고 사용자에게 확인한다.

### DB 미사용 프로젝트
- Prisma schema, migration, DB deploy script를 생성하지 않는다.
- `.flh/runtime/STATE.md`에 `approvals.database_baseline.required: false`와 `approvals.database_baseline.skipped: true`를 기록한다.
- skip approval을 기록하는 커밋에는 source file 변경을 포함하지 않는다.
- 이 기록이 있으면 이후 기능 구현 루프에서 1.6을 다시 요구하지 않는다.

### DB-backed 프로젝트
- 공식 자동 baseline은 Prisma만 대상으로 한다.
- `docs/DB_SCHEMA.md`의 Prisma-ready 명세를 기준으로 `app/be/prisma/schema.prisma`를 생성한다.
- baseline migration을 생성하고 실제 개발 DB에 반영한다.
- `db:deploy`, `db:verify` 같은 명령으로 배포와 검증을 수행한다.
- 성공하면 `.flh/runtime/STATE.md`에 `approvals.database_baseline.required: true`와 `approvals.database_baseline.verified: true`를 기록한다.

### 주의사항
- 비밀값, API key, token, password, DB connection string은 `STATE.md`나 문서에 기록하지 않는다.
- Prisma가 아닌 ORM, migration tool, raw SQL baseline은 현재 하네스의 공식 자동 처리 범위가 아니다.
- `approvals.database_baseline` 기록이 없으면 다음 기능 구현 루프에서도 1.6 단계가 다시 요구될 수 있다.

<br>
<br>

## 18. Review Patch Flow

<br>
<br>

## 19. Quality Scoring

<br>
<br>

# Part 4. Git, 검증, 실행 환경

<br>
<br>

## 20. Pre-commit Guard

<br>
<br>

## 21. Branch와 Commit 정책

<br>
<br>

## 22. 설치와 최초 설정

<br>
<br>

## 23. 테스트와 검증

<br>
<br>

## 24. Troubleshooting

<br>
<br>

# Part 5. 유지보수와 운영 사례

<br>
<br>

## 25. 정책 변경 가이드

<br>
<br>

## 26. 운영 예시

<br>
<br>

## 27. 설계 원칙과 한계
