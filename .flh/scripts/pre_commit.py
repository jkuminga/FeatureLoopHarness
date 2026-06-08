#!/usr/bin/env python3
"""Source-code pre-commit guard for the Feature Loop Harness."""

from __future__ import annotations

import fnmatch
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".flh/runtime/STATE.md"
SOURCE_LAYOUT_PATH = ROOT / "docs/source-layout.yml"

SUPPORTED_PACKAGE_MANAGERS = {"npm", "pnpm", "yarn", "bun"}
IMPLEMENTATION_BRANCH_PREFIXES = ("feat/", "fix/", "refactor/")
SOURCE_CANDIDATE_PREFIXES = ("app/", "apps/", "packages/")

DOC_HARNESS_PATTERNS = (
    "docs/**",
    ".flh/**",
    ".codex/**",
    "AGENTS.md",
    "README.md",
    "tests/hooks/**",
    ".husky/**",
    "package.json",
    "package-lock.json",
)

ROOT_SCAFFOLD_PATTERNS = (
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "yarn.lock",
    "tsconfig.base.json",
    "eslint.config.*",
    "prettier.config.*",
    ".prettierrc*",
    ".prettierignore",
    ".gitignore",
)

SOURCE_SCAFFOLD_ALLOW_PATTERNS = (
    "package.json",
    "package-lock.json",
    "tsconfig*.json",
    "vite.config.*",
    "vitest.config.*",
    "eslint.config.*",
    "src/index.*",
    "src/main.*",
    "src/app.*",
    ".gitkeep",
)

SOURCE_SCAFFOLD_BLOCK_PATTERNS = (
    "src/features/**",
    "src/routes/**",
    "src/pages/**",
    "src/components/**",
    "*.test.*",
    "*.spec.*",
    "tests/**",
)

DB_BASELINE_ALLOW_PATTERNS = (
    "prisma/schema.prisma",
    "prisma/migrations/**",
    "package.json",
)


class PreCommitBlock(Exception):
    """Raised when the commit should be blocked."""


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise PreCommitBlock(result.stderr.strip() or "git 명령 실행에 실패했습니다.")
    return result.stdout.strip()


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


def parse_yaml_subset(text: str) -> dict[str, Any]:
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
            next_value = [] if lookahead.strip().startswith("- ") else {}
            break

        if not isinstance(parent, dict):
            raise ValueError(f"Invalid nested mapping at line {index + 1}: {raw_line}")
        parent[key] = next_value
        stack.append((indent, next_value))

    return root


def parse_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return parse_yaml_subset(parts[1])


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return parse_yaml_subset(path.read_text(encoding="utf-8"))


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    return parse_frontmatter(STATE_PATH.read_text(encoding="utf-8"))


