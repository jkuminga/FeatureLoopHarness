#!/usr/bin/env python3
"""UserPromptSubmit hook for the harness workflow.

The hook is intentionally deterministic. It does not call an LLM.

Input:
  - argv text
  - stdin plain text
  - stdin JSON with one of: prompt, user_prompt, message, input
  - USER_PROMPT environment variable

Output:
  Codex hook-compatible JSON.

Exit codes:
  0: hook decision emitted
  1: hook error
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".flh/runtime/STATE.md"
FLOW_PATH = ROOT / ".flh/workflow/flow.yml"
DOCS_SPEC_PATH = ROOT / ".flh/workflow/docs-spec.yml"
TRANSITION_GUARDS_PATH = ROOT / ".flh/workflow/transition-guards.yml"
REQUEST_PATTERNS_PATH = ROOT / ".flh/workflow/request-patterns.yml"

ALLOW_EXIT_CODE = 0
ERROR_EXIT_CODE = 1
QUESTION_PREFIXES = ("/q",)
DOCUMENTATION_PREFIXES = ("/d",)


@dataclass
class HookResult:
    action: str
    request_type: str
    confidence: str
    current_state: str | None
    target_state: str | None = None
    updated_state: str | None = None
    reason: str | None = None
    additional_prompt: str | None = None
    missing: list[str] | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "action": self.action,
                "request_type": self.request_type,
                "confidence": self.confidence,
                "current_state": self.current_state,
                "target_state": self.target_state,
                "updated_state": self.updated_state,
                "reason": self.reason,
                "additional_prompt": self.additional_prompt,
                "missing": self.missing or [],
            },
            ensure_ascii=False,
            indent=2,
        )


@dataclass
class RequestClassification:
    request_type: str
    confidence: str
    matched_kinds: list[str]
    matched_request_types: list[str]


# Fallback only. The editable source of truth is .flh/workflow/request-patterns.yml.
REQUEST_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "PRISMA_BASELINE_CREATE_REQUEST",
        [
            r"prisma.*baseline",
            r"baseline.*prisma",
            r"schema\.prisma",
            r"프리즈마.*베이스라인",
            r"프리즈마.*생성",
            r"prisma.*생성",
        ],
    ),
    (
        "IMPLEMENTATION_REQUEST",
        [
            r"구현해",
            r"코드.*작성",
            r"컴포넌트.*만들",
            r"api.*구현",
            r"파일.*수정",
            r"앱.*수정",
            r"작업.*진행",
        ],
    ),
    ("TEST_REQUEST", [r"테스트.*작성", r"테스트.*실행", r"e2e", r"unit test", r"유닛"]),
    ("COMMIT_REQUEST", [r"커밋", r"commit", r"push", r"푸쉬", r"merge", r"머지"]),
    (
        "FEATURE_PREPARE_REQUEST",
        [
            r"기능.*준비",
            r"feature.*prepare",
            r"backlog",
            r"기능.*디렉토리.*생성",
        ],
    ),
    (
        "FEATURE_DESIGN_REQUEST",
        [
            r"기능.*설계",
            r"SPEC\.md",
            r"CHECKLIST\.md",
            r"TEST_CASES\.md",
            r"기능.*스펙",
        ],
    ),
    (
        "MVP_DESIGN_REQUEST",
        [r"\bmvp\b", r"MVP", r"엠브이피", r"최소.*제품", r"최소.*범위"],
    ),
    (
        "ARCHITECTURE_DESIGN_REQUEST",
        [r"아키텍처", r"아키텍쳐", r"architecture", r"시스템.*구조"],
    ),
    (
        "FEATURE_INDEX_REQUEST",
        [r"feature-index", r"기능.*목록", r"기능.*리스트", r"Feature Index"],
    ),
    (
        "DATA_MODEL_DESIGN_REQUEST",
        [r"데이터.*모델", r"DB_SCHEMA", r"ERD", r"E-R", r"엔티티", r"schema"],
    ),
    ("API_DESIGN_REQUEST", [r"\bAPI\b", r"api", r"엔드포인트", r"endpoint"]),
    (
        "FRONTEND_DESIGN_REQUEST",
        [r"프론트", r"frontend", r"FRONTEND", r"디자인.*지침", r"UI.*지침"],
    ),
    (
        "STATE_STATUS_REQUEST",
        [
            r"현재.*상태",
            r"진행.*상황",
            r"다음.*할",
            r"남은.*작업",
            r"요약",
            r"상태.*알려",
        ],
    ),
    ("STATE_TRANSITION_REQUEST", [r"다음.*단계", r"전이", r"상태.*변경"]),
]


REQUEST_ALIASES: list[tuple[str, list[str]]] = [
    (
        "MVP_DESIGN_REQUEST",
        [
            r"초기.*범위.*정리",
            r"1차.*출시.*범위",
            r"핵심.*범위",
            r"어디까지.*만들",
            r"가장.*먼저.*만들",
            r"필수.*기능.*추",
            r"첫.*버전.*범위",
            r"프로젝트.*목표.*정리",
            r"타겟.*사용자.*정리",
            r"해결.*문제.*정리",
        ],
    ),
    (
        "ARCHITECTURE_DESIGN_REQUEST",
        [
            r"전체.*구조",
            r"기술.*구조",
            r"프로젝트.*구조",
            r"폴더.*구조",
            r"모듈.*구조",
            r"레이어.*구조",
            r"서비스.*구성",
            r"백엔드.*프론트.*연결",
        ],
    ),
    (
        "FEATURE_INDEX_REQUEST",
        [
            r"필요한.*기능.*정리",
            r"구현할.*기능.*뽑",
            r"기능.*리스트업",
            r"기능.*우선순위",
            r"기능.*인덱스",
            r"MVP.*기능.*나",
            r"기능.*단위.*쪼",
            r"작업할.*기능.*정리",
        ],
    ),
    (
        "DATA_MODEL_DESIGN_REQUEST",
        [
            r"데이터.*구조",
            r"테이블.*구조",
            r"DB.*구조",
            r"ER.*구조",
            r"관계.*정의",
            r"스키마.*초안",
            r"도메인.*모델",
            r"저장.*데이터",
            r"Prisma.*모델.*방향",
        ],
    ),
    (
        "PRISMA_BASELINE_CREATE_REQUEST",
        [
            r"Prisma.*baseline.*만들",
            r"schema\.prisma.*생성",
            r"Prisma.*초기.*스키마",
            r"Prisma.*모델.*생성",
            r"DB.*baseline.*생성",
            r"초기.*migration",
            r"baseline.*migration",
            r"Prisma.*migration.*준비",
        ],
    ),
    (
        "API_DESIGN_REQUEST",
        [
            r"API.*목록",
            r"엔드포인트.*목록",
            r"API.*스펙",
            r"요청.*응답.*구조",
            r"라우트.*구조",
            r"서버.*API.*설계",
            r"백엔드.*API.*설계",
            r"API.*계약",
        ],
    ),
    (
        "FRONTEND_DESIGN_REQUEST",
        [
            r"화면.*설계",
            r"UI.*방향",
            r"프론트.*구조",
            r"화면.*흐름",
            r"페이지.*구성",
            r"사용자.*플로우",
            r"디자인.*가이드",
            r"컴포넌트.*방향",
            r"레이아웃.*방향",
        ],
    ),
    (
        "FEATURE_PREPARE_REQUEST",
        [
            r"이.*기능.*준비",
            r"기능.*작업.*준비",
            r"기능.*문서.*공간",
            r"feature.*workspace",
            r"작업.*대상.*올",
            r"기능.*ready",
            r"feature-index.*추가.*준비",
        ],
    ),
    (
        "FEATURE_DESIGN_REQUEST",
        [
            r"이.*기능.*설계",
            r"기능.*스펙.*작성",
            r"SPEC.*작성",
            r"체크리스트.*만들",
            r"테스트.*케이스.*정리",
            r"구현.*전.*기능.*문서",
            r"기능.*요구사항.*정리",
            r"기능.*범위.*정리",
            r"기능.*완료.*기준",
        ],
    ),
    (
        "IMPLEMENTATION_REQUEST",
        [
            r"이.*기능.*구현",
            r"개발.*시작",
            r"코드.*반영",
            r"실제.*코드.*작성",
            r"앱.*반영",
            r"기능.*붙",
            r"화면.*만들",
            r"API.*만들",
            r"컴포넌트.*만들",
            r"로직.*작성",
            r"수정.*반영",
        ],
    ),
    (
        "TEST_REQUEST",
        [
            r"테스트.*만들",
            r"테스트.*추가",
            r"검증해",
            r"테스트.*돌",
            r"E2E.*만들",
            r"유닛.*테스트.*만들",
            r"통합.*테스트.*작성",
            r"테스트.*케이스.*코드",
        ],
    ),
    (
        "COMMIT_REQUEST",
        [
            r"PR.*만들",
            r"브랜치.*정리",
            r"작업.*마무리",
            r"후처리.*진행",
            r"변경사항.*올",
        ],
    ),
    (
        "STATE_STATUS_REQUEST",
        [
            r"어디까지.*됐",
            r"현재.*단계",
            r"뭐.*해야",
            r"뭐부터.*하면",
            r"다음.*작업.*추천",
        ],
    ),
    (
        "STATE_TRANSITION_REQUEST",
        [
            r"다음.*단계.*넘어",
            r"단계.*변경",
            r"단계.*완료.*처리",
            r"workflow.*이동",
            r"이.*단계.*끝",
            r"다음.*상태.*바",
        ],
    ),
]

QUESTION_OR_CONFIRMATION_PATTERNS: list[str] = [
    r"\?",
    r"맞아\??$",
    r"맞나\??$",
    r"되나\??$",
    r"되는거지\??$",
    r"하면 되는거지\??$",
    r"해야 하나\??$",
    r"해도 돼\??$",
    r"괜찮아\??$",
    r"어떻게 생각",
    r"어때",
    r"맞을까",
    r"좋을까",
    r"수정하면 되는거지\??$",
    r"바꾸면 되는거지\??$",
    r"진행하면 되는거지\??$",
]


def read_prompt() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()

    raw = sys.stdin.read().strip()
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return raw

        if isinstance(payload, dict):
            for key in ("prompt", "user_prompt", "message", "input"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        if isinstance(payload, str):
            return payload.strip()

    return os.environ.get("USER_PROMPT", "").strip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "None", "~"}:
        return None
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value

# YAML 파서 구현 
def parse_yaml_subset(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by this harness.

    Supported:
      - nested mappings by indentation
      - block lists using "- value"
      - inline empty list/dict
      - scalar strings/bools/null
    """

    root: dict[str, Any] = {}
    stack: list[tuple[int, Any]] = [(-1, root)]

    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if stripped.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"Invalid list item at line {index + 1}: {raw_line}")
            parent.append(parse_scalar(stripped[2:]))
            continue

        if ":" not in stripped:
            raise ValueError(f"Invalid YAML line {index + 1}: {raw_line}")

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        if value:
            if not isinstance(parent, dict):
                raise ValueError(f"Invalid mapping at line {index + 1}: {raw_line}")
            parent[key] = parse_scalar(value)
            continue

        next_value: Any = {}
        for lookahead in lines[index + 1 :]:
            if not lookahead.strip() or lookahead.lstrip().startswith("#"):
                continue
            next_stripped = lookahead.strip()
            next_value = [] if next_stripped.startswith("- ") else {}
            break

        if not isinstance(parent, dict):
            raise ValueError(f"Invalid nested mapping at line {index + 1}: {raw_line}")
        parent[key] = next_value
        stack.append((indent, next_value))

    return root


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required workflow file is missing: {path}")
    return parse_yaml_subset(path.read_text(encoding="utf-8"))


