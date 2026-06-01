# AGENTS.md

## Project Guard

- Always read `.flh/runtime/STATE.md` before deciding what workflow applies.
- When performing project workflow work, read only the current state's entry from `.flh/workflow/state-actions.yml`.
- Do not run the feature implementation pipeline unless `current_state` is `FEATURE_IMPLEMENTATION`.
- When `current_state` is not `FEATURE_IMPLEMENTATION`, only design, documentation, and analysis work is allowed.

## Prefix Modes

- `/q`: question mode. Answer only. Do not create, modify, delete, commit, push, merge, update `STATE.md`, or run workflow pipelines.
- `/d`: documentation mode. Documentation, harness-maintenance, and explicit workflow state control are allowed. Commit and push are allowed only when explicitly requested and every changed file is within the allowed documentation/harness targets. Merge is forbidden.

## File Write Rules

When `current_state` is not `FEATURE_IMPLEMENTATION`, file creation/modification/deletion is limited to:

- `docs/`
- `.flh/runtime/`
- `.flh/workflow/`
- `.flh/docs/`

Additional `/d` documentation-mode targets:

- `AGENTS.md`
- `README.md`
- `.flh/`
- `.codex/`
- `.flh/hooks/`
- `tests/hooks/`
- `.husky/`
- `package.json`
- `package-lock.json`

Forbidden outside `FEATURE_IMPLEMENTATION`:

- `app/`
- `apps/`
- `src/`
- `tests/`
- feature implementation code
- test files
- DB migrations
- worktree/branch creation
- commit/push/merge

Exceptions:

- In `/d` documentation mode, commit and push are allowed only when the user explicitly requests them and all changed files are limited to the allowed documentation/harness targets.
- Merge remains forbidden in `/d` documentation mode.
- In `/d` documentation mode, explicit workflow state skip/transition requests may update `.flh/runtime/STATE.md`, but `MVP_DEFINITION`, `ARCHITECTURE_DESIGN`, and `FEATURE_INDEX_DEFINITION` must not be skipped.
- In `DATA_MODEL_DEFINITION`, Prisma baseline creation may modify:
  - `app/be/package.json`
  - `app/be/prisma/schema.prisma`
  - `app/be/prisma/migrations/**`
  - root `package.json` DB forwarding scripts when needed

## Feature Implementation

If `current_state` is `FEATURE_IMPLEMENTATION` and the user explicitly asks to implement, follow:

- `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`
- `docs/features/feature-index.md`
- the selected feature's `SPEC.md`, `CHECKLIST.md`, and `TEST_CASES.md`

Do not exceed the feature scope or violate its non-goals.

Feature concurrency rules:

- Do not start a new feature if `docs/features/active/` or `docs/features/review/` contains a feature directory.
- `docs/features/review/` may contain at most one feature directory.
- If `docs/features/review/` contains one feature, user edit requests target that feature by default.
- For a feature in `docs/features/review/`, do not run the full feature implementation pipeline again.
- Apply only the lightweight review patch flow: understand the requested change, keep the scope minimal, edit only what is needed, run related tests when applicable, and update the feature's `QUALITY_SCORE.md` if the change affects quality.
- Move a feature from `review/` to `done/` only when the user explicitly approves completion.

Database baseline rule:

- Before moving the first feature into `docs/features/active/`, confirm `.flh/runtime/STATE.md` has `approvals.database_baseline.verified: true`.
- If it is missing, ask the user for the required DB environment setup and run the baseline DB deployment flow from `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`.
- Do not write API keys, service keys, passwords, or connection secrets into project docs or `STATE.md`.
- Record only non-secret deployment status, provider, environment, and verification timestamp in `STATE.md`.

## Progress Questions

If the user asks about progress, current status, next work, or remaining work, do not execute the implementation pipeline.

Answer using only:

- `.flh/runtime/STATE.md`
- `docs/features/feature-index.md`
- `docs/features/backlog/**`
- `docs/features/ready/**`
- `docs/features/active/**`
- `docs/features/review/**`

Only create branches, worktrees, code, tests, commits, pushes, or merges when explicitly requested.

## References

- Project workflow: `.flh/docs/PROJECT_WORKFLOW.md`
- Feature implementation pipeline: `.flh/docs/FEATURE_IMPLEMENTATION_PIPELINE.md`
- Document map: `docs/docs-map.md` 
