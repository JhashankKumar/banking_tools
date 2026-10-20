# API and Code Conventions — Backend and Frontend

How data moves through OpenFraud Investigator: how the backend receives and validates input, how it shapes responses and errors, and how the frontend calls the API, validates what comes back, and shows it. Every new endpoint, feature module, and page follows this file. If code and this file disagree, fix one of them in the same change.

Status: **Accepted 2026-10-20.** Milestone 1 code predates parts of this file; see [Migration of existing code](#migration-of-existing-code).

---

## 1. The wire contract

### 1.1 Success responses

Every JSON endpoint under `/api/v1` returns an envelope. The HTTP status code says whether the call succeeded; the body carries data.

Single resource:

```json
{ "data": { "id": "FR-10482", "status": "open" } }
```

List (always paginated):

```json
{
  "data": [{ "id": "TX-1001" }, { "id": "TX-1002" }],
  "page": { "total": 2, "limit": 50, "offset": 0 }
}
```

Action with nothing to return: `204 No Content`, empty body.

Rules:

- `data` is always present on 2xx responses (object or array), never `""`.
- There is no `success` boolean: status `2xx` means success. One source of truth.
- Lists never return a bare array and never a second list shape.

**Documented exceptions** (they follow external standards, not the envelope):

| Endpoint                                         | Shape                                            | Why                                                                                                                                |
| ------------------------------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| `POST /api/v1/auth/token` (success)              | `{ "access_token", "token_type", "expires_in" }` | OAuth2 password flow (RFC 6749); the `/docs` Authorize button and standard clients expect it. Errors still use the error envelope. |
| `GET /api/v1/health`, `GET /api/v1/health/ready` | `{ "status": "ok" \| "unavailable" }`            | Read by load balancers and probes, not by the UI.                                                                                  |

### 1.2 Error responses

Every error (4xx and 5xx) has one shape:

```json
{
  "error": {
    "code": "CASE_NOT_FOUND",
    "message": "Case not found",
    "details": [],
    "request_id": "3f1c…"
  }
}
```

- `code`: machine-readable, `DOMAIN_REASON` in upper snake case. The frontend branches on `code`, never on `message`.
- `message`: short, safe to show a user, no internal detail (no SQL, stack traces, file paths, library names, or secrets).
- `details`: field-level problems for validation errors, otherwise `[]`. Each item is `{ "field": "body.password", "message": "String should have at least 12 characters" }`. **Never include the submitted value** (it may be a password or other sensitive input).
- `request_id`: the same value as the `X-Request-ID` response header, so a user can quote it and an operator can find the logs.

### 1.3 Error code registry

Codes are stable once released. Add new codes here in the same change that introduces them.

| Code                       | HTTP | Meaning                                                                                       |
| -------------------------- | ---- | --------------------------------------------------------------------------------------------- |
| `VALIDATION_FAILED`        | 422  | Request body, query, or path failed validation; see `details`.                                |
| `AUTH_NOT_AUTHENTICATED`   | 401  | Missing, invalid, or expired token, or the user is inactive. Sets `WWW-Authenticate: Bearer`. |
| `AUTH_INVALID_CREDENTIALS` | 401  | Login failed. Same message for unknown user, wrong password, or inactive user.                |
| `AUTH_FORBIDDEN`           | 403  | Authenticated, but the role lacks the permission. Never reveals whether the resource exists.  |
| `NOT_FOUND`                | 404  | No such route.                                                                                |
| `METHOD_NOT_ALLOWED`       | 405  | Route exists, method does not.                                                                |
| `CASE_NOT_FOUND`           | 404  |                                                                                               |
| `ALERT_NOT_FOUND`          | 404  |                                                                                               |
| `USER_NOT_FOUND`           | 404  |                                                                                               |
| `USER_USERNAME_TAKEN`      | 409  |                                                                                               |
| `USER_SELF_LOCKOUT`        | 409  | A Supervisor tried to deactivate or demote their own account.                                 |
| `RATE_LIMITED`             | 429  | Sets `Retry-After`. (Milestone 5+)                                                            |
| `MODEL_UNAVAILABLE`        | 503  | The LLM provider failed or timed out; deterministic features still work. (Milestone 5)        |
| `SERVICE_UNAVAILABLE`      | 503  | A dependency (e.g. database) is down.                                                         |
| `INTERNAL_ERROR`           | 500  | Anything unexpected. Message is always the generic "Something went wrong".                    |

### 1.4 Field formats

| Kind                   | Wire format                                                        | Example                                   |
| ---------------------- | ------------------------------------------------------------------ | ----------------------------------------- |
| Field names            | `snake_case`                                                       | `occurred_at`                             |
| Money                  | string with exactly two decimals, plus a separate `currency` field | `"amount": "48500.00", "currency": "INR"` |
| Timestamps             | ISO 8601 UTC with `Z`                                              | `"2026-09-15T04:32:14Z"`                  |
| Business IDs           | stable prefixed strings                                            | `FR-10482`, `TX-1001`, `EV-10482-TX-1001` |
| User IDs               | UUID string                                                        | `"7c9e…"`                                 |
| Enums                  | lowercase strings                                                  | `"settled"`, `"analyst"`                  |
| Absent optional values | `null` (not `""`, not omitted)                                     | `"description": null`                     |

Never send money as a JSON number. Never add amounts in different currencies.

### 1.5 URLs

- Versioned prefix `/api/v1`.
- Resource nouns, plural, kebab-case: `/cases/{case_id}/transactions`, `/audit-logs`. No verb paths like `/get_case/`.
- Actions that are not CRUD use a sub-resource noun: `POST /cases/{case_id}/investigations`.
- Pagination: `?limit=` (1–100, default 50) and `?offset=` (≥ 0).

---

## 2. Backend structure (`services/api`)

### 2.1 Layers and what each may do

```text
app/
├── main.py                 create_app(): middleware, exception handlers, routers
├── core/                   config, security, permissions, errors, request_id, logging
├── api/                    root router, shared dependencies, envelope + pagination helpers
├── db/                     Base, engine/session, model registry
├── modules/<domain>/
│   ├── router.py           HTTP only: parse, depend on auth, call service, wrap response
│   ├── schemas.py          Pydantic request/response models for this domain
│   ├── service.py          use cases: business rules, transactions, audit; raises AppError
│   ├── repository.py       only when queries are complex enough to deserve a name
│   └── models.py           SQLAlchemy entities
└── seed/                   synthetic data
```

| Layer        | May                                                                                             | Must not                                                                                                      |
| ------------ | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `router.py`  | read request, declare permission dependency, call one service function, return a response model | contain business rules, raw SQL, `try/except` that turns domain errors into HTTP (the global handler does it) |
| `service.py` | apply rules, query via the session, write audit events, raise `AppError` subclasses             | import FastAPI, return HTTP responses, return `(result, "error")` tuples                                      |
| `schemas.py` | define request/response shapes, field formats                                                   | contain database access                                                                                       |
| `models.py`  | define tables and constraints                                                                   | be returned from a router                                                                                     |

### 2.2 Data objects: names and flow

```text
HTTP JSON ──▶ XCreate / XUpdate / query params (Pydantic, validated at the edge)
          ──▶ service(session, actor, data, request_id)
          ──▶ SQLAlchemy model (persistence)
          ──▶ XOut (Pydantic, from_attributes or built explicitly)
          ──▶ envelope { "data": XOut } / { "data": [XOut], "page": … }
```

Naming per domain:

| Purpose             | Name                                                                | Example          |
| ------------------- | ------------------------------------------------------------------- | ---------------- |
| Create body         | `<Thing>Create`                                                     | `UserCreate`     |
| Partial update body | `<Thing>Update` (all fields optional; only fields sent are applied) | `UserUpdate`     |
| Response item       | `<Thing>Out`                                                        | `TransactionOut` |
| Nested reference    | `<Thing>Ref`                                                        | `PartyRef`       |

Shared generic types live in `app/api/responses.py`:

- `DataResponse[T]` → `{ "data": T }`
- `PageResponse[T]` → `{ "data": list[T], "page": PageMeta }`
- `ErrorResponse` → `{ "error": ErrorBody }`

Routers declare `response_model` with these so the OpenAPI schema matches reality.

### 2.3 Receiving data

- Every body, query, and path parameter is typed by Pydantic or FastAPI parameter types. No reading `request.json()` or untyped dicts.
- Constrain at the edge: lengths, patterns, ranges, enums (`Field(min_length=12)`, `Query(ge=1, le=100)`).
- `extra="forbid"` on request models, so unknown fields are a 422 rather than silently ignored (prevents mass-assignment surprises).
- Free text from data sources (transaction descriptions, notes) is stored and returned verbatim as data and is never interpreted as instructions.
- Never trust client-supplied role, user ID, case ownership, or evidence IDs; derive them from the token and the database.

### 2.4 Errors in code

`app/core/errors.py`:

```python
class AppError(Exception):
    status: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "Something went wrong"
```

Each domain defines subclasses next to its service (`CaseNotFoundError(AppError)` with `status=404, code="CASE_NOT_FOUND"`). Services `raise`; `create_app()` registers exactly three handlers:

1. `AppError` → its status, code, message.
2. `RequestValidationError` → 422 `VALIDATION_FAILED` with `details` (location + message only, input values dropped).
3. `Exception` → 500 `INTERNAL_ERROR`, logged with stack trace server-side, generic message to the client.

Starlette `HTTPException` (404 for unknown routes, 405) is mapped to the same envelope.

### 2.5 Cross-cutting rules

- **Request ID:** set by middleware, stored in a `contextvar`, added to every log record by a logging filter, echoed in `X-Request-ID`, included in every error body and audit event.
- **Logging:** structured, one line per event, `logging.getLogger(__name__)`. Never log request/response bodies, passwords, tokens, `Authorization` headers, or record contents. Tests assert this for auth endpoints.
- **Audit:** written by services through `app.modules.audit.service.record(...)`, never with secrets. On error paths that must keep the audit row, commit it before raising.
- **Transactions:** one session per request; it commits before the response is sent (`Depends(get_session, scope="function")`).
- **Config:** only through typed `Settings`. No `os.getenv` in modules. Security controls are switched by typed settings with secure defaults, never by commenting code out.
- **Outbound calls** (LLM provider): distinguish "the provider failed" (`MODEL_UNAVAILABLE`, retryable) from "the provider answered no/invalid" (validation failure). Timeouts on every call.

### 2.6 Backend tests

- API behaviour is tested through `TestClient` against the real test database, not by calling route functions with mocked requests.
- Each endpoint has tests for: success shape, 401, 403 (with audit row), 404, 422 (with `details`), and pagination bounds.
- File names by topic (`test_cases_api.py`), never numbered (`test_views7.py`). Regression tests describe the behaviour in their name.
- No `sys.modules` stubbing; inject dependencies (`dependency_overrides`, fake model provider).

---

## 3. Frontend structure (`apps/web`)

### 3.1 Folders

```text
src/
├── app/                           Next.js routes: thin; compose feature components
│   └── (investigator)/cases/[caseId]/page.tsx
├── features/<feature>/            e.g. cases, transactions, money-flow, audit, auth
│   ├── api.ts                     endpoint functions: call apiClient, parse with schemas
│   ├── schemas.ts                 Zod schemas for this feature's API responses/requests
│   ├── queries.ts                 query-key factory + useQuery/useMutation hooks
│   ├── hooks/use<Page>.ts         one view-model hook per page (data, state, actions)
│   ├── components/                feature components (+ co-located *.test.tsx)
│   └── index.ts                   public exports of the feature
├── components/ui/                 design primitives (Button, Table, Alert, Skeleton…)
├── components/layout/
├── lib/
│   ├── api-client.ts              the only HTTP client
│   ├── api-error.ts               ApiError class + userMessage()
│   ├── query-client.ts            QueryClient factory with project defaults
│   ├── format.ts                  money, date/time, IDs — the only formatters
│   └── config.ts                  typed public config
└── test/                          test utilities (render with providers, fixtures)
```

Features import from `lib/` and `components/`; features do not import each other's internals (only their `index.ts`).

### 3.2 The API client

`lib/api-client.ts` is the single place that talks HTTP:

- Built on `fetch`; base URL from typed config.
- Every request has a timeout (`AbortSignal.timeout`) and forwards the caller's `signal` (TanStack Query passes one), so navigating away cancels requests.
- Unwraps the envelope: returns `data` (and `page` for lists).
- Turns every non-2xx response into `ApiError` (a real `class ApiError extends Error` with `status`, `code`, `message`, `details`, `requestId`). Network failures and timeouts become `ApiError` with code `NETWORK_ERROR`.
- Never logs response bodies.

`lib/api-error.ts` exports `userMessage(error, fallback)`: shows the server `message` for known `ApiError` codes, the fallback for anything else.

### 3.3 Validating what comes back

The backend is trusted but verified. Every response is parsed with Zod (v4) at the feature boundary, then converted to the UI model:

```ts
// features/transactions/schemas.ts
export const transactionSchema = z
  .object({
    id: z.string(),
    amount: z.string().regex(/^\d+\.\d{2}$/),
    currency: z.string().length(3),
    occurred_at: z.iso.datetime(),
    status: transactionStatusSchema,
    description: z.string().nullable(),
  })
  .transform((t) => ({
    id: t.id,
    amount: t.amount, // stays a string; formatting is lib/format.ts
    currency: t.currency,
    occurredAt: t.occurred_at,
    status: t.status,
    description: t.description,
  }));

export type Transaction = z.output<typeof transactionSchema>;
```

- Wire objects are `snake_case`; UI models are `camelCase`. The `.transform()` in the schema is the only place that converts.
- Types come from `z.output<…>`, not hand-written duplicates.
- A schema mismatch is an error (shown as "Unexpected response"), not silently cast.
- Money stays a string end to end. Display with `formatMoney(amount, currency)` (`Intl.NumberFormat("en-IN", { style: "currency", currency })`). Never `parseFloat` money for arithmetic; the UI does not do money arithmetic.
- Times stay ISO UTC strings in models. Display with `formatDateTime(iso)` in IST (`Asia/Kolkata`), with the zone shown.

### 3.4 Server state and client state

- Server state: TanStack Query only. Client state: `useState` and small contexts. No global store unless a real need appears.
- `lib/query-client.ts` exports `makeQueryClient()` with defaults: `staleTime: 30_000`; `retry`: never on 4xx, up to 2 times on network/5xx; `refetchOnWindowFocus: false`. Created once per browser session inside the provider (never a module-level singleton shared across server requests).
- Query keys come from one factory per feature:

  ```ts
  export const caseKeys = {
    all: ["cases"] as const,
    detail: (caseId: string) => [...caseKeys.all, "detail", caseId] as const,
    transactions: (caseId: string, page: PageParams) =>
      [...caseKeys.all, "transactions", caseId, page] as const,
  };
  ```

  Keys contain case IDs and pagination only — never account numbers, names, or other sensitive values.

- Mutations invalidate through the same factory (`invalidateQueries({ queryKey: caseKeys.detail(id) })`).
- Global handling via `QueryCache`/`MutationCache` `onError`: `AUTH_NOT_AUTHENTICATED` → redirect to login. Everything else is shown where it happened. Route-level `error.tsx` boundaries catch the rest.

### 3.5 Auth in the browser

- The access token is never stored in `localStorage` or `sessionStorage` and never readable by browser JavaScript.
- Next.js server code (route handlers) holds the token in an `httpOnly`, `Secure`, `SameSite=Lax` cookie and forwards it to the API. Decided in detail in Milestone 4.
- Role-based UI hiding is a convenience only; the API enforces permissions.

### 3.6 Forms

- React Hook Form with `zodResolver`; the same Zod schema produces the form type.
- Client validation is for usability; the API is authoritative. Map a 422 `details` list onto fields with `setError`.

### 3.7 Components and pages

- Pages are composition only; data and state come from the page's `use<Page>` hook.
- Every data view handles **loading, empty, error, success**, and **permission denied** (403) where applicable.
- Use `components/ui` primitives rather than raw interactive elements, so focus, labels, and keyboard behaviour are consistent. Every icon-only control has an accessible name; status is never shown by colour alone.
- Component files are PascalCase with named exports; props types live with the component.

### 3.8 Frontend tests

- Co-located `*.test.ts(x)`; Vitest runs with `TZ=UTC`.
- Test each feature's `api.ts` + `schemas.ts` with fixture JSON shaped exactly like the backend envelope (including invalid shapes).
- Hook tests use a fresh QueryClient per test.
- Mock at the HTTP boundary (fetch), not by mocking our own modules.

---

## 4. Comments and public-repo hygiene

- Comments explain _why_, briefly. No multi-paragraph essays in infrastructure code.
- Never mention private systems, internal repositories, clients, or institutions in code, comments, or docs. This repository is public.
- No secrets in code, tests, fixtures, or CI except clearly labelled throwaway values for ephemeral test services.

---

## Migration of existing code

Done 2026-10-20: Milestone 1 endpoints use the envelopes, `AppError` subclasses with registry codes, the three global handlers (plus a request-ID middleware safety net for unexpected errors), `extra="forbid"` request models, validation `details` without input values, and request IDs on every log record. Contract tests: `services/api/tests/test_api_contract.py`.