def load_committed_state() -> dict[str, Any]:
    result = subprocess.run(
        ["git", "show", "HEAD:.flh/runtime/STATE.md"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return {}
    return parse_frontmatter(result.stdout)


def normalize_path(path: str) -> str:
    return path.strip().strip("/")


def normalize_package_manager(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text.split("@", 1)[0]


def is_todo_value(value: Any) -> bool:
    return "{{TODO" in str(value) or "TODO" in str(value)


def path_matches(path: str, pattern: str) -> bool:
    path = normalize_path(path)
    pattern = normalize_path(pattern)
    return fnmatch.fnmatch(path, pattern)


def path_is_inside(path: str, root: str) -> bool:
    path = normalize_path(path)
    root = normalize_path(root)
    return path == root or path.startswith(f"{root}/")


def source_roots(source_layout: dict[str, Any]) -> list[dict[str, Any]]:
    roots = source_layout.get("source_roots")
    if not isinstance(roots, dict):
        return []

    result: list[dict[str, Any]] = []
    for key, config in roots.items():
        if not isinstance(config, dict):
            continue
        path = config.get("path")
        if not path or is_todo_value(path):
            continue
        result.append(
            {
                "key": str(key),
                "path": normalize_path(str(path)),
                "package": config.get("package") is True,
            }
        )
    return result


def is_doc_harness_file(path: str) -> bool:
    return any(path_matches(path, pattern) for pattern in DOC_HARNESS_PATTERNS)


def is_source_candidate(path: str, roots: list[dict[str, Any]]) -> bool:
    normalized = normalize_path(path)
    if normalized.startswith(SOURCE_CANDIDATE_PREFIXES):
        return True
    return any(path_is_inside(normalized, str(root["path"])) for root in roots)


def unknown_files(staged_files: list[str], roots: list[dict[str, Any]]) -> list[str]:
    return [
        path
        for path in staged_files
        if not is_doc_harness_file(path) and not is_source_candidate(path, roots)
    ]


def match_source_root(path: str, roots: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [root for root in roots if path_is_inside(path, str(root["path"]))]
    if not matches:
        return None
    return max(matches, key=lambda root: len(str(root["path"])))


def relative_to_source_root(path: str, source_root: dict[str, Any]) -> str:
    root_path = normalize_path(str(source_root["path"]))
    normalized = normalize_path(path)
    if normalized == root_path:
        return ""
    return normalized[len(root_path) + 1 :]


def branch_kind(branch: str) -> str:
    if branch in {"main", "master"}:
        return "main"
    if branch.startswith(IMPLEMENTATION_BRANCH_PREFIXES):
        return "implementation"
    return "other"


def feature_directory_exists(kind: str) -> bool:
    base = ROOT / f"docs/features/{kind}"
    if not base.exists():
        return False
    return any(path.is_dir() for path in base.iterdir())


def source_layout_completed(source_layout: dict[str, Any]) -> bool:
    return source_layout.get("status") == "completed"


def package_manager_from_layout(source_layout: dict[str, Any]) -> str:
    project = source_layout.get("project")
    if not isinstance(project, dict):
        return ""
    return normalize_package_manager(project.get("package_manager"))


def package_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreCommitBlock(f"{path.relative_to(ROOT)} 파일의 JSON 문법이 올바르지 않습니다: {exc}")


def package_manager_conflicts(package_json_path: Path, expected_pm: str) -> str | None:
    data = package_json(package_json_path)
    actual = normalize_package_manager(data.get("packageManager"))
    if actual and actual != expected_pm:
        return actual
    return None


def script_command(pm: str, package_path: str, script_name: str) -> list[str]:
    if pm == "npm":
        return ["npm", "--prefix", package_path, "run", script_name]
    if pm == "pnpm":
        return ["pnpm", "-C", package_path, "run", script_name]
    if pm == "yarn":
        return ["yarn", "--cwd", package_path, "run", script_name]
    if pm == "bun":
        return ["bun", "--cwd", package_path, "run", script_name]
    raise PreCommitBlock(f"지원하지 않는 package manager입니다: {pm}")


def lint_staged_command(pm: str) -> list[str]:
    if pm == "npm":
        return ["npx", "lint-staged"]
    if pm == "pnpm":
        return ["pnpm", "exec", "lint-staged"]
    if pm == "yarn":
        return ["yarn", "lint-staged"]
    if pm == "bun":
        return ["bunx", "lint-staged"]
    raise PreCommitBlock(f"지원하지 않는 package manager입니다: {pm}")


def run_command(command: list[str]) -> None:
    print(f"🔎 실행 명령: {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise PreCommitBlock(f"명령이 실패했습니다: {' '.join(command)}")


def root_scaffold_extra_files(source_layout: dict[str, Any]) -> set[str]:
    project = source_layout.get("project")
    if not isinstance(project, dict):
        return set()
    values = project.get("scaffold_extra_root_files")
    if not isinstance(values, list):
        return set()
    return {normalize_path(str(value)) for value in values}


def is_root_scaffold_file(path: str, source_layout: dict[str, Any]) -> bool:
    normalized = normalize_path(path)
    if "/" in normalized:
        return False
    if any(path_matches(normalized, pattern) for pattern in ROOT_SCAFFOLD_PATTERNS):
        return True
    return normalized in root_scaffold_extra_files(source_layout)


def source_scaffold_allowed(path: str, source_root: dict[str, Any]) -> bool:
    relative = relative_to_source_root(path, source_root)
    if any(path_matches(relative, pattern) for pattern in SOURCE_SCAFFOLD_BLOCK_PATTERNS):
        return False
    return any(path_matches(relative, pattern) for pattern in SOURCE_SCAFFOLD_ALLOW_PATTERNS)


def has_source_scaffold_approval(state: dict[str, Any]) -> bool:
    approvals = state.get("approvals")
    if not isinstance(approvals, dict):
        return False
    source_scaffold = approvals.get("source_scaffold")
    if not isinstance(source_scaffold, dict):
        return False
    return source_scaffold.get("created") is True


def has_database_baseline_approval(state: dict[str, Any]) -> bool:
    approvals = state.get("approvals")
    if not isinstance(approvals, dict):
        return False
    database_baseline = approvals.get("database_baseline")
    if not isinstance(database_baseline, dict):
        return False
    return database_baseline.get("verified") is True


def scaffold_exception_allowed(
    staged_files: list[str],
    source_files: list[tuple[str, dict[str, Any]]],
    source_layout: dict[str, Any],
    current_state: dict[str, Any],
    committed_state: dict[str, Any],
) -> tuple[bool, str]:
    if current_state.get("current_state") != "FEATURE_IMPLEMENTATION":
        return False, "현재 상태가 FEATURE_IMPLEMENTATION이 아닙니다."
    if has_source_scaffold_approval(committed_state):
        return False, "이전 커밋에 이미 source scaffold approval이 기록되어 있습니다."
    if not has_source_scaffold_approval(current_state):
        return False, "현재 STATE.md에 source scaffold approval 기록이 없습니다."
    if ".flh/runtime/STATE.md" not in staged_files:
        return False, "source scaffold approval을 기록한 .flh/runtime/STATE.md가 staged되지 않았습니다."

    source_file_set = {path for path, _ in source_files}
    for path, root in source_files:
        if not source_scaffold_allowed(path, root):
            return False, f"scaffold 허용 범위를 벗어난 source file입니다: {path}"

    for path in staged_files:
        if path in source_file_set:
            continue
        if path == ".flh/runtime/STATE.md":
            continue
        if is_root_scaffold_file(path, source_layout):
            continue
        return False, f"scaffold 예외에 허용되지 않는 파일입니다: {path}"

    return True, "scaffold baseline exception 조건을 만족했습니다."


def db_baseline_allowed(path: str, source_root: dict[str, Any]) -> bool:
    relative = relative_to_source_root(path, source_root)
    return any(path_matches(relative, pattern) for pattern in DB_BASELINE_ALLOW_PATTERNS)


def database_baseline_exception_allowed(
    staged_files: list[str],
    source_files: list[tuple[str, dict[str, Any]]],
    source_layout: dict[str, Any],
    current_state: dict[str, Any],
    committed_state: dict[str, Any],
) -> tuple[bool, str]:
    if current_state.get("current_state") != "FEATURE_IMPLEMENTATION":
        return False, "현재 상태가 FEATURE_IMPLEMENTATION이 아닙니다."
    if not has_source_scaffold_approval(current_state):
        return False, "source scaffold approval이 아직 기록되어 있지 않습니다."
    if has_database_baseline_approval(committed_state):
        return False, "이전 커밋에 이미 database baseline approval이 기록되어 있습니다."
    if not has_database_baseline_approval(current_state):
        return False, "현재 STATE.md에 database baseline approval 기록이 없습니다."
    if ".flh/runtime/STATE.md" not in staged_files:
        return False, "database baseline approval을 기록한 .flh/runtime/STATE.md가 staged되지 않았습니다."

    source_file_set = {path for path, _ in source_files}
    for path, root in source_files:
        if not db_baseline_allowed(path, root):
            return False, f"database baseline 예외에 허용되지 않는 source file입니다: {path}"

    for path in staged_files:
        if path in source_file_set:
            continue
        if path == ".flh/runtime/STATE.md":
            continue
        if is_root_scaffold_file(path, source_layout):
            continue
        return False, f"database baseline 예외에 허용되지 않는 파일입니다: {path}"

    return True, "database baseline exception 조건을 만족했습니다."


def block(message: str) -> None:
    raise PreCommitBlock(message)


def print_block(message: str, details: list[str] | None = None) -> None:
    print("\n🚫 커밋 차단\n")
    print(message)
    if details:
        print()
        for detail in details:
            print(f"- {detail}")


def main() -> int:
    try:
        branch = run_git(["branch", "--show-current"]) or "(detached)"
        staged_files = [
            line
            for line in run_git(["diff", "--cached", "--name-only"]).splitlines()
            if line.strip()
        ]

        print(f"🔎 현재 브랜치: {branch}")
        if not staged_files:
            print("✅ staged file이 없어 pre-commit 검사를 건너뜁니다.")
            return 0

        source_layout = load_yaml(SOURCE_LAYOUT_PATH)
        candidate_roots = source_roots(source_layout)
        source_candidates = [
            path for path in staged_files if is_source_candidate(path, candidate_roots)
        ]
        unknown = unknown_files(staged_files, candidate_roots)

        if not source_candidates:
            if unknown:
                print("⚠️ unknown file이 staged되어 있습니다.")
                print("source file 변경이 함께 없으므로 commit을 차단하지 않습니다.")
                for path in unknown:
                    print(f"- {path}")
            print("⏭️ source file 변경이 없어 source package checks와 lint-staged를 건너뜁니다.")
            return 0

        if unknown:
            block(
                "source file과 unknown file이 함께 staged되어 있습니다.\n\n"
                "unknown file은 source/layout 또는 docs/harness 정책에 속하지 않아 함께 커밋할 수 없습니다.\n\n"
                "unknown file:\n"
                + "\n".join(f"- {path}" for path in unknown)
            )

        if not source_layout_completed(source_layout):
            block(
                "source file 변경이 감지됐지만 docs/source-layout.yml이 completed 상태가 아닙니다.\n\n"
                "해결 방법:\n"
                "docs/source-layout.yml을 완성하고 status를 completed로 변경한 뒤 다시 커밋하세요."
            )

        roots = source_roots(source_layout)
        source_files: list[tuple[str, dict[str, Any]]] = []
        for path in staged_files:
            root = match_source_root(path, roots)
            if root is not None:
                source_files.append((path, root))

        if not source_files:
            block(
                "source 후보 파일은 감지됐지만 completed source-layout 기준 source root에 속하지 않습니다.\n\n"
                "해결 방법:\n"
                "docs/source-layout.yml의 source_roots.*.path를 확인하세요."
            )

        kind = branch_kind(branch)
        if kind == "main":
            state = load_state()
            committed_state = load_committed_state()
            allowed, reason = scaffold_exception_allowed(
                staged_files, source_files, source_layout, state, committed_state
            )
            if allowed:
                print(f"✅ {reason}")
                print("⏭️ scaffold baseline commit이므로 package checks와 lint-staged를 건너뜁니다.")
                return 0
            db_allowed, db_reason = database_baseline_exception_allowed(
                staged_files, source_files, source_layout, state, committed_state
            )
            if db_allowed:
                print(f"✅ {db_reason}")
                print("⏭️ database baseline commit이므로 package checks와 lint-staged를 건너뜁니다.")
                return 0
            block(
                "main/master 브랜치에서는 실제 source file을 직접 커밋할 수 없습니다.\n\n"
                f"scaffold 예외 미적용 사유: {reason}\n"
                f"database baseline 예외 미적용 사유: {db_reason}\n\n"
                "해결 방법:\n"
                "feat/*, fix/*, refactor/* 브랜치에서 작업하거나, baseline 예외 조건을 확인하세요."
            )

        if kind == "other":
            block(
                f"현재 브랜치에서 source file 변경을 커밋할 수 없습니다: {branch}\n\n"
                "허용 브랜치:\n"
                "- feat/*\n"
                "- fix/*\n"
                "- refactor/*\n\n"
                "문서/하네스 파일만 변경한 커밋은 브랜치 prefix와 관계없이 허용됩니다."
            )

        if not feature_directory_exists("active") and not feature_directory_exists("review"):
            block(
                "source file 변경이 있지만 active 또는 review 기능 디렉토리가 없습니다.\n\n"
                "해결 방법:\n"
                "docs/features/active/ 또는 docs/features/review/에 대상 기능 디렉토리가 있는지 확인하세요."
            )

        affected: dict[str, dict[str, Any]] = {}
        for _path, root in source_files:
            if root.get("package") is True:
                affected[str(root["path"])] = root

        pm = package_manager_from_layout(source_layout)
        if pm not in SUPPORTED_PACKAGE_MANAGERS:
            block(
                f"지원하지 않는 package manager입니다: {pm or '(empty)'}\n\n"
                "docs/source-layout.yml의 project.package_manager 값을 확인하세요."
            )

        if shutil.which(pm) is None:
            block(
                f"package manager 실행 파일을 찾을 수 없습니다: {pm}\n\n"
                "해결 방법:\n"
                f"{pm}을 설치하거나 docs/source-layout.yml의 project.package_manager 값을 수정하세요."
            )

        root_pm_conflict = package_manager_conflicts(ROOT / "package.json", pm)
        if root_pm_conflict:
            block(
                "package manager 설정이 서로 다릅니다.\n\n"
                f"docs/source-layout.yml: {pm}\n"
                f"package.json: {root_pm_conflict}"
            )

        if affected:
            print("🔎 affected package:")
            for package_path in sorted(affected):
                print(f"- {package_path}")
        else:
            print("⏭️ package: true source root 변경이 없어 package script 검사를 건너뜁니다.")

        for package_path in sorted(affected):
            package_dir = ROOT / package_path
            package_json_path = package_dir / "package.json"
            if not package_json_path.exists():
                block(
                    f"{package_path}는 package로 표시되어 있지만 package.json이 없습니다.\n\n"
                    "해결 방법:\n"
                    f"{package_path}/package.json을 생성하거나, package가 아닌 디렉토리라면 "
                    "docs/source-layout.yml에서 package 값을 false로 변경하세요."
                )

            package_pm_conflict = package_manager_conflicts(package_json_path, pm)
            if package_pm_conflict:
                block(
                    "package manager 설정이 서로 다릅니다.\n\n"
                    f"docs/source-layout.yml: {pm}\n"
                    f"{package_path}/package.json: {package_pm_conflict}"
                )

            data = package_json(package_json_path)
            scripts = data.get("scripts") if isinstance(data, dict) else {}
            scripts = scripts if isinstance(scripts, dict) else {}

            print(f"\n🔎 {package_path} 검사 시작")
            for script_name in ("lint", "typecheck", "test"):
                if script_name not in scripts:
                    print(f"⏭️ {script_name} script 없음 - 스킵")
                    continue
                run_command(script_command(pm, package_path, script_name))
                print(f"✅ {script_name} 통과")

        run_command(lint_staged_command(pm))
        print("\n✅ pre-commit 검사 완료")
        return 0

    except PreCommitBlock as exc:
        print_block(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