def load_request_patterns() -> tuple[list[tuple[str, list[str]]], list[tuple[str, list[str]]]]:
    if not REQUEST_PATTERNS_PATH.exists():
        return REQUEST_PATTERNS, REQUEST_ALIASES

    config = load_yaml(REQUEST_PATTERNS_PATH)
    patterns: list[tuple[str, list[str]]] = []
    aliases: list[tuple[str, list[str]]] = []

    for request_type, request_config in (config.get("patterns") or {}).items():
        if not isinstance(request_config, dict):
            continue
        strong_patterns = request_config.get("strong") or []
        alias_patterns = request_config.get("aliases") or []
        patterns.append((request_type, list(strong_patterns)))
        aliases.append((request_type, list(alias_patterns)))

    return patterns, aliases


def load_question_or_confirmation_patterns() -> list[str]:
    if not REQUEST_PATTERNS_PATH.exists():
        return QUESTION_OR_CONFIRMATION_PATTERNS

    config = load_yaml(REQUEST_PATTERNS_PATH)
    patterns = config.get("question_or_confirmation_patterns") or []
    return list(patterns) if patterns else QUESTION_OR_CONFIRMATION_PATTERNS


# markdown frontmatter 파싱
def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    frontmatter = parse_yaml_subset(parts[1])
    body = parts[2].lstrip()
    return frontmatter, body


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        raise FileNotFoundError(f"STATE file is missing: {STATE_PATH}")
    frontmatter, _ = parse_frontmatter(STATE_PATH.read_text(encoding="utf-8"))
    return frontmatter


