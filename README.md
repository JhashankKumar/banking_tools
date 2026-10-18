# OpenFraud Investigator

**Trace the money. Connect the evidence. Investigate with AI.**

An open-source AI copilot for fraud investigation, transaction graph analysis, and evidence-grounded financial-crime workflows.

> **Status: Milestone 0 — project skeleton only.** There are no investigation features yet. See the [implementation plan](docs/project/IMPLEMENTATION_PLAN.md).
>
> **Synthetic data only.** This is a demonstration project. Never load real customer or bank data. It is not production-ready and makes no compliance or fraud-accuracy claims.

## Prerequisites

| Tool                             | Version |
| -------------------------------- | ------- |
| Python                           | 3.12    |
| [uv](https://docs.astral.sh/uv/) | 0.13.1  |
| Node.js                          | 24      |
| [pnpm](https://pnpm.io/)         | 11      |

Install uv if you don't have it, then make sure `~/.local/bin` is on your `PATH` (open a new shell or run `source ~/.local/bin/env`):

```bash
curl -LsSf https://astral.sh/uv/0.13.1/install.sh | sh
uv --version   # uv 0.13.1
```

Node 24 is required (`apps/web/package.json` declares `engines.node >=24`). If you use nvm: `nvm install 24`.

## Run locally

Backend API (`services/api`):

```bash
cd services/api
uv sync
uv run uvicorn app.main:app --reload
# http://localhost:8000/api/v1/health → {"status":"ok"}
```

Frontend (`apps/web`):

```bash
cd apps/web
pnpm install
pnpm dev
# http://localhost:3000
```

Configuration: copy `.env.example` to `services/api/.env` if you need local overrides. Never commit `.env` files.

## Checks

These are the same checks CI runs on every push and pull request.

Backend:

```bash
cd services/api
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
```

Frontend:

```bash
cd apps/web
pnpm lint
pnpm typecheck
pnpm format:check
pnpm test
pnpm build
```

## Repository layout

```text
apps/web/          Next.js frontend (TypeScript, Tailwind, Vitest)
services/api/      FastAPI backend (Pydantic, pytest, ruff, pyright)
docs/project/      Product brief, architecture, engineering principles, plan
docs/banking-domain/  Banking and fraud-investigation domain context
docs/decisions/    Architecture decision records
.github/workflows/ CI
```

## Documentation

- [Project knowledge base](docs/project/README.md)
- [Banking domain knowledge base](docs/banking-domain/README.md)
- [Decisions](docs/decisions/)
- [Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md) · [Code of conduct](CODE_OF_CONDUCT.md)

## License

[MIT](LICENSE)
