# Architecture and Folder Structure

## Architecture choice
Start with a **modular monolith**: one API deployment with clearly separated domain modules. It is easier to run, test, contribute to, and deploy than a set of microservices. Keep module boundaries so later extraction is possible if justified.

## Repository layout

```text
openfraud-investigator/
├── apps/
│   └── web/
│       ├── src/
│       │   ├── app/                     # Next.js routes and layouts
│       │   ├── features/
│       │   │   ├── dashboard/
│       │   │   ├── alerts/
│       │   │   ├── cases/
│       │   │   ├── transactions/
│       │   │   ├── money-flow/
│       │   │   ├── investigation/
│       │   │   └── audit/
│       │   ├── components/
│       │   │   ├── ui/                  # Generic primitives only
│       │   │   └── layout/
│       │   ├── lib/
│       │   │   ├── api-client.ts
│       │   │   ├── query-client.ts
│       │   │   └── config.ts
│       │   ├── hooks/
│       │   ├── types/                   # Shared UI-only types
│       │   └── test/
│       ├── public/
│       ├── package.json
│       └── ...
├── services/
│   └── api/
│       ├── app/
│       │   ├── main.py                  # App creation and startup
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   ├── logging.py
│       │   │   ├── errors.py
│       │   │   └── security.py
│       │   ├── api/
│       │   │   ├── router.py
│       │   │   └── dependencies.py
│       │   ├── db/
│       │   │   ├── session.py
│       │   │   └── base.py
│       │   ├── modules/
│       │   │   ├── alerts/
│       │   │   │   ├── router.py
│       │   │   │   ├── schemas.py
│       │   │   │   ├── models.py
│       │   │   │   ├── repository.py
│       │   │   │   ├── service.py
│       │   │   │   └── tests/
│       │   │   ├── cases/
│       │   │   ├── transactions/
│       │   │   ├── evidence/
│       │   │   ├── graph/
│       │   │   ├── detection/
│       │   │   ├── investigation/
│       │   │   ├── agent/
│       │   │   └── audit/
│       │   └── tests/
│       ├── migrations/                  # Alembic
│       ├── pyproject.toml
│       └── ...
├── packages/
│   └── api-contracts/                   # Optional generated OpenAPI client/types
├── data/
│   ├── generator/
│   ├── scenarios/
│   └── README.md                        # Dataset provenance and synthetic-only notice
├── evals/
│   ├── scenarios/
│   ├── test_detection.py
│   ├── test_graph_discovery.py
│   ├── test_grounding.py
│   ├── test_prompt_injection.py
│   └── test_authorization.py
├── docs/
│   ├── architecture.md
│   ├── problem-validation.md
│   ├── threat-model.md
│   ├── benchmark-results.md
│   └── decisions/
│       └── 0001-modular-monolith.md
├── scripts/
│   ├── seed_demo_data.py
│   └── verify_environment.py
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
└── SECURITY.md
```

This is a target layout, not a requirement to create every file on day one. Begin with the folders needed for the current milestone and expand incrementally.

## Backend request flow
1. Router parses HTTP request and resolves the authenticated principal.
2. Pydantic validates the request.
3. Authorization policy checks access to the requested case/accounts.
4. Application service runs the use case.
5. Domain service performs graph traversal, rules, or investigation orchestration.
6. Repository loads required records from PostgreSQL.
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