def format_yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        if value == "":
            return '""'
        if re.search(r"[:#\[\]{}]|^\s|\s$", value):
            return json.dumps(value, ensure_ascii=False)
        return value
    return str(value)


def append_yaml_value(lines: list[str], key: str, value: Any, indent: int = 0) -> None:
    prefix = " " * indent
    if isinstance(value, dict):
        if not value:
            lines.append(f"{prefix}{key}: {{}}")
            return
        lines.append(f"{prefix}{key}:")
        for child_key, child_value in value.items():
            append_yaml_value(lines, str(child_key), child_value, indent + 2)
        return

    if isinstance(value, list):
        if not value:
            lines.append(f"{prefix}{key}: []")
            return
        lines.append(f"{prefix}{key}:")
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{prefix}  -")
                for child_key, child_value in item.items():
                    append_yaml_value(lines, str(child_key), child_value, indent + 4)
            else:
                lines.append(f"{prefix}  - {format_yaml_scalar(item)}")
        return

    lines.append(f"{prefix}{key}: {format_yaml_scalar(value)}")


def write_state(state: dict[str, Any]) -> None:
    lines = ["---"]
    for key in ("current_state", "completed_states", "approvals", "last_transition", "updated_at"):
        append_yaml_value(lines, key, state.get(key))
    lines.extend(
        [
            "---",
            "",
            "# STATE",
            "",
            "현재 하네스가 적용될 실제 프로젝트의 진행 상태를 저장한다.",
            "",
            "이 파일은 하네스 자체의 개발 진행 상태가 아니라, 하네스를 사용해 진행할 실제 프로젝트의 워크플로우 상태를 나타낸다.",
            "",
            f"현재 상태는 `{state.get('current_state')}`이다.",
            "",
        ]
    )
    STATE_PATH.write_text("\n".join(lines), encoding="utf-8")


