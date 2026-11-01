# OpenFraud Investigator

**Trace the money. Connect the evidence. Investigate with AI.**

An open-source AI copilot for fraud investigation, transaction graph analysis, and evidence-grounded financial-crime workflows.

**What it does:**

- **Deterministic detection rules**: rapid onward transfer, fan-out split, fan-in collect and circular flow, with cross-currency transfers compared only through recorded conversions.
- **Money paths**: trace funds across accounts and see them on an interactive transaction graph.
- **Investigator UI**: alerts, cases, evidence and a "why it fired" explanation for every alert.
- **Evidence-grounded AI copilot**: answers cite case evidence, decline customer-information questions, and draft case notes that a supervisor reviews (four-eyes).
- **In-app safety checks**: scripted attacks run against the real defences.
- **Reproducible benchmark**: labelled synthetic scenarios with published, seed-stable results.

See the [demo script](docs/DEMO.md) for a guided walkthrough.

> **Synthetic data only.** This is a demonstration project. Never load real customer or bank data. It is not production-ready and makes no compliance or fraud-accuracy claims.

![Case FR-10482: why the alert fired, the money-flow graph and the evidence](docs/images/case-graph.png)

| | |
|---|---|
| ![Alerts list](docs/images/alerts.png) | ![Copilot declining a customer-information question](docs/images/copilot.png) |
| ![Notes awaiting supervisor review](docs/images/reviews.png) | ![Safety checks: 33 passed](docs/images/safety-checks.png) |

## Quick start

