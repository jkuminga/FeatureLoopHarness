import importlib.util
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

    def test_package_manager_normalizes_versions(self):
        self.assertEqual(self.module.normalize_package_manager("pnpm@9.0.0"), "pnpm")
        self.assertEqual(self.module.normalize_package_manager("npm@10.0.0"), "npm")
        self.assertEqual(self.module.normalize_package_manager("yarn"), "yarn")

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