def request_type_priority() -> dict[str, int]:
    patterns, _ = load_request_patterns()
    return {request_type: index for index, (request_type, _) in enumerate(patterns)}


def collect_request_matches(prompt: str) -> dict[str, set[str]]:
    normalized = prompt.strip()
    matches: dict[str, set[str]] = {}
    patterns, aliases = load_request_patterns()

    for request_type, strong_patterns in patterns:
        for pattern in strong_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                matches.setdefault(request_type, set()).add("strong")

    for request_type, alias_patterns in aliases:
        for pattern in alias_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                matches.setdefault(request_type, set()).add("alias")

    return matches


def is_question_or_confirmation(prompt: str) -> bool:
    normalized = prompt.strip()
    return any(
        re.search(pattern, normalized, re.IGNORECASE)
        for pattern in load_question_or_confirmation_patterns()
    )


def starts_with_prefix(prompt: str, prefixes: tuple[str, ...]) -> bool:
    normalized = prompt.strip()
    return any(
        normalized == prefix or normalized.startswith(f"{prefix} ")
        for prefix in prefixes
    )


def is_merge_command(prompt: str) -> bool:
    normalized = prompt.strip()
    return bool(
        re.search(r"\bmerge\s*(해줘|하자|진행|처리|해|하셈)", normalized, re.IGNORECASE)
        or re.search(r"머지\s*(해줘|하자|진행|처리|해|하셈)", normalized, re.IGNORECASE)
    )