Already have the [prerequisites](#prerequisites)? From the repository root:

```bash
cp .env.example .env                      # then fill in every <PLACEHOLDER> (see step 1)
cp frontend/.env.example frontend/.env.local

docker compose up -d --wait               # PostgreSQL 16 on localhost:5433

cd backend
uv sync
uv run alembic upgrade head               # create tables
uv run python -m app.seed                 # synthetic cases, demo users, detection
uv run uvicorn app.main:app --reload      # terminal 1 → http://localhost:8000

cd frontend                               # terminal 2, from the repository root
pnpm install
pnpm dev                                  # → http://localhost:3000
```

Sign in as `analyst.demo` with your `OFI_DEMO_PASSWORD` and open an alert.

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

Node 24 is required (`frontend/package.json` declares `engines.node >=24`). If you use nvm: `nvm install 24`. Docker needs the Compose v2 plugin (`docker compose version`); on Ubuntu: `sudo apt install docker-compose-v2`.

## Set up and run, step by step

### 1. Configure

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local   # OFI_API_URL: where the API listens (server-only)
```

Fill in every `<PLACEHOLDER>` in `.env` with your own local values:

- `OFI_DB_USER` / `OFI_DB_PASSWORD` / `OFI_DB_NAME`: any throwaway local credentials; use the same values inside `OFI_DATABASE_URL` and `OFI_TEST_DATABASE_URL`.
- `OFI_JWT_SECRET`: generate with `openssl rand -hex 32`.
- `OFI_DEMO_PASSWORD`: at least 12 characters; all seeded demo users sign in with it.
- `OPENROUTER_API_KEY` (optional): enables live copilot answers; see [AI copilot](#ai-copilot-optional).

`.env` and `frontend/.env.local` are git-ignored. Never commit them.

### 2. Start the database

```bash
docker compose up -d --wait    # PostgreSQL 16 on localhost:5433 (also creates openfraud_test)
```

### 3. Backend API (`backend/`, terminal 1)

```bash
cd backend
uv sync
uv run alembic upgrade head              # create or update tables
uv run python -m app.seed                # load synthetic cases and demo users, then run detection
uv run uvicorn app.main:app --reload
# http://localhost:8000/api/v1/health → {"status":"ok"}
```

`uv run python -m app.modules.detection` re-runs the detection rules at any time; it is safe to repeat. With `OFI_DOCS_ENABLED=true`, http://localhost:8000/docs has the interactive API docs (**Authorize** with a demo user).

### 4. Frontend (`frontend/`, terminal 2)

Keep the API running, then:

```bash
cd frontend
pnpm install
pnpm dev                       # development, http://localhost:3000
# or, for a demo without the development badge:
pnpm build && pnpm start
```

The browser never holds the API token: Next.js keeps it in an `httpOnly` cookie and forwards calls through `/api/*` (see `docs/project/API_AND_CODE_CONVENTIONS.md` §3.5).

### 5. Sign in

Demo users are synthetic and share the password you set as `OFI_DEMO_PASSWORD`. Access is role-based only.

| Username          | Role       | Can                                                                                         |
| ----------------- | ---------- | ------------------------------------------------------------------------------------------- |
| `analyst.demo`    | Analyst    | Alerts and cases, the AI copilot, write and submit case notes                               |
| `supervisor.demo` | Supervisor | Analyst access + review notes (four-eyes), close cases, manage users, run safety checks     |
| `auditor.demo`    | Auditor    | Audit log and safety checks only (read-only)                                                |

If sign-in fails, the users may have been seeded with an older `OFI_DEMO_PASSWORD`: reset the database (below) and seed again.

## What's in the seeded data

Thirteen synthetic cases, described in full in the [synthetic casebook](docs/banking-domain/SYNTHETIC_CASEBOOK.md). Four deterministic rules ([detection rules](docs/project/DETECTION_RULES.md)) raise 10 alerts: rapid onward transfer (ROT), fan-out split (FOS), fan-in collect (FIC) and circular flow (CIR).

| Case | Pattern | Alerts |
|---|---|---|
| FR-10482 | Rapid onward transfer ACC-001 → BEN-B → ACC-C | `AL-ROT-TX-1002` |
| FR-10483 | Large scheduled supplier payment | none |
| FR-10484 | Funds return to the sender, hours apart | `AL-CIR-TX-4003` |
| FR-10485 | Transfer later reversed | none |
| FR-10486 | Instruction-like text in a transaction description | none |
| FR-10488 | No authoritative settlement status | none |
| FR-10489 | Fan-in: five payers, then sent on | `AL-ROT-TX-8906`, `AL-FIC-TX-8906` |
| FR-10490 | Fan-out: a large credit split into five smaller transfers | `AL-FOS-TX-9006` (silent for ROT) |
| FR-10491 | Fast three-hop chain | `AL-ROT-TX-9102`, `AL-ROT-TX-9103` |
| FR-10492 | Busy account: salary, a failed attempt, pending and rent, one pass-through | `AL-ROT-TX-9204` |
| FR-10493 | INR in, sent abroad in USD with a recorded conversion | `AL-ROT-TX-9302` |
| FR-10494 | Benign look-alike: company funding, then same-day payroll | `AL-FOS-TX-9406` (the payroll caveat applies) |
| FR-10495 | Benign look-alike: merchant collections settled hours later | none |

Transfers in different currencies are compared only through the converted amount and rate recorded on the transfer, never an assumed exchange rate ([detection rules](docs/project/DETECTION_RULES.md)).

## AI copilot (optional)

The case page's copilot calls an open-weight model through [OpenRouter](https://openrouter.ai/). Add your own key to the repo-root `.env` (never commit it):

```bash
OPENROUTER_API_KEY=<your OpenRouter key>
OPENROUTER_MODEL=openai/gpt-oss-120b   # any open-weight model with tool calling
```

Restart the API after changing `.env`. Without a key the copilot answers "unavailable"; everything else, including declining customer-information questions, still works. A live answer can take up to about two minutes on a slow connection. Limits: 20 questions per user per hour and US$2 per day across all users (`OFI_COPILOT_QUESTIONS_PER_HOUR`, `OFI_COPILOT_DAILY_BUDGET_USD`).

Compare models on the seeded cases (capped spend, prints a table, writes nothing):

```bash
cd backend
uv run python -m app.modules.copilot.compare --models openai/gpt-oss-120b,qwen/qwen3-235b-a22b-2507 --cap-usd 1.00
```

## Safety checks

Sign in as `supervisor.demo` or `auditor.demo`, open **Safety checks** (`/safety`) and press **Run checks**. 33 scripted attacks run against the real defences: prompt injection, customer-information questions, access control, tool abuse, grounding, limits, and audit and secrets. Only the model is scripted; each run happens in a transaction that is rolled back, so data does not change. One `safety.checks.run` audit row records the counts. The same catalogue runs in the test suite:

```bash
cd backend
uv run pytest -q tests/security
```

What the checks do **not** cover, with measurements: [SECURITY_LIMITATIONS.md](docs/project/SECURITY_LIMITATIONS.md).

## Benchmark

```bash
cd backend
uv run python -m app.benchmark --seed 20261101 --variants 50
```

Generates 16 labelled synthetic scenario families (800 variants), scores the detection rule, the money-path finder and the copilot's answer validator, and writes [docs/evaluation/results/](docs/evaluation/results/RESULTS.md). The same seed gives the same metrics on any machine; CI checks the published results. It is a regression benchmark on project-written data, not real-world performance: see [docs/evaluation/README.md](docs/evaluation/README.md).

With a key, `--live --models openai/gpt-oss-120b --cap-usd 1.00` adds a live-model section; use `--out <dir>` for that run so the published results stay reproducible.

## Update, reset and stop

After pulling new code:

```bash
cd backend && uv sync && uv run alembic upgrade head && uv run python -m app.seed
cd ../frontend && pnpm install
```

Seeding again adds new cases and resets the seeded case rows (for example a closed FR-10482 reopens), but keeps notes, chats and audit history. For a completely clean database, for example before a demo (**this deletes all local data**):

```bash
docker compose down -v && docker compose up -d --wait
cd backend && uv run alembic upgrade head && uv run python -m app.seed
```

Stop: `Ctrl+C` in both terminals, then `docker compose stop` (keeps the data).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `uv: command not found` | `source ~/.local/bin/env`, or add `~/.local/bin` to `PATH` |
| API fails to start: database connection refused | `docker compose up -d --wait`; check the credentials in `OFI_DATABASE_URL` match `OFI_DB_USER` / `OFI_DB_PASSWORD` |
| "Target database is not up to date" | `cd backend && uv run alembic upgrade head` |
| Sign-in rejected | Seeded with another `OFI_DEMO_PASSWORD`: reset and seed again |
| Frontend shows "The API is not reachable." | Start the API (step 3); check `OFI_API_URL` in `frontend/.env.local` |
| Copilot says "unavailable" | No `OPENROUTER_API_KEY`, the model failed, or the run passed its time limit; restart the API after editing `.env` |
| Safety checks show "skipped" | The casebook is not seeded: `uv run python -m app.seed` |

## Checks

These are the same checks CI runs on every push and pull request.

Backend:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run alembic check           # models and migrations agree
uv run pytest                  # needs the database from step 2
```

Frontend:

```bash
cd frontend
pnpm lint
pnpm typecheck
pnpm format:check
pnpm test
pnpm build
```

Fix formatting with `uv run ruff format .` (backend) and `pnpm format` (frontend).

## Repository layout

```text
frontend/             Next.js frontend (TypeScript, Tailwind, Vitest)
backend/              FastAPI backend (Pydantic, SQLAlchemy, Alembic, pytest, ruff, pyright)
docs/project/         Product brief, architecture, engineering principles
docs/banking-domain/  Banking and fraud-investigation domain context, synthetic casebook
docs/decisions/       Architecture decision records
docs/evaluation/      Benchmark method and published results
docs/images/          README screenshots
.github/              CI, issue and pull request templates
```

## Documentation

- [Project knowledge base](docs/project/README.md)
- [Banking domain knowledge base](docs/banking-domain/README.md) · [Synthetic casebook](docs/banking-domain/SYNTHETIC_CASEBOOK.md)
- [Detection rules](docs/project/DETECTION_RULES.md) · [API and code conventions](docs/project/API_AND_CODE_CONVENTIONS.md)
- [Demo script](docs/DEMO.md) · [Security limitations](docs/project/SECURITY_LIMITATIONS.md) · [Evaluation](docs/evaluation/README.md) · [First issues](docs/project/FIRST_ISSUES.md)
- [Decisions](docs/decisions/)
- [Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md) · [Code of conduct](CODE_OF_CONDUCT.md)

## License

[MIT](LICENSE)
