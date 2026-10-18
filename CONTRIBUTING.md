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

Backend (`services/api`):

```bash
uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest
```

Frontend (`apps/web`):

```bash
pnpm lint && pnpm typecheck && pnpm format:check && pnpm test && pnpm build
```

## Reporting security issues

Do not open public issues for vulnerabilities. See [SECURITY.md](SECURITY.md).