def classify_prompt(prompt: str) -> RequestClassification:
    if starts_with_prefix(prompt, QUESTION_PREFIXES):
        return RequestClassification(
            request_type="QUESTION_OR_CONFIRMATION_REQUEST",
            confidence="high",
            matched_kinds=["prefix"],
            matched_request_types=["QUESTION_OR_CONFIRMATION_REQUEST"],
        )

    if starts_with_prefix(prompt, DOCUMENTATION_PREFIXES):
        return RequestClassification(
            request_type="DOCUMENTATION_REQUEST",
            confidence="high",
            matched_kinds=["prefix"],
            matched_request_types=["DOCUMENTATION_REQUEST"],
        )

    is_question = is_question_or_confirmation(prompt)
    matches = collect_request_matches(prompt)

    if is_question and matches:
        priority = request_type_priority()
        matched_request_types = sorted(matches, key=lambda item: priority.get(item, 999))
        selected = matched_request_types[0]
        return RequestClassification(
            request_type=selected,
            confidence="low",
            matched_kinds=["question_or_confirmation", *sorted(matches[selected])],
            matched_request_types=["QUESTION_OR_CONFIRMATION_REQUEST", *matched_request_types],
        )

    if is_question:
        return RequestClassification(
            request_type="QUESTION_OR_CONFIRMATION_REQUEST",
            confidence="high",
            matched_kinds=["question_or_confirmation"],
            matched_request_types=["QUESTION_OR_CONFIRMATION_REQUEST"],
        )

    if not matches:
        return RequestClassification(
            request_type="UNKNOWN",
            confidence="unknown",
            matched_kinds=[],
            matched_request_types=[],
        )

    priority = request_type_priority()
    matched_request_types = sorted(matches, key=lambda item: priority.get(item, 999))
    selected = matched_request_types[0]

    if len(matched_request_types) > 1:
        confidence = "low"
    elif "strong" in matches[selected]:
        confidence = "high"
    else:
        confidence = "medium"

    return RequestClassification(
        request_type=selected,
        confidence=confidence,
        matched_kinds=sorted(matches[selected]),
        matched_request_types=matched_request_types,
    )


def classify_request_type(prompt: str) -> str:
    return classify_prompt(prompt).request_type


def is_allowed(flow: dict[str, Any], state: str, request_type: str) -> bool:
    state_config = flow.get("states", {}).get(state, {})
    return request_type in state_config.get("allowed_request_types", [])


def find_target_state(flow: dict[str, Any], request_type: str) -> str | None:
    for state, config in flow.get("states", {}).items():
        if request_type in config.get("allowed_request_types", []):
            return state
    return None


def find_state_path(flow: dict[str, Any], start: str, target: str) -> list[str] | None:
    queue: deque[list[str]] = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        current = path[-1]
        if current == target:
            return path
        next_states = flow.get("states", {}).get(current, {}).get("next_states", [])
        for next_state in next_states:
            if next_state not in visited:
                visited.add(next_state)
                queue.append(path + [next_state])
    return None


def transition_key(from_state: str, to_state: str) -> str:
    return f"{from_state}_TO_{to_state}"


def section_body(text: str, section: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(section)}\s*$([\s\S]*?)(?=^##\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def markdown_table_headers(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines[:-1]):
        next_line = lines[index + 1]
        if not (line.startswith("|") and line.endswith("|")):
            continue
        if not (next_line.startswith("|") and next_line.endswith("|")):
            continue
        separator_cells = [cell.strip() for cell in next_line.strip("|").split("|")]
        if separator_cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator_cells):
            return [cell.strip() for cell in line.strip("|").split("|")]
    return []


def doc_is_complete(doc_key: str, docs_spec: dict[str, Any]) -> tuple[bool, list[str]]:
    defaults = docs_spec.get("defaults", {})
    doc_config = docs_spec.get("documents", {}).get(doc_key)
    if not doc_config:
        return False, [f"Unknown docs-spec document key: {doc_key}"]

    candidates = [doc_config.get("path")] + list(doc_config.get("alternative_paths", []) or [])
    failures: list[str] = []

    for candidate in candidates:
        if not candidate:
            continue
        path = ROOT / candidate
        if not path.exists():
            failures.append(f"Missing document: {candidate}")
            continue

        text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        required_status = doc_config.get("required_status", defaults.get("required_status"))
        if required_status and frontmatter.get("status") != required_status:
            failures.append(f"{candidate}: status is not {required_status}")
            continue

        forbidden_tokens = doc_config.get("forbidden_tokens", defaults.get("forbidden_tokens", []))
        found_token = next((token for token in forbidden_tokens if token in body), None)
        if found_token:
            failures.append(f"{candidate}: forbidden token remains: {found_token}")
            continue

        missing_sections = [
            section
            for section in doc_config.get("required_sections", [])
            if not re.search(rf"^##\s+{re.escape(section)}\s*$", body, re.MULTILINE)
        ]
        if missing_sections:
            failures.append(f"{candidate}: missing sections: {', '.join(missing_sections)}")
            continue

        min_chars = int(doc_config.get("min_section_chars", defaults.get("min_section_chars", 0)) or 0)
        short_sections = [
            section
            for section in doc_config.get("required_sections", [])
            if len(section_body(body, section)) < min_chars
        ]
        if short_sections:
            failures.append(f"{candidate}: sections too short: {', '.join(short_sections)}")
            continue

        required_item_fields = doc_config.get("required_item_fields", []) or []
        if required_item_fields:
            table_text = section_body(body, "Feature List")
            headers = markdown_table_headers(table_text)
            missing_fields = [field for field in required_item_fields if field not in headers]
            if missing_fields:
                failures.append(
                    f"{candidate}: feature table missing fields: {', '.join(missing_fields)}"
                )
                continue

        return True, []

    return False, failures


