import contextlib
import io
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / ".flh/scripts/pre_commit.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pre_commit", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PreCommitScriptTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def make_temp_root(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        root = Path(tmpdir.name)
        self.module.ROOT = root
        self.module.STATE_PATH = root / ".flh/runtime/STATE.md"
        self.module.SOURCE_LAYOUT_PATH = root / "docs/source-layout.yml"
        return root

    def write_source_layout(
        self,
        root,
        *,
        status="completed",
        package_manager="npm",
        package=True,
    ):
        package_value = "true" if package else "false"
        target = root / "docs/source-layout.yml"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "\n".join(
                [
                    "version: 1",
                    f"status: {status}",
                    "project:",
                    f"  package_manager: {package_manager}",
                    "source_roots:",
                    "  backend:",
                    "    path: app/be",
                    f"    package: {package_value}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def write_package_json(self, root, path, data):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data), encoding="utf-8")

    def stub_git(self, branch, staged_files):
        def fake_run_git(args):
            if args == ["branch", "--show-current"]:
                return branch
            if args == ["diff", "--cached", "--name-only"]:
                return "\n".join(staged_files)
            raise AssertionError(f"Unexpected git args: {args}")

        self.module.run_git = fake_run_git

    def stub_package_manager_available(self):
        self.module.shutil = type(
            "FakeShutil",
            (),
            {"which": staticmethod(lambda _pm: "/usr/bin/tool")},
        )

    def run_main(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.module.main()
        return result, output.getvalue()

    def test_package_manager_normalizes_versions(self):
        self.assertEqual(self.module.normalize_package_manager("pnpm@9.0.0"), "pnpm")
        self.assertEqual(self.module.normalize_package_manager("npm@10.0.0"), "npm")
        self.assertEqual(self.module.normalize_package_manager("yarn"), "yarn")

    def test_branch_kind_classifies_source_commit_branches(self):
        scenarios = [
            ("main", "main"),
            ("master", "main"),
            ("feat/login", "implementation"),
            ("fix/button", "implementation"),
            ("refactor/core", "implementation"),
            ("chore/docs", "other"),
        ]

        for branch, expected in scenarios:
            with self.subTest(branch=branch):
                self.assertEqual(self.module.branch_kind(branch), expected)

    def test_main_blocks_source_changes_on_other_branch(self):
        root = self.make_temp_root()
        self.write_source_layout(root)
        self.stub_git("chore/source-edit", ["app/be/src/index.ts"])

        result, _output = self.run_main()

        self.assertEqual(result, 1)

    def test_main_allows_docs_harness_only_without_running_commands(self):
        self.make_temp_root()
        self.stub_git(
            "chore/docs",
            [
                "README.md",
                "docs/MVP.md",
                ".flh/runtime/STATE.md",
                "tests/hooks/test_pre_commit.py",
            ],
        )
        commands = []
        self.module.run_command = commands.append

        result, _output = self.run_main()

        self.assertEqual(result, 0)
        self.assertEqual(commands, [])

    def test_source_root_file_wins_over_root_file_name(self):
        source_layout = {
            "source_roots": {
                "backend": {
                    "path": "app/be",
                    "package": True,
                }
            }
        }
        roots = self.module.source_roots(source_layout)

        self.assertTrue(self.module.is_source_candidate("app/be/package.json", roots))
        self.assertEqual(
            self.module.match_source_root("app/be/package.json", roots)["path"],
            "app/be",
        )
        self.assertTrue(self.module.is_doc_harness_file("package.json"))

    def test_nested_source_root_prefers_longest_path(self):
        source_layout = {
            "source_roots": {
                "app_root": {
                    "path": "app",
                    "package": False,
                },
                "backend": {
                    "path": "app/be",
                    "package": True,
                },
            }
        }
        roots = self.module.source_roots(source_layout)

        matched = self.module.match_source_root("app/be/src/user.ts", roots)

        self.assertEqual(matched["key"], "backend")
        self.assertEqual(matched["path"], "app/be")

    def test_feature_directory_exists_requires_child_directory(self):
        root = self.make_temp_root()
        active = root / "docs/features/active"
        active.mkdir(parents=True)

        self.assertFalse(self.module.feature_directory_exists("active"))

        (active / "FEAT-001-login").mkdir()

        self.assertTrue(self.module.feature_directory_exists("active"))
        self.assertFalse(self.module.feature_directory_exists("review"))

    def test_main_blocks_source_changes_without_active_or_review_feature(self):
        root = self.make_temp_root()
        self.write_source_layout(root)
        self.stub_git("feat/login", ["app/be/src/index.ts"])
        self.module.feature_directory_exists = lambda _kind: False
        commands = []
        self.module.run_command = commands.append

        result, _output = self.run_main()

        self.assertEqual(result, 1)
        self.assertEqual(commands, [])

    def test_main_accepts_review_feature_directory_for_source_changes(self):
        root = self.make_temp_root()
        self.write_source_layout(root, package=False)
        self.stub_git("fix/review-patch", ["app/be/src/index.ts"])
        self.stub_package_manager_available()
        self.module.feature_directory_exists = lambda kind: kind == "review"
        commands = []
        self.module.run_command = commands.append

        result, _output = self.run_main()

        self.assertEqual(result, 0)
        self.assertEqual(commands, [["npx", "lint-staged"]])

    def test_unknown_files_excludes_source_and_harness_files(self):
        source_layout = {
            "source_roots": {
                "backend": {
                    "path": "app/be",
                    "package": True,
                }
            }
        }
        roots = self.module.source_roots(source_layout)

        unknown = self.module.unknown_files(
            [
                "docs/ARCHITECTURE.md",
                ".flh/runtime/STATE.md",
                "app/be/src/index.ts",
                "HARNESS_MANUAL.md",
            ],
            roots,
        )

        self.assertEqual(unknown, ["HARNESS_MANUAL.md"])

    def test_main_blocks_source_when_source_layout_is_not_completed(self):
        root = self.make_temp_root()
        self.write_source_layout(root, status="draft")
        self.stub_git("feat/login", ["app/be/src/index.ts"])

        result, _output = self.run_main()

        self.assertEqual(result, 1)

    def test_main_blocks_source_candidate_outside_configured_roots(self):
        root = self.make_temp_root()
        self.write_source_layout(root)
        self.stub_git("feat/login", ["app/unknown/src/index.ts"])

        result, _output = self.run_main()

        self.assertEqual(result, 1)

    def test_main_blocks_root_package_manager_conflict(self):
        root = self.make_temp_root()
        self.write_source_layout(root, package_manager="npm")
        self.write_package_json(root, "package.json", {"packageManager": "pnpm@9.0.0"})
        self.stub_git("feat/login", ["app/be/src/index.ts"])
        self.stub_package_manager_available()
        self.module.feature_directory_exists = lambda kind: kind == "active"

        result, _output = self.run_main()

        self.assertEqual(result, 1)

    def test_main_runs_affected_package_scripts_and_lint_staged(self):
        root = self.make_temp_root()
        self.write_source_layout(root)
        self.write_package_json(
            root,
            "app/be/package.json",
            {
                "packageManager": "npm@10.0.0",
                "scripts": {
                    "lint": "eslint .",
                    "typecheck": "tsc --noEmit",
                    "test": "vitest run",
                },
            },
        )
        self.stub_git("feat/login", ["app/be/src/index.ts"])
        self.stub_package_manager_available()
        self.module.feature_directory_exists = lambda kind: kind == "active"
        commands = []
        self.module.run_command = commands.append

        result, _output = self.run_main()

        self.assertEqual(result, 0)
        self.assertEqual(
            commands,
            [
                ["npm", "--prefix", "app/be", "run", "lint"],
                ["npm", "--prefix", "app/be", "run", "typecheck"],
                ["npm", "--prefix", "app/be", "run", "test"],
                ["npx", "lint-staged"],
            ],
        )

    def test_state_frontmatter_ignores_body_approval_example(self):
        text = "\n".join(
            [
                "---",
                "current_state: FEATURE_IMPLEMENTATION",
                "approvals: {}",
                "---",
                "",
                "```yaml",
                "approvals:",
                "  source_scaffold:",
                "    created: true",
                "```",
            ]
        )

        frontmatter = self.module.parse_frontmatter(text)

        self.assertEqual(frontmatter["current_state"], "FEATURE_IMPLEMENTATION")
        self.assertFalse(self.module.has_source_scaffold_approval(frontmatter))

    def test_scaffold_exception_allows_root_extra_files_from_source_layout(self):
        source_layout = {
            "project": {
                "scaffold_extra_root_files": ["turbo.json"],
            },
            "source_roots": {
                "backend": {
                    "path": "app/be",
                    "package": True,
                }
            },
        }
        state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                }
            },
        }
        committed_state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {},
        }
        roots = self.module.source_roots(source_layout)
        source_root = self.module.match_source_root("app/be/src/index.ts", roots)

        allowed, reason = self.module.scaffold_exception_allowed(
            ["app/be/src/index.ts", "turbo.json", ".flh/runtime/STATE.md"],
            [("app/be/src/index.ts", source_root)],
            source_layout,
            state,
            committed_state,
        )

        self.assertTrue(allowed, reason)

    def test_scaffold_exception_blocks_feature_code(self):
        source_layout = {
            "project": {
                "scaffold_extra_root_files": [],
            },
            "source_roots": {
                "backend": {
                    "path": "app/be",
                    "package": True,
                }
            },
        }
        state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                }
            },
        }
        committed_state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {},
        }
        roots = self.module.source_roots(source_layout)
        source_root = self.module.match_source_root("app/be/src/features/login.ts", roots)

        allowed, _reason = self.module.scaffold_exception_allowed(
            ["app/be/src/features/login.ts"],
            [("app/be/src/features/login.ts", source_root)],
            source_layout,
            state,
            committed_state,
        )

        self.assertFalse(allowed)

    def test_scaffold_exception_requires_current_state_approval(self):
        source_layout = {
            "project": {
                "scaffold_extra_root_files": [],
            },
            "source_roots": {
                "backend": {
                    "path": "app/be",
                    "package": True,
                }
            },
        }
        state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {},
        }
        committed_state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {},
        }
        roots = self.module.source_roots(source_layout)
        source_root = self.module.match_source_root("app/be/src/index.ts", roots)

        allowed, reason = self.module.scaffold_exception_allowed(
            ["app/be/src/index.ts"],
            [("app/be/src/index.ts", source_root)],
            source_layout,
            state,
            committed_state,
        )

        self.assertFalse(allowed)
        self.assertIn("approval", reason)

    def test_main_allows_scaffold_baseline_exception_on_main(self):
        root = self.make_temp_root()
        self.write_source_layout(root)
        self.stub_git(
            "main",
            ["app/be/src/index.ts", ".flh/runtime/STATE.md"],
        )
        self.module.load_state = lambda: {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                }
            },
        }
        self.module.load_committed_state = lambda: {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {},
        }
        commands = []
        self.module.run_command = commands.append

        result, _output = self.run_main()

        self.assertEqual(result, 0)
        self.assertEqual(commands, [])

    def test_database_baseline_exception_allows_prisma_baseline_files(self):
        source_layout = {
            "project": {
                "scaffold_extra_root_files": [],
            },
            "source_roots": {
                "backend": {
                    "path": "app/be",
                    "package": True,
                }
            },
        }
        state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                },
                "database_baseline": {
                    "required": True,
                    "verified": True,
                },
            },
        }
        committed_state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                },
            },
        }
        roots = self.module.source_roots(source_layout)
        source_root = self.module.match_source_root(
            "app/be/prisma/schema.prisma",
            roots,
        )

        allowed, reason = self.module.database_baseline_exception_allowed(
            ["app/be/prisma/schema.prisma", ".flh/runtime/STATE.md"],
            [("app/be/prisma/schema.prisma", source_root)],
            source_layout,
            state,
            committed_state,
        )

        self.assertTrue(allowed, reason)

    def test_main_allows_database_baseline_exception_on_main(self):
        root = self.make_temp_root()
        self.write_source_layout(root)
        self.stub_git(
            "main",
            ["app/be/prisma/schema.prisma", ".flh/runtime/STATE.md"],
        )
        self.module.load_state = lambda: {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                },
                "database_baseline": {
                    "required": True,
                    "verified": True,
                },
            },
        }
        self.module.load_committed_state = lambda: {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                },
            },
        }
        commands = []
        self.module.run_command = commands.append

        result, _output = self.run_main()

        self.assertEqual(result, 0)
        self.assertEqual(commands, [])

    def test_database_baseline_approval_allows_no_database_skip(self):
        state = {
            "approvals": {
                "database_baseline": {
                    "required": False,
                    "skipped": True,
                }
            }
        }

        self.assertTrue(self.module.has_database_baseline_approval(state))

    def test_database_baseline_approval_rejects_legacy_verified_without_required(self):
        state = {
            "approvals": {
                "database_baseline": {
                    "verified": True,
                }
            }
        }

        self.assertFalse(self.module.has_database_baseline_approval(state))

    def test_database_baseline_exception_rejects_no_database_skip_with_source_files(self):
        source_layout = {
            "project": {
                "scaffold_extra_root_files": [],
            },
            "source_roots": {
                "backend": {
                    "path": "app/be",
                    "package": True,
                }
            },
        }
        state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                },
                "database_baseline": {
                    "required": False,
                    "skipped": True,
                },
            },
        }
        committed_state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                },
            },
        }
        roots = self.module.source_roots(source_layout)
        source_root = self.module.match_source_root(
            "app/be/prisma/schema.prisma",
            roots,
        )

        allowed, reason = self.module.database_baseline_exception_allowed(
            ["app/be/prisma/schema.prisma", ".flh/runtime/STATE.md"],
            [("app/be/prisma/schema.prisma", source_root)],
            source_layout,
            state,
            committed_state,
        )

        self.assertFalse(allowed)
        self.assertIn("skip approval", reason)

    def test_database_baseline_exception_blocks_feature_code(self):
        source_layout = {
            "project": {
                "scaffold_extra_root_files": [],
            },
            "source_roots": {
                "backend": {
                    "path": "app/be",
                    "package": True,
                }
            },
        }
        state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                },
                "database_baseline": {
                    "required": True,
                    "verified": True,
                },
            },
        }
        committed_state = {
            "current_state": "FEATURE_IMPLEMENTATION",
            "approvals": {
                "source_scaffold": {
                    "created": True,
                },
            },
        }
        roots = self.module.source_roots(source_layout)
        source_root = self.module.match_source_root("app/be/src/db.ts", roots)

        allowed, _reason = self.module.database_baseline_exception_allowed(
            ["app/be/src/db.ts", ".flh/runtime/STATE.md"],
            [("app/be/src/db.ts", source_root)],
            source_layout,
            state,
            committed_state,
        )

        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
