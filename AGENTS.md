# AGENTS.md

## Core Routing

- Always read `.flh/runtime/STATE.md` before choosing a workflow.
- For project workflow work, read only the current state's entry from `.flh/workflow/state-actions.yml`.
- Follow the current state's `actions`, `allowed_extra_writes`, and `ask_user_when`.
- Do not perform implementation work unless `current_state` is `FEATURE_IMPLEMENTATION`.

## Prefix Modes

- `/q`: question mode. Answer only. Do not create, modify, delete, commit, push, merge, update state, or run workflow pipelines.
- `/d`: documentation and harness-control mode.
- `/d` may modify only documentation and harness-maintenance targets: `docs/`, `.flh/`, `AGENTS.md`, `README.md`, `.codex/`, `tests/hooks/`, `.husky/`, `package.json`, `package-lock.json`.
- `/d` may commit or push only when the user explicitly requests it and every changed file is within the allowed documentation/harness targets.
- `/d` must not merge.
- `/d` may perform explicit workflow state skip/transition requests.
- Do not skip `MVP_DEFINITION`, `ARCHITECTURE_DESIGN`, or `FEATURE_INDEX_DEFINITION`.

## Feature Implementation

- Run `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md` only when `current_state` is `FEATURE_IMPLEMENTATION` and the user explicitly asks for feature implementation.
- If the user has not explicitly requested implementation, do not run the implementation pipeline; ask whether they want to start or continue feature implementation.
- Before running the full implementation pipeline, inspect `docs/features/active/` and `docs/features/review/`.
- If `docs/features/active/` contains a feature directory, tell the user there is already an active feature and ask whether to continue it, block it, or finish it before starting another feature.
- If `docs/features/review/` contains a feature directory, do not run the full implementation pipeline; use the review patch rules.
- Do not start a new feature when either `docs/features/active/` or `docs/features/review/` contains a feature directory.
- For status, progress, or next-work questions, answer only; do not run the implementation pipeline.

## Review Patch

- If `docs/features/review/` contains a feature directory, user edit requests target that feature by default.
- Do not run `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md` for review feature edits.
- Apply only lightweight patches: understand the requested change, keep scope minimal, and edit only what is needed.
- Run related tests when applicable.
- Update the feature's `QUALITY_SCORE.md` if the change affects quality.
- Move a feature from `docs/features/review/` to `docs/features/done/` only when the user explicitly approves completion.
