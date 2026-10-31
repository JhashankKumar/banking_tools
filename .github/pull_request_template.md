## What and why

<!-- What changed, and the problem it solves. Link the issue. -->

## How it was tested

<!-- Tests added or changed; manual checks with the role used. -->

## Checks

- [ ] Backend: `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run alembic check && uv run pytest`
- [ ] Frontend: `pnpm lint && pnpm typecheck && pnpm format:check && pnpm test && pnpm build`
- [ ] New or changed defence: a safety check in `backend/app/modules/safety/checks/`, seen to fail with the defence off
- [ ] Detection, paths or answer validator changed: benchmark rerun and `docs/evaluation/results/` updated

## Data and secrets

- [ ] Synthetic data only: no real customer, account or bank data in code, fixtures, screenshots or logs.
- [ ] No secrets, tokens or keys added; placeholders such as `<OPENROUTER_API_KEY>` only.
