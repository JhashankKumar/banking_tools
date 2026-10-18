# Engineering Principles — Frontend and Backend

These principles are rules for decisions and code reviews, not slogans. Prefer understandable code over cleverness.

## 1. KISS — Keep It Simple
- Choose the simplest design that satisfies current, documented requirements.
- Prefer a modular monolith and clear functions over premature microservices or elaborate abstractions.
- Avoid clever one-liners when explicit code is easier to review.
- A new library must solve a real problem better than a small, maintainable implementation.

## 2. DRY — Don't Repeat Yourself
- Do not duplicate business rules, validation, authorization, or transaction calculations.
- Create an abstraction when the same stable concept is repeated and the abstraction makes the intent clearer.
- Do not force superficially similar code into one generic abstraction when the underlying rules differ.
- Frontend form validation improves usability; backend validation remains authoritative.
- Shared TypeScript/Python types are not automatically shareable across languages. Define API contracts clearly and generate clients only if useful.

## 3. YAGNI — You Aren't Gonna Need It
- Implement only features required for the current milestone or explicitly accepted requirements.
- Do not build plugin marketplaces, multi-tenant enterprise controls, event buses, generic workflow engines, or model routing frameworks in advance.
- Keep extension points at real boundaries (e.g. model provider) rather than abstracting every class.

## 4. SOLID, applied pragmatically
- Single Responsibility: each module should have one clear reason to change.
- Open/Closed: extend rules through small rule implementations or configuration without editing unrelated flows.
- Liskov: implementations of an interface must preserve its contract.
- Interface Segregation: use small interfaces such as `ModelProvider` instead of one huge service interface.
- Dependency Inversion: business logic depends on interfaces/ports where external dependencies vary (database, model provider), not directly on vendor-specific implementations.
Do not introduce an interface for every function just to satisfy SOLID.

## 5. High cohesion, low coupling
- Keep code that changes for the same reason together.
- Domain modules should expose small, meaningful public functions.
- Avoid circular imports and cross-layer imports.
- A feature should not require editing many unrelated files.
- Keep database access, business rules, HTTP serialization, UI rendering, and LLM prompting in separate layers.

## 6. Make the code flow like a sentence
Use a predictable end-to-end flow:

Frontend page/component
→ typed API client
→ FastAPI route/controller
→ request schema validation
→ application/use-case service
→ domain logic (rules/graph)
→ repository/data access
→ PostgreSQL
→ response schema
→ frontend rendering.

For AI investigation:

User question
→ authenticated request
→ case/resource authorization
→ investigation use case
→ allowlisted tool registry
→ each tool validates arguments and checks authorization
→ deterministic services retrieve evidence
→ model composes a structured explanation
→ evidence references are validated
→ response + audit event
→ UI displays answer and source records.

Routes/controllers should be thin. They coordinate, but do not contain business algorithms or giant SQL queries. Business logic should be testable without starting the web server or calling an LLM.

## 7. Explicit beats implicit
- Use descriptive names: `find_money_paths`, not `process_data`.
- Use small functions with one purpose.
- Use explicit error types and documented API error shapes.
- Avoid hidden global mutable state and import-time side effects.
- Use configuration via typed settings; validate required settings at startup.
- Avoid boolean arguments whose meaning is unclear; use named options or distinct functions when appropriate.

## 8. Type and data contracts
- TypeScript strict mode; avoid `any` unless justified and isolated.
- Python type hints for public functions and domain data.
- Pydantic schemas at API boundaries.
- Use enums or constrained types for statuses and currencies where appropriate.
- Never trust client-provided account access, role, evidence ID, or case ownership.
- Validate data at boundaries, then rely on clear internal invariants.

## 9. Errors and observability
- Handle expected errors explicitly: not found, invalid input, permission denied, conflict, model unavailable, tool timeout.
- Do not silently swallow exceptions or return fake success.
- Do not expose stack traces, secrets, internal SQL, or sensitive records to users.
- Use structured logs with correlation/request IDs.
- Avoid logging raw prompts or customer-like data by default.
- Model unavailability must not break deterministic alert and graph features.

## 10. Frontend principles
- Organize by feature/domain, not only by technical type.
- Keep pages as composition layers; move complex behavior into feature hooks/services.
- Separate server state (TanStack Query) from local UI state.
- Use reusable components when they express a shared design concept, not merely because markup repeats once.
- Use semantic HTML, keyboard accessibility, focus states, and clear loading/error/empty states.
- Keep API calls out of low-level presentation components.
- Never hardcode demo transaction data in production UI components; load seeded data through APIs.
- Keep graph rendering separate from graph calculation.
- Use Zod for UI form validation but repeat authoritative validation on the backend.

## 11. Backend principles
- Organize by feature/domain: alerts, cases, transactions, graph, detection, evidence, agent, audit.
- Keep routes thin; application services coordinate use cases.
- Repositories encapsulate persistence where this meaningfully separates domain logic from SQLAlchemy.
- Do not add repository wrappers that merely forward every ORM call without benefit.
- Use database transactions for multi-record changes.
- Add pagination and bounded query parameters to list/graph endpoints.
- Make time windows, hop limits, and result caps explicit.
- Keep money arithmetic decimal-safe.
- Use migrations for schema changes; never rely on manual production schema edits.

## 12. Extensibility without overengineering
- Add a new fraud rule by implementing a documented rule contract and registering it.
- Add a model provider by implementing `ModelProvider`.
- Add a new AI tool by declaring its schema, permission requirement, result schema, and audit behavior.
- Add a new feature in its own module with tests and API/UI integration.
- Do not make the whole application generic just because future features are possible.

## 13. Security is an invariant
- Authorization must be enforced on every backend resource access and every tool call.
- Never use the LLM to enforce permissions.
- Never execute model-generated SQL, shell commands, or arbitrary code.
- Treat retrieved notes and transaction descriptions as untrusted data.
- Limit tool count, arguments, execution time, recursion/turns, output size, and graph traversal.
- Audit security-relevant actions.
- No real customer data in demos, fixtures, logs, or public issues.

## 14. Testability
- Keep deterministic core logic independent of network and model calls.
- Inject model providers and repositories where that makes tests reliable.
- Use fixed clocks or explicit timestamps in tests; avoid fragile tests based on current time.
- Test behavior and invariants rather than private implementation details.
- Test both allowed and denied authorization cases.
- Add regression tests for every bug fixed.

## 15. Definition of done for a feature
A feature is complete only when:
1. Requirements and edge cases are documented.
2. Backend validation and authorization are enforced.
3. Core logic has unit tests.
4. API contract and error cases are tested.
5. UI has loading, empty, error, and success states where applicable.
6. Audit behavior is covered for security-relevant actions.
7. Documentation and examples are updated.
8. Lint/type/test/build checks pass.
9. No secrets or real customer data are introduced.

## 16. Code review checklist
- Can a new contributor follow the happy path in a few minutes?
- Is there a simpler implementation?
- Is logic duplicated?
- Is any abstraction premature?
- Are permissions checked server-side?
- Can outputs be traced to evidence?
- Are amount/time semantics correct?
- Are failures visible and safe?
- Are tests meaningful?
