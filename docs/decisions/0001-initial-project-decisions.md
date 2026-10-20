# ADR 0001 — Initial project decisions

- Status: Accepted
- Date: 2026-10-18

These decisions resolve open questions and inconsistencies in `docs/project/` and `docs/banking-domain/`. Where older wording conflicts, this record wins.

## Decisions

1. **Architecture:** modular monolith — one FastAPI backend with domain modules, one Next.js frontend, PostgreSQL.
2. **LLM provider:** OpenRouter only, calling open-weight models only (no proprietary models). Model ID is configured with `OPENROUTER_MODEL`. Ollama is out of scope. Tests use a deterministic fake provider.
3. **Rate limits:** investigation endpoints are rate-limited per user and per client IP (HTTP 429), with a daily token/cost budget.
4. **Authorization:** role-based access control only (Analyst, Supervisor, Auditor). No per-case assignment.
5. **Evidence:** its own table with stable `EV-…` IDs pointing to source records. AI citations must reference `EV-…` IDs that belong to the case.
6. **Time:** stored in UTC; displayed in IST (Asia/Kolkata).
7. **Entities:** accounts and beneficiaries are separate tables.
8. **Money paths:** pending and reversed transactions are included and labeled with their status; paths containing non-final edges are flagged.
9. **Docs location:** knowledge bases moved from `.claude/` to `docs/project/` and `docs/banking-domain/` so contributors can see them.
10. **Tooling:** `uv` for the Python backend, `pnpm` for the frontend.
11. **Users:** stored and managed in PostgreSQL (`users` table: ID, username, password hash, role, active flag, timestamps). Users log in against the database; demo users are seeded. Passwords are hashed (never stored or logged in plain text).
12. **Agent harness:** custom bounded harness in the `agent` module (tool registry, loop with turn limit, argument and permission checks, evidence validation). No agent framework.
13. **User management:** Supervisors create, update, and deactivate users. No separate Admin role.
14. **MCP:** not in scope. May be revisited after the Hacktoberfest presentation.
15. **Auth moved to Milestone 1** (decided 2026-10-20): login and role-based permission checks ship with the first data endpoints, so no endpoint is ever unprotected. Milestone 6 keeps the adversarial/security test suite.
16. **API and code conventions** (decided 2026-10-20): `{ "data" }` / `{ "data", "page" }` success envelope, `{ "error": { code, message, details, request_id } }` errors with a code registry, snake_case wire with camelCase UI models converted at a Zod boundary, money as two-decimal strings, UTC `Z` timestamps. Full rules: `docs/project/API_AND_CODE_CONVENTIONS.md`.
17. **Graph traversal** (decided 2026-10-20): money paths use a small hand-written, time-respecting, bounded depth-first search. NetworkX is not used: it does not support time-ordered paths and adds an untyped dependency. Revisit only with measured need (rustworkx, or a graph database).
18. **MVP graph view** (decided 2026-10-20): one case's neighbourhood within the time window (case parties plus every transaction touching them), rendered in the UI with React Flow + ELK layered layout. No whole-network view in the MVP.

## Timeline

The product should be demo-ready before 1 November 2026 (Hacktoberfest presentation). Model usage, use cases, and the open-source roadmap are discussed there.

Must-ship: Milestones 0–5. Milestone 6 partial. Milestone 7 stretch.

## Open

- Exact open-weight model, chosen by Claude after tool-calling tests (no user preference).
