# Architecture and Folder Structure

## Architecture choice
Start with a **modular monolith**: one API deployment with clearly separated domain modules. It is easier to run, test, contribute to, and deploy than a set of microservices. Keep module boundaries so later extraction is possible if justified.

## Repository layout

One frontend and one backend, so each sits directly at the repository root (no `apps/` or `services/` wrapper; decided in ADR 0001 #21). Items marked *planned* do not exist yet.

```text
openfraud-investigator/
├── frontend/                         # Next.js 16 (App Router), React 19, TypeScript, Tailwind 4, Vitest
│   ├── src/
│   │   ├── app/                      # routes and layouts only; pages compose features
│   │   │   ├── (app)/                # signed-in area: alerts, cases, cases/[caseId], audit, users
│   │   │   ├── login/
│   │   │   ├── auth/                 # POST /auth/login, /auth/logout (sets the httpOnly session cookie)
│   │   │   └── api/[...path]/        # API proxy: adds the token and forwards to the backend (BFF pattern)
│   │   ├── features/<name>/          # one folder per domain area, always the same shape:
│   │   │   ├── schemas.ts            #   Zod schemas + camelCase types (the wire boundary)
│   │   │   ├── api.ts                #   every HTTP call for the feature, via lib/api-client
│   │   │   ├── queries.ts            #   TanStack Query keys and hooks only
│   │   │   ├── hooks/                #   page hooks (useXPage) and feature context
│   │   │   ├── components/           #   feature components, tests next to them
│   │   │   └── <logic>/              #   pure logic when it grows (e.g. money-flow/graph/)
│   │   │   features: alerts, audit, auth, cases, copilot, money-flow, rules, transactions, users
│   │   ├── components/
│   │   │   ├── ui/                   # generic primitives (Button, Chip, Table, StatePanel, QueryError, KpiTiles…)
│   │   │   ├── layout/               # app shell: AppShell, TopNav, UserMenu, ThemeSwitch, PageHeader
│   │   │   └── theme/
│   │   ├── lib/                      # api-client, api-error, query-client, format, permissions, config
│   │   ├── server/                   # server-only helpers for route handlers (session cookie, API URL)
│   │   ├── test/                     # render helpers, API-shaped fixtures, mocks
│   │   └── proxy.ts                  # redirects signed-out page requests to /login
│   ├── public/
│   └── package.json, next.config.ts, vitest.config.mts, eslint.config.mjs
├── backend/                          # FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, uv
│   ├── app/
│   │   ├── main.py                   # create_app(): routers, error handlers, middleware
│   │   ├── core/                     # config, security, permissions, errors, logging, request_id
│   │   ├── api/                      # root router, dependencies, pagination, response envelopes
│   │   ├── db/                       # Base, engine/session, model registry, column types
│   │   ├── modules/<name>/           # router.py · schemas.py · service.py · models.py (only the files it needs)
│   │   │   modules: alerts, audit, auth, cases, detection (rules/), evidence, graph, parties,
│   │   │            transactions, users; agent/ planned for Milestone 5
│   │   └── seed/                     # synthetic casebook loader (python -m app.seed)
│   ├── migrations/                   # Alembic
│   ├── tests/
│   │   ├── api/                      # HTTP-level tests through the app (auth, permissions, envelopes)
│   │   ├── db/                       # schema, migrations, seed, session/timezone behaviour
│   │   ├── unit/                     # pure logic: detection rules, graph paths, config
│   │   ├── conftest.py               # test database and client fixtures
│   │   └── factories.py
│   └── pyproject.toml, uv.lock, alembic.ini
├── docs/
│   ├── project/                      # brief, architecture, conventions, plan, testing, security
│   ├── banking-domain/               # domain context and the synthetic casebook
│   ├── decisions/                    # ADRs
│   └── specs/                        # committed design specs (e.g. the Milestone 4 UI spec)
├── evals/                            # planned (Milestone 7): benchmark scenarios and scorers
├── docker/postgres/init/             # creates the test database on first start
├── .github/workflows/ci.yml          # backend and frontend checks
├── docker-compose.yml, .env.example
└── README.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, LICENSE
```

Endpoints that are scoped to a case (`/cases/{id}/transactions`, `/graph`, `/money-paths`) live in `cases/router.py`; the `graph`, `transactions`, `evidence` and `parties` modules therefore have no router of their own.

## Backend request flow
1. Router parses HTTP request and resolves the authenticated principal.
2. Pydantic validates the request.
3. Authorization policy checks access to the requested case/accounts.
4. Application service runs the use case.
5. Domain service performs graph traversal, rules, or investigation orchestration.
6. The service queries PostgreSQL through the request's session (there is no separate repository layer).
7. Response schema serializes the result.
8. Audit service records the relevant action.
9. Frontend renders the typed response.

## AI investigation flow
1. User submits a question for a case.
2. Server authenticates and authorizes access to the case.
3. Agent receives a minimal case context and a bounded set of available tools.
4. Model requests a tool call using a declared schema.
5. Server validates arguments, rechecks permissions, executes the tool, and returns structured results.
6. Agent may call further tools within configured limits.
7. Model drafts an answer using only returned evidence.
8. Backend validates evidence references and structured output.
9. Response includes evidence records, limitations, and investigation run ID.
10. Audit event is persisted.

## Import direction
- `api/router` may call application services.
- Application services may call domain services and repository interfaces.
- Domain logic should not import FastAPI routers or UI code.
- Persistence implementation should not import frontend code.
- Agent tools may call authorized application services; domain services must not depend on prompts.
- Avoid circular imports. Keep dependencies flowing inward toward stable domain concepts.

## Feature addition pattern
For each new feature:
1. Write a short feature spec and acceptance criteria.
2. Define API request/response contracts.
3. Implement domain logic and unit tests.
4. Add persistence/migration only if needed.
5. Add authorized service and route.
6. Add frontend feature page/components and API integration.
7. Add integration/security tests.
8. Update docs and demo data.