def approval_is_granted(approval_key: str, state_data: dict[str, Any]) -> bool:
    approvals = state_data.get("approvals") or {}
    approval = approvals.get(approval_key) if isinstance(approvals, dict) else None
    if approval is True:
        return True
    if isinstance(approval, dict):
        return approval.get("approved") is True
    return False


def check_transition_guards(
    path: list[str],
    docs_spec: dict[str, Any],
    guards: dict[str, Any],
    state_data: dict[str, Any],
) -> tuple[bool, list[str]]:
    missing: list[str] = []
    transitions = guards.get("transitions", {})

    for from_state, to_state in zip(path, path[1:]):
        key = transition_key(from_state, to_state)
        guard = transitions.get(key)
        if not guard:
            missing.append(f"Missing transition guard: {key}")
            continue

        for doc_key in guard.get("required_docs", []) or []:
            ok, failures = doc_is_complete(doc_key, docs_spec)
            if not ok:
                missing.extend(failures)

        docs_any = guard.get("required_docs_any", []) or []
        approvals_any = guard.get("required_approvals_any", []) or []
        if docs_any or approvals_any:
            any_passed = False
            any_failures: list[str] = []

            for doc_key in docs_any:
                ok, failures = doc_is_complete(doc_key, docs_spec)
                if ok:
                    any_passed = True
                    break
                any_failures.extend(failures)

            if not any_passed:
                for approval_key in approvals_any:
                    if approval_is_granted(approval_key, state_data):
                        any_passed = True
                        break

            if not any_passed:
                expected = list(docs_any) + [f"approval:{key}" for key in approvals_any]
                missing.append("Missing one of: " + ", ".join(expected))
                missing.extend(any_failures)

        for rel_path in guard.get("required_files", []) or []:
            if not (ROOT / rel_path).exists():
                missing.append(f"Missing required file: {rel_path}")

        for rel_path in guard.get("required_directories", []) or []:
            if not (ROOT / rel_path).is_dir():
                missing.append(f"Missing required directory: {rel_path}")

    return not missing, missing


def unknown_additional_prompt() -> str:
    return (
        "[Harness Guard]\n"
        "This request was classified as UNKNOWN by user_prompt_submit.py.\n\n"
        "- If it can be answered without creating, modifying, or deleting files, proceed.\n"
        "- If it is a design/documentation request, file changes are allowed only in docs/ or .flh/.\n"
        "- If it requires code, tests, DB migrations, app/src/apps changes, commits, or state transitions, do not proceed.\n"
        "- Ask the user to clarify the intended workflow request type when the requested action is not clearly documentation-only.\n"
        "- Do not update .flh/runtime/STATE.md.\n"
        "- Do not run .flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md."
    )


def question_or_confirmation_additional_prompt() -> str:
    return (
        "[Harness Guard]\n"
        "This request was classified as QUESTION_OR_CONFIRMATION_REQUEST.\n\n"
        "- If the prompt starts with /q, treat /q as a control prefix and not as user content.\n"
        "- Treat it as a question, confirmation, or discussion request.\n"
        "- Answer directly without creating, modifying, or deleting files.\n"
        "- Do not update .flh/runtime/STATE.md.\n"
        "- Do not start implementation, tests, commits, state transitions, or feature pipeline work."
    )


def documentation_additional_prompt() -> str:
    return (
        "[Harness Guard]\n"
        "This request used /d documentation mode.\n\n"
        "- Treat /d as a control prefix and not as user content.\n"
        "- Perform only documentation or harness-maintenance work.\n"
        "- Allowed write targets: docs/, .flh/, AGENTS.md, README.md.\n"
        "- Allowed harness-maintenance targets when directly relevant: .codex/, .flh/hooks/, tests/hooks/, .husky/, package.json.\n"
        "- Do not modify app/, apps/, src/, implementation code, tests/e2e/, Prisma migrations, or DB schema/migration files.\n"
        "- Do not run .flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md as an implementation workflow.\n"
        "- Do not create worktrees or branches.\n"
        "- Commit and push are allowed only when the user explicitly asks and all changed files are within the allowed documentation/harness targets.\n"
        "- Merge is not allowed in /d mode."
    )


