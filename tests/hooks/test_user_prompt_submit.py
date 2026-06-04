import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = REPO_ROOT / ".flh/hooks/user_prompt_submit.py"


def load_hook_module():
    spec = importlib.util.spec_from_file_location("user_prompt_submit", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class UserPromptSubmitHookTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        shutil.copytree(REPO_ROOT / ".flh", self.root / ".flh")
        shutil.copytree(REPO_ROOT / "docs", self.root / "docs")
        self.module = load_hook_module()
        self.original_root = self.module.ROOT
        self.original_state = self.module.STATE_PATH
        self.original_flow = self.module.FLOW_PATH
        self.original_docs_spec = self.module.DOCS_SPEC_PATH
        self.original_guards = self.module.TRANSITION_GUARDS_PATH
        self.original_request_patterns = self.module.REQUEST_PATTERNS_PATH
        self.module.ROOT = self.root
        self.module.STATE_PATH = self.root / ".flh/runtime/STATE.md"
        self.module.FLOW_PATH = self.root / ".flh/workflow/flow.yml"
        self.module.DOCS_SPEC_PATH = self.root / ".flh/workflow/docs-spec.yml"
        self.module.TRANSITION_GUARDS_PATH = self.root / ".flh/workflow/transition-guards.yml"
        self.module.REQUEST_PATTERNS_PATH = self.root / ".flh/workflow/request-patterns.yml"

    def tearDown(self):
        self.module.ROOT = self.original_root
        self.module.STATE_PATH = self.original_state
        self.module.FLOW_PATH = self.original_flow
        self.module.DOCS_SPEC_PATH = self.original_docs_spec
        self.module.TRANSITION_GUARDS_PATH = self.original_guards
        self.module.REQUEST_PATTERNS_PATH = self.original_request_patterns
        self.tmpdir.cleanup()

    def write_completed_doc(self, path, sections):
        body = ["---", "status: completed", "---", "", f"# {Path(path).name}", ""]
        for section in sections:
            body.extend(
                [
                    f"## {section}",
                    "",
                    f"Completed content for {section}. This section has enough text.",
                    "",
                ]
            )
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(body), encoding="utf-8")

    def write_state(self, text):
        self.module.STATE_PATH.write_text(text, encoding="utf-8")

    def write_base_state(self, current_state):
        completed_by_state = {
            "FEATURE_INDEX_DEFINITION": [
                "MVP_DEFINITION",
                "ARCHITECTURE_DESIGN",
            ],
            "FRONTEND_DESIGN": [
                "MVP_DEFINITION",
                "ARCHITECTURE_DESIGN",
                "FEATURE_INDEX_DEFINITION",
                "DATA_MODEL_DEFINITION",
                "API_DESIGN",
            ],
        }
        lines = [
            "---",
            f"current_state: {current_state}",
            "completed_states:",
        ]
        completed = completed_by_state.get(current_state, [])
        if completed:
            lines.extend(f"  - {state}" for state in completed)
        else:
            lines[-1] = "completed_states: []"
        lines.extend(
            [
                "approvals: {}",
                "last_transition: null",
                "updated_at: null",
                "---",
                "",
                "# STATE",
                "",
            ]
        )
        self.write_state("\n".join(lines))

    def test_allows_request_type_in_current_state(self):
        result = self.module.handle_prompt("MVP 범위를 설계해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "MVP_DESIGN_REQUEST")
        self.assertEqual(result.confidence, "high")
        self.assertEqual(result.current_state, "MVP_DEFINITION")
        self.assertIsNone(result.updated_state)

    def test_alias_classifies_with_medium_confidence(self):
        result = self.module.handle_prompt("초기 범위 정리해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "MVP_DESIGN_REQUEST")
        self.assertEqual(result.confidence, "medium")
        self.assertIn("alias pattern", result.additional_prompt)

    def test_request_patterns_are_loaded_from_workflow_config(self):
        self.module.REQUEST_PATTERNS_PATH.write_text(
            "\n".join(
                [
                    "version: 1",
                    "patterns:",
                    "  MVP_DESIGN_REQUEST:",
                    "    strong:",
                    "      - custom-mvp-token",
                    "    aliases:",
                    "      - custom-alias-token",
                ]
            ),
            encoding="utf-8",
        )

        strong = self.module.classify_prompt("custom-mvp-token")
        alias = self.module.classify_prompt("custom-alias-token")
        fallback_unknown = self.module.classify_prompt("MVP 범위를 설계해줘")

        self.assertEqual(strong.request_type, "MVP_DESIGN_REQUEST")
        self.assertEqual(strong.confidence, "high")
        self.assertEqual(alias.request_type, "MVP_DESIGN_REQUEST")
        self.assertEqual(alias.confidence, "medium")
        self.assertEqual(fallback_unknown.request_type, "UNKNOWN")

    def test_unknown_allows_with_additional_prompt_without_state_change(self):
        result = self.module.handle_prompt("이 구조에 대한 의견을 말해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "UNKNOWN")
        self.assertEqual(result.confidence, "unknown")
        self.assertIn("Harness Guard", result.additional_prompt)
        output = self.module.format_codex_output(result)
        self.assertEqual(
            output["hookSpecificOutput"]["hookEventName"],
            "UserPromptSubmit",
        )
        self.assertIn(
            "UNKNOWN",
            output["hookSpecificOutput"]["additionalContext"],
        )
        self.assertIn(
            "docs/",
            output["hookSpecificOutput"]["additionalContext"],
        )
        state_text = self.module.STATE_PATH.read_text(encoding="utf-8")
        self.assertIn("current_state: MVP_DEFINITION", state_text)

    def test_ambiguous_request_asks_for_clarification_without_state_change(self):
        result = self.module.handle_prompt("mvp 구현해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "IMPLEMENTATION_REQUEST")
        self.assertEqual(result.confidence, "low")
        self.assertIn("matched_request_types", result.additional_prompt)
        self.assertIn("multiple or conflicting workflow signals", result.additional_prompt)
        state_text = self.module.STATE_PATH.read_text(encoding="utf-8")
        self.assertIn("current_state: MVP_DEFINITION", state_text)

    def test_question_confirmation_takes_priority_over_mutation_keyword(self):
        result = self.module.handle_prompt("수정하면 되는거지?")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "QUESTION_OR_CONFIRMATION_REQUEST")
        self.assertEqual(result.confidence, "high")
        self.assertIn("without creating, modifying, or deleting files", result.additional_prompt)
        state_text = self.module.STATE_PATH.read_text(encoding="utf-8")
        self.assertIn("current_state: MVP_DEFINITION", state_text)

    def test_question_prefix_forces_question_mode(self):
        result = self.module.handle_prompt("/q 커밋하고 구현해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "QUESTION_OR_CONFIRMATION_REQUEST")
        self.assertEqual(result.confidence, "high")
        self.assertIn("control prefix", result.additional_prompt)
        self.assertIn("without creating, modifying, or deleting files", result.additional_prompt)

    def test_question_prefix_takes_priority_over_documentation_prefix(self):
        result = self.module.handle_prompt("/q /d README 수정하고 커밋해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "QUESTION_OR_CONFIRMATION_REQUEST")
        self.assertEqual(result.confidence, "high")
        self.assertIn("Do not start implementation", result.additional_prompt)

    def test_documentation_prefix_allows_documentation_mode(self):
        result = self.module.handle_prompt("/d README 수정하고 커밋해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "DOCUMENTATION_REQUEST")
        self.assertEqual(result.confidence, "high")
        self.assertIn("documentation mode", result.additional_prompt)
        self.assertIn("Commit and push are allowed", result.additional_prompt)
        self.assertIn("Merge is not allowed", result.additional_prompt)

    def test_documentation_prefix_blocks_merge(self):
        result = self.module.handle_prompt("/d 머지 해줘")

        self.assertEqual(result.action, "block")
        self.assertEqual(result.request_type, "DOCUMENTATION_REQUEST")
        self.assertIn("Merge is not allowed", result.reason)

    def test_documentation_prefix_blocks_english_merge(self):
        result = self.module.handle_prompt("/d merge 해줘")

        self.assertEqual(result.action, "block")
        self.assertEqual(result.request_type, "DOCUMENTATION_REQUEST")
        self.assertIn("Merge is not allowed", result.reason)

    def test_documentation_prefix_takes_priority_over_question_text(self):
        result = self.module.handle_prompt("/d README 수정하면 되는거지?")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "DOCUMENTATION_REQUEST")
        self.assertEqual(result.confidence, "high")
        self.assertIn("documentation mode", result.additional_prompt)

    def test_question_command_mix_asks_for_clarification(self):
        result = self.module.handle_prompt("수정하면 되는거지? 앱 수정해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "IMPLEMENTATION_REQUEST")
        self.assertEqual(result.confidence, "low")
        self.assertIn(
            "QUESTION_OR_CONFIRMATION_REQUEST, IMPLEMENTATION_REQUEST",
            result.additional_prompt,
        )
        self.assertIn("explanation only", result.additional_prompt)
        state_text = self.module.STATE_PATH.read_text(encoding="utf-8")
        self.assertIn("current_state: MVP_DEFINITION", state_text)

    def test_question_command_mix_with_specific_mutation_asks_for_clarification(self):
        result = self.module.handle_prompt("왜 안돼? 파일 수정해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "IMPLEMENTATION_REQUEST")
        self.assertEqual(result.confidence, "low")
        self.assertIn(
            "QUESTION_OR_CONFIRMATION_REQUEST, IMPLEMENTATION_REQUEST",
            result.additional_prompt,
        )

    def test_question_transition_mix_asks_for_clarification(self):
        result = self.module.handle_prompt("다음 단계로 가면 되나? 다음 단계 넘어")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.confidence, "low")
        self.assertIn("QUESTION_OR_CONFIRMATION_REQUEST", result.additional_prompt)

    def test_question_patterns_are_loaded_from_workflow_config(self):
        self.module.REQUEST_PATTERNS_PATH.write_text(
            "\n".join(
                [
                    "version: 1",
                    "question_or_confirmation_patterns:",
                    "  - custom-question-token",
                    "patterns:",
                    "  IMPLEMENTATION_REQUEST:",
                    "    strong:",
                    "      - custom-question-token.*수정",
                    "    aliases: []",
                ]
            ),
            encoding="utf-8",
        )

        pure_question = self.module.classify_prompt("custom-question-token")
        mixed = self.module.classify_prompt("custom-question-token 수정")

        self.assertEqual(pure_question.request_type, "QUESTION_OR_CONFIRMATION_REQUEST")
        self.assertEqual(mixed.request_type, "IMPLEMENTATION_REQUEST")
        self.assertEqual(mixed.confidence, "low")

    def test_blocks_transition_when_required_doc_is_template(self):
        result = self.module.handle_prompt("아키텍처 설계하자")

        self.assertEqual(result.action, "block")
        self.assertEqual(result.request_type, "ARCHITECTURE_DESIGN_REQUEST")
        self.assertEqual(result.confidence, "high")
        self.assertEqual(result.target_state, "ARCHITECTURE_DESIGN")
        self.assertTrue(result.missing)
        output = self.module.format_codex_output(result)
        self.assertEqual(output["decision"], "block")
        self.assertIn("[Harness Guard: BLOCKED]", output["reason"])
        self.assertIn("Transition guard check failed", output["reason"])
        self.assertIn("Request:", output["reason"])
        self.assertIn("- current_state: MVP_DEFINITION", output["reason"])
        self.assertIn("Missing requirements:", output["reason"])
        self.assertIn("docs/MVP.md", output["reason"])
        self.assertIn("Next action:", output["reason"])

    def test_blocks_when_no_transition_path_exists(self):
        self.write_base_state("FEATURE_IMPLEMENTATION")

        result = self.module.handle_prompt("MVP 범위를 설계해줘")

        self.assertEqual(result.action, "block")
        self.assertEqual(result.request_type, "MVP_DESIGN_REQUEST")
        self.assertEqual(result.target_state, "MVP_DEFINITION")
        self.assertIn("No transition path exists", result.reason)

    def test_transitions_when_required_doc_is_completed(self):
        self.write_completed_doc(
            "docs/MVP.md",
            [
                "MVP Goal",
                "Target Users",
                "Core Problem",
                "In Scope",
                "Out of Scope",
                "Success Criteria",
            ],
        )

        result = self.module.handle_prompt("아키텍처 설계하자")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.target_state, "ARCHITECTURE_DESIGN")
        self.assertEqual(result.updated_state, "ARCHITECTURE_DESIGN")
        output = self.module.format_codex_output(result)
        self.assertIn("hookSpecificOutput", output)
        self.assertIn(
            "STATE.md was updated",
            output["hookSpecificOutput"]["additionalContext"],
        )
        state_text = self.module.STATE_PATH.read_text(encoding="utf-8")
        self.assertIn("current_state: ARCHITECTURE_DESIGN", state_text)
        self.assertIn("  - MVP_DEFINITION", state_text)

    def test_frontend_to_feature_implementation_accepts_design_approval(self):
        self.write_state(
            "\n".join(
                [
                    "---",
                    "current_state: FRONTEND_DESIGN",
                    "completed_states:",
                    "  - MVP_DEFINITION",
                    "  - ARCHITECTURE_DESIGN",
                    "  - FEATURE_INDEX_DEFINITION",
                    "  - DATA_MODEL_DEFINITION",
                    "  - API_DESIGN",
                    "approvals:",
                    "  design:",
                    "    source: external",
                    "    path: docs/DESIGN.md",
                    "    approved: true",
                    "last_transition: API_DESIGN -> FRONTEND_DESIGN",
                    "updated_at: null",
                    "---",
                    "",
                    "# STATE",
                    "",
                ]
            )
        )

        result = self.module.handle_prompt("이 기능 준비해줘")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "FEATURE_PREPARE_REQUEST")
        self.assertEqual(result.target_state, "FEATURE_IMPLEMENTATION")
        self.assertEqual(result.updated_state, "FEATURE_IMPLEMENTATION")

    def test_frontend_design_request_adds_design_selection_context(self):
        self.write_base_state("FRONTEND_DESIGN")

        result = self.module.handle_prompt("프론트 디자인 지침 정리하자")

        self.assertEqual(result.action, "allow")
        self.assertEqual(result.request_type, "FRONTEND_DESIGN_REQUEST")
        self.assertIn("FRONTEND_DESIGN uses docs/DESIGN.md", result.additional_prompt)
        self.assertIn("Import an existing external DESIGN.md", result.additional_prompt)

    def test_feature_index_requires_configured_table_fields(self):
        self.write_base_state("FEATURE_INDEX_DEFINITION")
        self.write_completed_doc(
            "docs/features/feature-index.md",
            [
                "Feature Index",
                "Feature List",
            ],
        )
        feature_index = self.root / "docs/features/feature-index.md"
        feature_index.write_text(
            "\n".join(
                [
                    "---",
                    "status: completed",
                    "---",
                    "",
                    "# Feature Index",
                    "",
                    "## Feature Index",
                    "",
                    "Completed feature index summary with enough detail.",
                    "",
                    "## Feature List",
                    "",
                    "| Feature ID | Name | Summary |",
                    "| --- | --- | --- |",
                    "| FEAT-001 | Login | User login flow |",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = self.module.handle_prompt("데이터 모델 설계하자")

        self.assertEqual(result.action, "block")
        self.assertIn("Priority", result.missing[0])
        self.assertIn("Core Requirements", result.missing[0])

    def test_write_state_preserves_nested_approvals_as_yaml(self):
        self.write_state(
            "\n".join(
                [
                    "---",
                    "current_state: FRONTEND_DESIGN",
                    "completed_states:",
                    "  - MVP_DEFINITION",
                    "  - ARCHITECTURE_DESIGN",
                    "  - FEATURE_INDEX_DEFINITION",
                    "  - DATA_MODEL_DEFINITION",
                    "  - API_DESIGN",
                    "approvals:",
                    "  design:",
                    "    source: external",
                    "    path: docs/DESIGN.md",
                    "    approved: true",
                    "last_transition: API_DESIGN -> FRONTEND_DESIGN",
                    "updated_at: null",
                    "---",
                    "",
                    "# STATE",
                    "",
                    "Custom state guide must be preserved.",
                    "",
                ]
            )
        )

        result = self.module.handle_prompt("이 기능 준비해줘")

        self.assertEqual(result.action, "allow")
        state_text = self.module.STATE_PATH.read_text(encoding="utf-8")
        self.assertIn("approvals:", state_text)
        self.assertIn("  design:", state_text)
        self.assertIn("    source: external", state_text)
        self.assertIn("    path: docs/DESIGN.md", state_text)
        self.assertIn("    approved: true", state_text)
        self.assertNotIn('approvals: {"design"', state_text)
        self.assertIn("Custom state guide must be preserved.", state_text)


if __name__ == "__main__":
    unittest.main()
