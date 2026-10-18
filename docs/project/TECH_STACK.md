# Recommended Technology Stack

Choose stable, mutually compatible versions at implementation time. Pin dependencies and document tested versions; do not blindly select canary releases.

## Frontend
- Next.js + React + TypeScript: application, routes, reusable UI.
- Tailwind CSS: styling.
- `@xyflow/react` (React Flow): interactive transaction graph.
- TanStack Query: server-state fetching, caching, retries, invalidation.
- React Hook Form + Zod: forms and client-side validation.
- Vitest + React Testing Library: component and frontend tests.

Frontend responsibilities:
- Display data and collect investigator intent.
- Render graph nodes and transaction edges returned by the backend.
- Show loading, empty, error, permission-denied, and partial-evidence states.
- Never independently decide whether a transaction path exists or whether activity is fraudulent.
- Never treat frontend-only role checks as security controls.

## Backend
- Python + FastAPI: REST API.
- Pydantic: request/response validation and structured model outputs.
- SQLAlchemy 2.x: persistence and query layer.
- Alembic: schema migrations.
- Uvicorn: ASGI server.
- HTTPX: API integration tests.
- pytest: unit and integration tests.
- Ruff and a Python type checker: linting and static checks.

## Data
- PostgreSQL: source of truth for structured records.
- `NUMERIC`/decimal arithmetic for monetary amounts; never binary floats for money.
- UTC timestamps in storage; render local time at the UI boundary.
- Foreign keys, unique constraints, indexes, and migrations.
- Synthetic dataset only.

## Graph analysis
- NetworkX: directed graph analysis for the MVP.
- Use bounded traversal, time windows, maximum hop counts, and result limits.
- Keep transaction identifiers and evidence metadata on each edge.
- Benchmark before introducing Neo4j or another graph database.

## Detection
- Deterministic Python rules first.
- scikit-learn baseline later, after synthetic labels and data splits are defined.
- Report precision, recall, PR-AUC, false positives, and evaluation limitations.
- Do not claim model quality from a tiny or leaked dataset.

## AI
- OpenRouter as the initial hosted model gateway, using its OpenAI-compatible chat completions API.
- Use the OpenAI Python SDK with `base_url="https://openrouter.ai/api/v1"`, or a small HTTPX adapter if that better fits the project. Keep provider-specific request details inside the adapter.
- Configure `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` via environment variables. Never expose the key to the browser or commit it.
- Hide model-specific logic behind a `ModelProvider` interface so the app can switch provider without changing domain logic.
- Use open-weight models only (open-weight model IDs via OpenRouter); no proprietary models. Check each model artifact licence.
- Select a model only after testing structured tool calling, argument reliability, latency, cost, context limits, and license terms. Tool-calling behavior varies by model.
- Build a small custom, bounded agent harness with an allowlisted tool registry.
- Consider LangGraph only if explicit multi-step state management warrants the dependency.
- Validate every structured output with Pydantic and verify all evidence IDs against retrieved records.
- Use synthetic data only. OpenRouter sends prompts to the selected inference provider; review OpenRouter and the selected provider's data policies. Where appropriate, use supported request controls such as `provider.data_collection="deny"` or `provider.zdr=true`, understanding that these only constrain eligible routing and do not keep data local.
- Check exact model and tokenizer licenses, model limits, pricing, provider data retention, and tool-call reliability.

## Delivery and quality
- Docker Compose for local repeatability.
- GitHub Actions for lint, type checks, tests, and build.
- `.env.example` with placeholders only.
- Apache-2.0 or MIT for project code after license review.
- `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and architecture documentation.

## Avoid in MVP
Do not add Redis, Kafka, Kubernetes, a vector database, a separate graph database, or multiple backend services until a concrete requirement and measurement justify them.
