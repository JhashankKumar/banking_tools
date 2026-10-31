# Incremental Implementation Plan

Build a vertical slice that works end-to-end before broadening the system.

## Milestone 0 — Repository and developer experience
- Create repository structure and documentation.
- Add license, contribution, code of conduct, security policy, environment example.
- Add format/lint/test commands and CI.
- Add Docker Compose for PostgreSQL and application services only when the initial app is ready.
Acceptance: a contributor can follow setup instructions and run the smallest checks.

## Milestone 1 — Synthetic domain and API
- Define schema and migrations.
- Generate deterministic synthetic accounts, transactions, alerts, and case FR-10482.
- Implement health, case detail, and transaction endpoints.
- Add database-backed users, login, role-based permission checks, Supervisor user management, and audit events (moved from Milestone 6; see ADR 0001 #15).
Acceptance: seeded data can be retrieved via API by an authorized role; unauthenticated and unauthorized requests are denied; no real customer data.

## Milestone 2 — Deterministic detection
- Define a documented rule contract.
- Add a few transparent rules with explanations and source IDs.
- Test positive and negative scenarios.
Acceptance: every alert indicates why it fired and references source records.

## Milestone 3 — Money-flow graph
- Build a directed graph from authorized transaction records.
- Implement bounded, time-windowed traversal.
- Return path edges with source IDs, amount, currency, timestamp, status.
Acceptance: FR-10482 path is deterministic and covered by tests.

## Milestone 4 — UI vertical slice
- Dashboard/alert list, case view, graph, evidence panel.
- Typed API client and clear loading/empty/error states.
Acceptance: a user can open FR-10482 and inspect the two-hop path.

Done 2026-10-24 (spec `docs/specs/2026-10-24-milestone-4-ui-design.md`):
- Screens: Login, Alerts, Cases list, Case page (Why it fired, Evidence, Limitations, money-flow graph with "3D look" / "3D view", edge detail card, timeline, copilot shell), Audit log (Auditor), Users (Supervisor). Light and dark themes.
- Auth through a Next.js backend-for-frontend (`/auth/*`, `/api/*`); the token stays in an `httpOnly` cookie.
- Backend additions: `GET /api/v1/cases`, `actor_username` on audit events, `rail`/`reference` on graph edges, `evidence_id` on alerts.
- Verified on a fresh database in a real browser for all three roles; Lighthouse accessibility 100 on Login, Alerts, Cases, Case page, Audit log and Users; keyboard-only path to a graph edge via the accessible list.

## Milestone 5 — AI copilot
- Add model provider interface and OpenRouter adapter (open-weight models only).
- Add bounded tool registry and investigation endpoint.
- Add evidence-linked response schema and citations validation.
Acceptance: model explains the deterministic path without changing its facts; fake provider tests run without an OpenRouter key or network access.

Done 2026-10-24 (spec `docs/specs/2026-10-24-milestone-5-ai-copilot-design.md`):
- Copilot: `ModelProvider` + OpenRouter adapter + fake provider; seven case-bound, ID-only tools; bounded harness (6 tool calls, one repair turn); JSON answers in four sections with server-verified citations and value checks; customer-information questions declined and audited; limits from the run log (20/hour per user, US$2/day overall).
- Chats: several per case, remembered, private to their author; supervisors read others' chats read-only.
- Case notes: saved from copilot answers (edited first), versioned, submitted for review; supervisors return or approve (keep open / escalate / close with a listed reason); four-eyes rule; one note under review per case (database-enforced); full status history.
- Seed adds FR-10488 (incomplete settlement status).
- Pending the owner's key: the live model comparison (`python -m app.modules.copilot.compare`) and a live-answer browser check.

## Milestone 6 — Security and adversarial tests
- Test prompt injection, unauthorized access, invalid tools, output grounding, audit logging.
Acceptance: all defined negative tests pass; limitations documented.

Done 2026-10-30 (spec `docs/specs/2026-10-30-milestones-6-7-safety-and-benchmark-design.md`):
- Safety checks: 33 scripted attacks in 7 groups (prompt injection, customer information, access control, tool abuse, grounding, limits, audit and secrets) run against the real defences inside a rolled-back transaction; only the model is scripted. Each check was seen to fail with its defence switched off.
- In-app **Safety checks** page (`/safety`, Supervisor and Auditor): run on demand, results per check, one `safety.checks.run` audit row per run.
- `backend/tests/security/`: the catalogue as tests, plus every API route without a token, the auditor on case routes, the analyst on safety and users, and error bodies without internals.
- `docs/project/SECURITY_LIMITATIONS.md`: what is not covered, with the measured customer-information filter misses (17 of 24 paraphrases).

## Milestone 7 — Benchmark and open-source polish
- Add scenario families and reproducible evaluation.
- Publish actual measured results and caveats.
- Improve README screenshots/demo, issue templates, contribution guide, first issues.
Acceptance: a new contributor can reproduce the demo and evaluation from scratch.

Done 2026-10-30/31:
- `python -m app.benchmark`: 15 seeded synthetic scenario families labelled from the rule's contract; rule, path and answer-validator scores; published in `docs/evaluation/results/` with caveats; CI checks they reproduce.
- README screenshots and sections, `docs/DEMO.md`, issue and PR templates, updated CONTRIBUTING, drafted `FIRST_ISSUES.md`.
- Pending the owner's key: the live-model section (`--live`) and the M5 model comparison.

## Work protocol for a coding agent
At the start of each milestone:
1. Inspect current files and git status.
2. Summarize current architecture and gaps.
3. Propose a small plan with files to create/change.
4. Implement only the current milestone.
5. Run tests, lint, type checks, and build relevant to the changes.
6. Report exact commands and results honestly.
7. List assumptions, known issues, and next milestone.
Do not silently skip failed checks or claim a command passed if it was not run.
