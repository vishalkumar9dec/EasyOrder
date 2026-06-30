---
name: easyorder-daily-status
description: "Run the daily EasyOrder project status workflow: verify local tests/build/lint, probe WhatsApp webhook sample payloads, inspect implementation docs for issue order, optionally fetch GitHub issue status, and summarize the next implementation task. Use when the user asks for current project status, daily verification, whether everything is working, next task, expected changes after implementation, or mentions restaurant/brand/source attribution and one-restaurant-one-order follow-up work."
---

# EasyOrder Daily Status

## Workflow

1. Run the local verification script from the repository root:

```bash
python3 .agents/skills/easyorder-daily-status/scripts/daily_status.py --repo-root .
```

2. If the user wants current GitHub issue state, or if the report depends on live issue labels, request approval for network access and run:

```bash
gh issue list --state all --limit 30 --json number,title,state,labels,url
```

3. Read the current source-of-truth docs after the script finishes:

- `docs/implementation-tasks.md`
- `docs/manual-ui-test-plan.md`
- `docs/easyorder-prd.md`
- `docs/implementation-plan.md`

4. Report four things, in this order:

- Current branch/worktree and whether local verification passed.
- Current project status, including closed/open issue order.
- The next implementation task.
- Expected user-visible and API/data changes after that task.

## Project-Specific Decision Rules

- Treat restaurant/brand/source attribution as part of the issue `#4` agent-cart contract until implementation proves otherwise.
- If issue `#4` is open or docs say "Needs vendor/source follow-up", the next task is the `#4` follow-up before issue `#5`.
- Do not describe issue `#5` WhatsApp link handoff as next while source attribution is incomplete, even if older docs call `#5` "ready next".
- Always mention the Swiggy constraint: one Food order cannot span multiple restaurants. Food checkout must eventually split by `restaurant_id`; Instamart remains a separate checkout group.
- Distinguish implemented behavior from documented/planned behavior. If docs require restaurant names but current API schemas do not yet expose them, say that clearly.

## Verification Expectations

The daily report should include results for:

- `make test`
- `make frontend-build`
- `src/backend/.venv/bin/python -m ruff check src/backend/app src/backend/tests`
- WhatsApp payload fixtures in `docs/api-test-data/whatsapp-*.json`

If a command fails because dependencies are missing, report the failing command and the likely setup command rather than assuming the product is broken.
