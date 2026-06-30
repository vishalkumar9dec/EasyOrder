---
name: easyorder-implement-task
description: "Implement the next EasyOrder task from docs/implementation-tasks.md with a clean feature branch, development, debugging, regression verification, manual UI test-plan updates, test report preparation, and pull request creation. Use when the user asks to implement the next EasyOrder task, implement according to implementation-tasks.md, develop/test/debug an EasyOrder issue, update manual-ui-test-plan.md after development, or prepare a PR after verified implementation."
---

# EasyOrder Implement Task

## User Prompt

Use this skill when the user wants the recurring EasyOrder implementation workflow captured by this prompt:

```text
implement the next task as per the [implementation-tasks.md](docs/implementation-tasks.md). Develop, test and debug any issue in between. This development should not break the existing functionality. Once the development is verified, update the [manual-ui-test-plan.md](docs/manual-ui-test-plan.md) so that I can verify the application manually. Start clean on a new feature branch, once the development is complete, manually verified, create a PR and the after the manual approval, it can be merged. Once the development is complete, prepare a test report as well for me so that I can verify what test was executed, what was result and if there are any regressions.
```

## Workflow

1. Establish the starting point.
   - Run `git status --short --branch`.
   - Confirm whether local `main` is clean and synced enough to branch from.
   - If local commits are ahead of `origin/main`, tell the user before branching or pushing.
   - Do not discard unrelated user changes.

2. Identify the next EasyOrder task.
   - Refer to the `/goal` skill or goal workflow before implementation so the objective and completion boundary are explicit.
   - Refer to the `easyorder-daily-status` skill before selecting the task. Run or use its status workflow, then verify that its "next task" output aligns with `docs/implementation-tasks.md`.
   - Read `docs/implementation-tasks.md`.
   - Read nearby source-of-truth docs when needed: `docs/easyorder-prd.md`, `docs/implementation-plan.md`, and `docs/manual-ui-test-plan.md`.
   - If GitHub status matters, request network approval and run `gh issue list --state all --limit 30 --json number,title,state,labels,url`.
   - Respect the restaurant/brand/source attribution and one-restaurant-one-order requirements. If issue `#4` still needs source attribution, treat that as the next task before issue `#5`.

3. Start clean on a feature branch.
   - Use a `codex/` branch name unless the user requested another naming scheme.
   - Prefer a branch name tied to the issue or task, for example `codex/issue-4-source-attribution`.
   - Emit the git branch directive in the final response only after the branch is actually created.

4. Implement the task end to end.
   - Read the relevant code before editing.
   - Make scoped changes using existing project patterns.
   - Add or update automated tests for the behavior changed.
   - Debug failures until the implementation is verified or a real blocker is found.

5. Preserve existing behavior.
   - Run the project verification suite after implementation.
   - At minimum run:

```bash
make test
make frontend-build
src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests
```

   - If API fixture behavior is involved, probe sample payloads under `docs/api-test-data/`.
   - If UI behavior is involved, run or start the app and manually verify with browser tooling when feasible.

6. Update manual verification docs.
   - Update `docs/manual-ui-test-plan.md` with new or changed manual test cases.
   - Include the expected UI/API behavior the user should verify.
   - Remove or adjust stale expectations that no longer match implemented behavior.

7. Prepare a test report.
   - Include commands executed, pass/fail result, and notable coverage.
   - Call out regressions, skipped checks, or risks plainly.
   - If no regressions are found, say that explicitly.

8. Commit, push, and open a PR after verification.
   - Review `git diff` before staging.
   - Commit only intended changes.
   - Push the feature branch.
   - Create a PR with a concise summary, test report, and manual verification notes.
   - Do not merge the PR. Stop after PR creation and state that merge requires manual approval.

## Final Response

End with:

- Branch and PR link, if created.
- Implementation summary.
- Test report.
- Manual verification instructions from `docs/manual-ui-test-plan.md`.
- Known risks or skipped checks.
- Clear statement that the PR is waiting for manual approval before merge.
