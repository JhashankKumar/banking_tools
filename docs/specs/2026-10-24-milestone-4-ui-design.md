# Milestone 4 — Investigator UI Design

Status: agreed with the project owner 2026-10-20 → 2026-10-24 in conversation; visual reference is the Figma file https://www.figma.com/design/uaops1Kg61tfOtQJbqsWlO (page 2 = styled case page, page 3 = Alerts, Audit, 3D view, Login, Users; page 1 = early wireframes, superseded).

## Intent

A polished, trustworthy investigator web app for the 1 November 2026 Hacktoberfest presentation. The audience must see an analyst open case FR-10482 and understand, at a glance and with exact evidence, how money moved (ACC-001 → BEN-B → ACC-C), why the alert fired, and what the records do **not** prove. The graph is the centrepiece and must look striking (network style, "3D look", optional true 3D view), but every number on screen must trace to a record.

## Goals

1. Screens: **Login**, **Alerts** (landing for Analyst/Supervisor), **Case page** (2D "3D look" default + 3D view), **Audit log** (Auditor), **Users** (Supervisor). A minimal **Cases list** so the "Cases" nav item works.
2. Role-aware navigation: Analyst → Alerts, Cases. Supervisor → Alerts, Cases, Users. Auditor → Audit only. Routes the role cannot use show a permission-denied state (the API also returns 403).
3. Light and dark themes with a switch in the top bar; choice persists per browser.
4. Case page = Figma page 2 layout "Option B": left context column (Why it fired, Evidence, Limitations), centre graph + timeline, right AI copilot panel; both side columns collapsible to thin rails.
5. Graph: network/force-directed, circular icon nodes (bank icon for accounts, person icon for beneficiaries), ⚑ amber badge for parties with alerts, curved directed edges, selected money path highlighted (teal, glow in dark), pending/failed edges dashed, reversal edges violet. Controls card: All nodes ↔ Case parties, All edges ↔ Money path, Re-layout; window (hours) and max hops pickers; money-path chips; zoom/fit. **3D look** (default, flat and readable) and **3D view** toggle (rotatable 3D, orbit hint, Reset camera, side columns collapse). Clicking an edge opens a detail card (tx, status, parties, amount, IST time, rail/reference, evidence ID, "Show in timeline", "Ask copilot") and highlights the timeline row; clicking a timeline row highlights the edge. For neighbourhood edges outside the case (`in_case: false`), "Show in timeline" is disabled with the note "Not one of this case's transactions" and the evidence ID shows "—". "Ask copilot" opens the copilot panel (empty state in M4). *(builder-check call)*
   - **Pickers and default selection:** the window picker (1–168 h, default 24) refetches both `/graph` and `/money-paths`; the max-hops picker (1–5, default 3) refetches only `/money-paths`. On load the **first money path is selected** (highlighted in the graph, its limitations shown in the Limitations card); choosing "All transactions" clears the selection and Limitations shows the fixed dataset sentence. *(builder-check call)*
6. Copilot panel: full visual shell (suggested questions, input, answer layout with Facts / Calculated / Not established + citation chips + "Signal for review; not a finding of fraud.") showing an **empty state** ("arrives in Milestone 5"). No model calls in M4.
7. Every data view handles loading, empty, error, and permission-denied states.

## Non-goals (M4)