def low_confidence_additional_prompt(classification: RequestClassification) -> str:
    return (
        "[Harness Guard]\n"
        "This request matched multiple or conflicting workflow signals.\n\n"
        f"- selected_request_type: {classification.request_type}\n"
        f"- confidence: {classification.confidence}\n"
        f"- matched_request_types: {', '.join(classification.matched_request_types)}\n"
        "- It may combine question/confirmation, design, implementation, test, commit, or transition intent.\n"
        "- Do not create, modify, or delete files.\n"
        "- Do not update .flh/runtime/STATE.md.\n"
        "- Ask the user to clarify the single intended action before proceeding.\n"
        "- If the prompt mixes a question with an execution command, ask whether the user wants explanation only or wants Codex to perform the action."
    )


def medium_confidence_additional_prompt(classification: RequestClassification) -> str:
    return (
        "[Harness Guard]\n"
        "This request was classified by an alias pattern.\n\n"
        f"- request_type: {classification.request_type}\n"
        f"- confidence: {classification.confidence}\n"
        "- Proceed under this workflow interpretation unless the user corrects it."
    )


def design_selection_additional_prompt(prefix: str | None = None) -> str:
    lines = ["[Harness Guard]"]
    if prefix:
        lines.extend(["", prefix])
    lines.extend(
        [
            "",
            "FRONTEND_DESIGN uses docs/DESIGN.md as the design guideline artifact.",
            "",
            "Before proceeding, ask the user to choose one:",
            "1. Import an existing external DESIGN.md into docs/DESIGN.md.",
            "2. Create docs/DESIGN.md together in this workflow.",
            "",
            "If the user imports an external DESIGN.md, record approval in .flh/runtime/STATE.md:",
            "approvals.design.approved: true",
            "",
            "Do not treat docs/FRONTEND.md as the workflow artifact.",
        ]
    )
    return "\n".join(lines)


def block_reason(result: HookResult) -> str:
    reason = result.reason or "Harness blocked this request."
    lines = [
        "[Harness Guard: BLOCKED]",
        "",
        "Codex did not start the requested work because the project workflow guard blocked this prompt.",
        "",
        "Reason:",
        f"- {reason}",
        "",
        "Request:",
        f"- request_type: {result.request_type}",
        f"- confidence: {result.confidence}",
        f"- current_state: {result.current_state}",
    ]
    if result.target_state:
        lines.append(f"- target_state: {result.target_state}")
    if result.missing:
        lines.extend(["", "Missing requirements:"])
        lines.extend(f"- {item}" for item in result.missing)

    lines.extend(
        [
            "",
            "Next action:",
            "- Finish the current workflow step first, or ask for current status/next work.",
        ]
    )
    return "\n".join(lines)


def format_codex_output(result: HookResult) -> dict[str, Any]:
    """Return the JSON shape Codex expects from a UserPromptSubmit hook."""

    if result.action == "block":
        return {
            "decision": "block",
            "reason": block_reason(result),
        }

    if result.additional_prompt:
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": result.additional_prompt,
            }
        }

    if result.updated_state:
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": (
                    "[Harness Guard]\n"
                    f"STATE.md was updated from {result.current_state} to {result.updated_state}.\n"
                    f"request_type={result.request_type}\n"
                    f"confidence={result.confidence}"
                ),
            }
        }

    return {}


