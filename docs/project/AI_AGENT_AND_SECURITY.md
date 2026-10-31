# AI Agent, Security, and Trust Boundaries

## Design rule
The LLM is an explanation and tool-selection layer, not the source of truth and not the authorization authority.

## Model provider
Use OpenRouter as the hosted model gateway, calling open-weight models only. It provides an OpenAI-compatible chat completions API, but each model can differ in tool-call behavior and supported features.

Define a small `ModelProvider` contract for:
- sending messages and declared tool definitions to the model,
- receiving text or structured tool calls,
- returning provider/model metadata and token usage where available,
- handling timeouts, rate limits, malformed responses, and provider errors.

Implementation guidance:
- Put OpenRouter-specific code in `OpenRouterModelProvider`; use the OpenAI Python SDK with base URL `https://openrouter.ai/api/v1` or HTTPX.
- Read `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` from validated backend settings.
- Never expose the API key in frontend code, browser requests, logs, error messages, or committed files.
- Keep model-specific code out of domain services. The application should depend on the provider interface.
- Support a deterministic fake provider so tests do not require a live API key or incur model costs.
- Test the exact chosen model's tool-call support and malformed-tool-call behavior before relying on it.

## OpenRouter privacy and cost
- Send only synthetic data in this public demo.
- Review both OpenRouter's current privacy settings and the selected downstream provider's policy before sending any sensitive information.
- Consider the supported `provider.data_collection="deny"` and/or `provider.zdr=true` request controls where appropriate. These restrict routing to eligible endpoints; they do not make the request local or guarantee that every other system in your application stores nothing.
- Rate-limit investigation requests per authenticated user and per client IP; return HTTP 429 with a retry hint. Enforce a daily token/cost budget so a public demo cannot exhaust the API key.
- Set reasonable request/token limits, timeouts, and application-level usage controls. Track usage metadata and cost without logging raw sensitive prompts by default.

## Tool contract
Each tool must declare:
- stable tool name and purpose,
- typed input schema,
- typed output schema,
- required permission/scope,
- maximum result size and execution time,
- audit event behavior,
- safe error behavior.

Initial allowlisted tools:
- `get_case_summary`
- `get_transactions`
- `find_money_paths`
- `get_alert_details`
- `get_evidence_records`
- `get_prior_case_findings` (only if synthetic records and authorization permit it)

No arbitrary SQL, shell execution, Python execution, unrestricted HTTP fetching, or dynamic tool creation from model output.

## Bounded agent loop
- Configure a maximum number of tool calls/turns.
- Validate every tool name and argument.
- Recheck the authenticated principal's authorization for every call.
- Apply query timeouts and result-size limits.
- Reject unknown tools and malformed arguments.
- Do not let the model change user roles or authorization scope.
- Return a controlled error if the model is unavailable; deterministic endpoints must remain usable.
- Store a minimal run record and useful audit metadata without storing sensitive raw prompts by default.

## Evidence grounding
- Tool results include stable evidence IDs and source record IDs.
- The model can cite only IDs supplied by tools.
- Backend validates that each cited evidence ID exists in this investigation's allowed evidence set.
- UI allows users to inspect each cited record.
- Distinguish observed record, derived calculation, hypothesis, and unknown.
- A model-generated narrative must not change amounts, timestamps, statuses, or path topology.
- For arithmetic such as time differences, calculate in deterministic code.

## Threat model
Threats include:
1. Prompt injection embedded in transaction descriptions or notes.
2. Unauthorized case/account lookup.
3. Hallucinated transactions, evidence, or conclusions.
4. Tool-call loops and excessive resource use.
5. Malformed model output.
6. Secrets leaked in logs or model prompts.
7. Unsafe dependency or model license.
8. User treating a risk indicator as proof of guilt.

## Required mitigations
- Treat all retrieved free text as untrusted data.
- Keep system instructions separate from retrieved content.
- Authorization enforced by backend services, not prompt wording.
- Evidence ID validation and structured output validation.
- Tool allowlist and argument schemas.
- Rate/size/time limits and maximum agent turns.
- Safe error responses and redacted structured logging.
- Synthetic-only public fixtures.
- Security tests for every threat above.
- Human review required for consequential conclusions or actions.

## How each threat is tested
Run from the Safety checks page (`/safety`) or `cd backend && uv run pytest -q tests/security`. Known gaps: [SECURITY_LIMITATIONS.md](SECURITY_LIMITATIONS.md).

| Threat (above) | Checks |
|---|---|
| 1. Prompt injection in records | INJ-01 … INJ-05 |
| 2. Unauthorized case/account lookup | ACC-01 … ACC-07, INJ-02, CUS-01 … CUS-09, `test_http_negatives.py` |
| 3. Hallucinated transactions, evidence or conclusions | GRD-01 … GRD-04, INJ-03, INJ-04 |
| 4. Tool-call loops and excessive resource use | TOOL-03, TOOL-04, LIM-01, LIM-02 |
| 5. Malformed model output | TOOL-01, TOOL-02, INJ-05, the repair turn in GRD-02/03 |
| 6. Secrets leaked in logs or prompts | AUD-01, AUD-02, `test_error_bodies_hide_internals` |
| 7. Unsafe dependency or model license | Not tested here: dependency review is manual (see `TECH_STACK.md`) |
| 8. Risk indicator treated as proof of guilt | INJ-03 (conclusion-wording guard); human review of every note (ACC-04) |

## Demo roles
- Analyst: permitted synthetic cases and investigation tools.
- Supervisor: review/approve demo case status transitions; create, update, and deactivate users.
- Auditor: read permitted audit events.
These are demonstration roles only. Make the demo authentication limitations explicit. Do not claim production compliance or certification.
