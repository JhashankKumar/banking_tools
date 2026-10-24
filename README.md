# OpenFraud Investigator

**Trace the money. Connect the evidence. Investigate with AI.**

An open-source AI copilot for fraud investigation, transaction graph analysis, and evidence-grounded financial-crime workflows.

> **Status: Milestone 3 — synthetic data, login, case API, detection rules, money paths, and case graph data.** No UI or AI features yet. See the [implementation plan](docs/project/IMPLEMENTATION_PLAN.md).
>
> **Synthetic data only.** This is a demonstration project. Never load real customer or bank data. It is not production-ready and makes no compliance or fraud-accuracy claims.

## Prerequisites

| Tool                             | Version    |
| -------------------------------- | ---------- |
| Python                           | 3.12       |
| [uv](https://docs.astral.sh/uv/) | 0.13.1     |
| Node.js                          | 24         |
| [pnpm](https://pnpm.io/)         | 11         |
| Docker + Compose v2              | any recent |

Install uv if you don't have it, then make sure `~/.local/bin` is on your `PATH` (open a new shell or run `source ~/.local/bin/env`):

```bash
curl -LsSf https://astral.sh/uv/0.13.1/install.sh | sh
uv --version   # uv 0.13.1
```

Node 24 is required (`apps/web/package.json` declares `engines.node >=24`). If you use nvm: `nvm install 24`.

## Run locally

### 1. Configure

```bash
cp .env.example .env
```

Fill in every `<PLACEHOLDER>` in `.env` with your own local values:

- `OFI_DB_USER` / `OFI_DB_PASSWORD`: any throwaway local credentials; use the same values inside `OFI_DATABASE_URL` and `OFI_TEST_DATABASE_URL`.
- `OFI_JWT_SECRET`: generate with `openssl rand -hex 32`.
- `OFI_DEMO_PASSWORD`: at least 12 characters; the seeded demo users log in with it.

`.env` is git-ignored. Never commit it.

### 2. Start the database

Requires Docker with the Compose v2 plugin (`docker compose version`). On Ubuntu: `sudo apt install docker-compose-v2`.

```bash
docker compose up -d db        # PostgreSQL 16 on localhost:5433 (also creates openfraud_test)
```

### 3. Backend API (`services/api`)

```bash
cd services/api
uv sync
uv run alembic upgrade head    # create tables
uv run python -m app.seed      # load synthetic cases and demo users, then run detection
uv run python -m app.modules.detection   # re-run detection rules any time (idempotent)
uv run uvicorn app.main:app --reload
# http://localhost:8000/api/v1/health → {"status":"ok"}
```

With `OFI_DOCS_ENABLED=true`, open http://localhost:8000/docs, click **Authorize**, sign in as `analyst.demo` with your `OFI_DEMO_PASSWORD`, and call `GET /api/v1/cases/FR-10482/transactions`.

Demo users (synthetic; roles are role-based access only):

| Username          | Role       | Can                                                 |
| ----------------- | ---------- | --------------------------------------------------- |
| `analyst.demo`    | Analyst    | read cases, transactions, alerts, evidence          |
| `supervisor.demo` | Supervisor | analyst access + case status changes + manage users |
| `auditor.demo`    | Auditor    | read the audit log only                             |

### 4. Frontend (`apps/web`)

Keep the API from step 3 running, then in a second terminal:

```bash
cd apps/web
cp .env.example .env.local     # OFI_API_URL: where the API listens (server-only, never sent to the browser)
pnpm install
pnpm dev                       # or: pnpm build && pnpm start
# http://localhost:3000
```

Sign in as one of the demo users above with your `OFI_DEMO_PASSWORD`:

- `analyst.demo` lands on **Alerts**. Open `AL-ROT-TX-1002` → case **FR-10482** shows the money path ACC-001 → BEN-B → ACC-C in the graph ("3D look", or "3D view" to rotate), the timeline in IST, and the evidence IDs.
- `supervisor.demo` also sees **Users** (create users, change roles, deactivate).
- `auditor.demo` sees only the **Audit log**.

The browser never holds the API token: Next.js keeps it in an `httpOnly` cookie and forwards calls through `/bff/*` (see `docs/project/API_AND_CODE_CONVENTIONS.md` §3.5).

## Checks

These are the same checks CI runs on every push and pull request.

Backend:

```bash
cd services/api
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run alembic check           # models and migrations agree
uv run pytest                  # needs the database from step 2
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
- [Detection rules](docs/project/DETECTION_RULES.md) · [API and code conventions](docs/project/API_AND_CODE_CONVENTIONS.md)
- [Decisions](docs/decisions/)
- [Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md) · [Code of conduct](CODE_OF_CONDUCT.md)

## License

[MIT](LICENSE)