def handle_prompt(prompt: str) -> HookResult:
    state_data = load_state()
    flow = load_yaml(FLOW_PATH)
    docs_spec = load_yaml(DOCS_SPEC_PATH)
    guards = load_yaml(TRANSITION_GUARDS_PATH)

    current_state = state_data.get("current_state")
    if not current_state:
        return HookResult(
            action="block",
            request_type="UNKNOWN",
            confidence="unknown",
            current_state=None,
            reason="STATE.md does not define current_state.",
        )

    classification = classify_prompt(prompt)
    request_type = classification.request_type

    if request_type == "QUESTION_OR_CONFIRMATION_REQUEST":
        return HookResult(
            action="allow",
            request_type=request_type,
            confidence=classification.confidence,
            current_state=current_state,
            reason="Question or confirmation requests are allowed without workflow action.",
            additional_prompt=question_or_confirmation_additional_prompt(),
        )

    if request_type == "DOCUMENTATION_REQUEST":
        if is_merge_command(prompt):
            return HookResult(
                action="block",
                request_type=request_type,
                confidence=classification.confidence,
                current_state=current_state,
                reason="Merge is not allowed in /d documentation mode.",
            )

        return HookResult(
            action="allow",
            request_type=request_type,
            confidence=classification.confidence,
            current_state=current_state,
            reason="/d documentation mode allows documentation and harness-maintenance work.",
            additional_prompt=documentation_additional_prompt(),
        )

    if request_type == "UNKNOWN":
        return HookResult(
            action="allow",
            request_type=request_type,
            confidence=classification.confidence,
            current_state=current_state,
            reason="UNKNOWN requests are allowed only for non-mutating explanation or analysis.",
            additional_prompt=unknown_additional_prompt(),
        )

    if classification.confidence == "low":
        return HookResult(
            action="allow",
            request_type=request_type,
            confidence=classification.confidence,
            current_state=current_state,
            reason="Ambiguous request type. User clarification is required before workflow action.",
            additional_prompt=low_confidence_additional_prompt(classification),
        )

    if is_allowed(flow, current_state, request_type):
        additional_prompt = None
        if classification.confidence == "medium":
            additional_prompt = medium_confidence_additional_prompt(classification)
        if current_state == "FRONTEND_DESIGN" and request_type == "FRONTEND_DESIGN_REQUEST":
            additional_prompt = design_selection_additional_prompt()

        return HookResult(
            action="allow",
            request_type=request_type,
            confidence=classification.confidence,
            current_state=current_state,
            reason="Request type is allowed in current state.",
            additional_prompt=additional_prompt,
        )

    target_state = find_target_state(flow, request_type)
    if not target_state:
        return HookResult(
            action="block",
            request_type=request_type,
            confidence=classification.confidence,
            current_state=current_state,
            reason="No workflow state allows this request type.",
        )

    path = find_state_path(flow, current_state, target_state)
    if not path:
        return HookResult(
            action="block",
            request_type=request_type,
            confidence=classification.confidence,
            current_state=current_state,
            target_state=target_state,
            reason="No transition path exists from current state to target state.",
        )

    ok, missing = check_transition_guards(path, docs_spec, guards, state_data)
    if not ok:
        return HookResult(
            action="block",
            request_type=request_type,
            confidence=classification.confidence,
            current_state=current_state,
            target_state=target_state,
            reason="Transition guard check failed.",
            missing=missing,
        )

    completed = list(state_data.get("completed_states") or [])
    for completed_state in path[:-1]:
        if completed_state not in completed:
            completed.append(completed_state)

    state_data["current_state"] = target_state
    state_data["completed_states"] = completed
    state_data["last_transition"] = f"{current_state} -> {target_state}"
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_state(state_data)

    additional_prompt = None
    if target_state == "FRONTEND_DESIGN":
        additional_prompt = design_selection_additional_prompt(
            f"STATE.md was updated from {current_state} to {target_state}."
        )

    return HookResult(
        action="allow",
        request_type=request_type,
        confidence=classification.confidence,
        current_state=current_state,
        target_state=target_state,
        updated_state=target_state,
        reason="Transition guard check passed and STATE.md was updated.",
        additional_prompt=additional_prompt,
    )


def main() -> int:
    prompt = read_prompt()
    if not prompt:
        result = HookResult(
            action="block",
            request_type="UNKNOWN",
            confidence="unknown",
            current_state=None,
            reason="No user prompt was provided.",
        )
        print(json.dumps(format_codex_output(result), ensure_ascii=False, indent=2))
        return ALLOW_EXIT_CODE

    try:
        result = handle_prompt(prompt)
    except Exception as exc:  # Keep hook failures explicit for the caller.
        result = HookResult(
            action="block",
            request_type="UNKNOWN",
            confidence="unknown",
            current_state=None,
            reason=f"Hook error: {exc}",
        )
        print(json.dumps(format_codex_output(result), ensure_ascii=False, indent=2))
        return ERROR_EXIT_CODE

    print(json.dumps(format_codex_output(result), ensure_ascii=False, indent=2))
    return ALLOW_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