- No AI calls, no case status transitions UI, no alert triage states, no real-time updates, no mobile layout beyond not breaking at ≥1280 px width (presentation is desktop).
- No synthetic-data badge anywhere in the product UI (owner decision 2026-10-24; the rule stays in data and docs).
- No PaySim or other external data (ADR #19).

## Anti-goals (would be failure even if it works)

- Any wording that implies fraud is confirmed; alerts are amber "needs review", red only for system errors.
- A number shown in the graph that differs from the API or isn't traceable to a transaction/evidence ID.
- The access token reachable by browser JavaScript (localStorage, sessionStorage, readable cookie, or client bundle).
- Frontend-only permission checks treated as security.
- Money rendered via float arithmetic.

## Constraints

- Stack: Next.js 16.4 App Router (already scaffolded in `frontend`, React 19, strict TS, Tailwind 4, Vitest), TanStack Query 5, Zod 4, React Hook Form 7 + `@hookform/resolvers`, **Reagraph 4.32** for the graph (WebGL; supports `forceDirected2d`/`forceDirected3d`, `cameraMode` `pan`/`rotate`/`orbit`, curved/dashed edges, node icons, `selections`/`actives`, custom themes). `lucide-react` icons. Fonts via `next/font`: Inter (UI), JetBrains Mono (IDs, amounts, times).
- **Binding conventions:** `docs/project/API_AND_CODE_CONVENTIONS.md` §3 (folders, single API client, Zod at the boundary with snake→camel transform, query-key factories, money stays a string formatted with `Intl.NumberFormat("en-IN")`, times shown in IST `Asia/Kolkata`, RHF + zodResolver, error classes, no token in browser JS).
- Next.js 16: request interception file is `src/proxy.ts` (the `middleware` convention is renamed). Read the bundled docs in `frontend/node_modules/next/dist/docs/` before writing Next-specific code (`frontend/AGENTS.md`).
- Backend API is the source of truth: `{data}` / `{data, page}` envelopes, `{error:{code,message,details,request_id}}` errors, OAuth2 token endpoint `POST /api/v1/auth/token` (form) returning `access_token` (30 min).
- Accessibility: WCAG 2.1 AA contrast (palette already checked), keyboard reachable controls, visible focus, status never by colour alone. The WebGL graph needs a non-canvas equivalent: the timeline table and an accessible list of nodes/edges for screen readers.

## Decided "how" (by the owner)

- Layout Option B; network graph like the owner's reference image; "3D look" default + "3D view" toggle; light + dark with switch; trust palette (tokens below); casebook data only; synthetic notice not shown in UI.

### Theme tokens (CSS variables, light / dark)

| Token | Light | Dark |
|---|---|---|
| `--bg-page` | `#F6F8FB` | `#0B1220` |
| `--bg-surface` | `#FFFFFF` | `#111A2E` |
| `--bg-surface-raised` | `#EEF2F7` | `#17223A` |
| `--border` | `#D9E0EA` | `#26344F` |
| `--text` | `#0F1B2D` | `#E6ECF5` |
| `--text-muted` | `#52607A` | `#93A1B8` |
| `--text-on-primary` | `#FFFFFF` | `#0B1220` |
| `--primary` | `#1D4ED8` | `#60A5FA` |
| `--selected` | `#0F766E` | `#2DD4BF` |
| `--review` | `#B45309` | `#FBBF24` |
| `--review-soft` | `#FEF3C7` | `#3A2A0A` |
| `--reversal` | `#6D28D9` | `#A78BFA` |
| `--counterparty` | `#5F6B7E` | `#94A3B8` |
| `--error` | `#B91C1C` | `#F87171` |
| `--success` | `#15803D` | `#4ADE80` |

## Auth design (decided here; owner approved "token never in browser JS" in the conventions)

Backend-for-frontend inside Next.js:

- `POST /auth/login` (route handler) receives username/password from the login form, calls the API token endpoint server-side, and sets an `httpOnly`, `SameSite=Lax`, `Secure` (in production), `Path=/`, 30-minute cookie holding the access token. Returns the API's error envelope unchanged on failure.
- `POST /auth/logout` clears the cookie.
- `/api/[...path]` route handler forwards GET/POST/PATCH to `${API_URL}/api/v1/...` with `Authorization: Bearer <cookie token>`, passing through status and body. Non-GET requests require same-origin (`Origin` header equals the app origin), otherwise 403.
- `src/proxy.ts` redirects unauthenticated page requests (no cookie) to `/login?next=…`. Authorisation remains the API's job.
- The current user and role come from `GET /api/auth/me`, cached by TanStack Query.

## API gaps to close in M4 (backend)

1. `GET /api/v1/cases` — paginated case list (`id`, `title`, `status`, `opened_at`, `alert_count`, `transaction_count`), permission `case:read`.
2. Audit entries need the actor's username: add `actor_username: str | null` to `AuditEventOut` (join `users`).
3. Date-range filters for alerts and audit are **not** added; the date filter chips in the Figma are dropped from M4.
4. Graph and money-path edges (`TransactionEdgeOut`) gain `rail` and `reference` so the edge detail card has real values for every edge, including neighbourhood edges. *(builder-check call)*
5. `AlertOut` gains `evidence_id: str | null` — the case evidence ID for the alert (e.g. `EV-10482-AL-ROT-TX-1002`), `null` when the alert has no case. *(builder-check call)*

## Screens (content per screen; Figma is the visual reference)

- **Login:** brand panel (logo, tagline "Trace the money. Connect the evidence. Investigate with AI.", three points: Role-based access, Every action audited, Evidence-cited AI copilot), sign-in card (username, password with show/hide, Sign in), demo-users hint naming the three usernames (never the password), footer "Every sign-in is audited". Error banner shows the API message and request ID.
- **Alerts:** title + subtitle "Signals for analyst review — not findings of fraud." KPI tiles from real data: Open alerts (alerts total), Cases (cases total), Active rules (rules count). Filters: search box (client-side over the loaded page), Rule, Case. Table: alert ID with ⚑, rule chip, party, triggered (IST), case chip with status, explanation. Row → case page. Pagination.
- **Cases list:** table of cases (ID, title, status, opened, alerts, transactions) → case page.
- **Case page:** header (breadcrumb, ID mono, title, status chip). Left: Why it fired (rule chips, explanation, metric tiles from alert `metrics`, "not a finding of fraud", rule caveats link opening the rule's caveats from `/rules`), Evidence list (the alert's `evidence_id` plus each case transaction's `evidence_id`; chips are labels that cross-highlight the graph edge and timeline row — no evidence-detail drawer in M4), Limitations (from the selected money path, else the fixed dataset limitation). Centre: graph card, timeline (from `/cases/{id}/transactions`, IST, mono amounts right-aligned, status chips, evidence chips; selected row synced with graph). Right: copilot shell.
- **Audit log (Auditor):** KPI tiles computed from the loaded page (events, denied, failed sign-ins, detection runs); filters: Action (server-side `action` param), Outcome (client-side); table: time IST, actor username (or "system"/"unknown"), action mono, resource, outcome chip (icon + colour), request ID. Pagination.
- **Users (Supervisor):** the Edit drawer's "audit note" is a static line ("Saved as audit event user.updated with the changed field names only"), not a field. *(builder-check: answered)*
- **Users (Supervisor) layout:** table (username mono + "You" chip, role chip, status, created), Create user drawer (username with pattern hint, role segmented control with permission explanation, temporary password ≥12 with inline validation, server 409/422 mapped to fields), Edit drawer (username read-only, role, Active toggle, optional password reset, audit note). Own row: role/status controls disabled with explanation (the API also returns 409).

## Left to the builder

Component breakdown, exact spacing, animation details, how the "3D look" depth effect is achieved in Reagraph (custom `renderNode` vs theme), node icon delivery (data-URI SVG vs static files), test granularity, and whether the 3D view lazy-loads Reagraph's 3D layout.
