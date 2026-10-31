# Contributing to OpenFraud Investigator

Thanks for helping. This project is a synthetic-data demonstration of evidence-grounded fraud investigation, so a few rules matter more than usual.

## Ground rules

- **Synthetic data only.** Never add real customer, account, or bank data to code, fixtures, issues, logs, or screenshots.
- **No secrets.** Never commit API keys, passwords, or tokens. Use placeholders like `<OPENROUTER_API_KEY>` and keep real values in an ignored `.env`.
- **Neutral wording.** A detection alert or money path is a signal for review, not proof of fraud. Follow [AI domain guardrails](docs/banking-domain/AI_DOMAIN_GUARDRAILS.md).
- **Simple, traceable code.** Follow the [engineering principles](docs/project/ENGINEERING_PRINCIPLES.md): KISS, YAGNI, thin routes, domain logic independent of HTTP/UI/LLM code, server-side authorization.

## Workflow

1. Open or pick an issue and describe the change you plan.
2. Create a branch from `main`.
3. Write tests alongside the change (add a regression test for every bug fix).
4. Run all checks locally (below) and make sure they pass.
5. Open a pull request explaining what changed, why, and how you tested it.

Material architecture changes need a short ADR in [`docs/decisions/`](docs/decisions/).

## Local checks

Backend tests need the local database (`docker compose up -d db`, see README). Schema changes need an Alembic migration (`uv run alembic revision --autogenerate -m "..."`), reviewed by hand.

Backend (`backend`):

```bash
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run alembic check && uv run pytest
```

The security suite (`uv run pytest -q tests/security`) runs every safety check against the real defences; a new defence needs a check there (see `backend/app/modules/safety/checks/`) that you have seen fail with the defence switched off. If you change detection, paths or the answer validator, rerun the benchmark and commit its output; CI fails if `docs/evaluation/results/` is stale:

```bash
uv run python -m app.benchmark --seed 20261101 --variants 50
```

Frontend (`frontend`):

```bash
pnpm lint && pnpm typecheck && pnpm format:check && pnpm test && pnpm build
```

## Reporting security issues

Do not open public issues for vulnerabilities. See [SECURITY.md](SECURITY.md).
