# Fraud Investigation Workflow

This workflow is an educational reference for a synthetic investigation app. Real institutions use their own policies, responsibilities, systems, and regulatory timelines.

## 1. Typical conceptual stages
1. Detection: a rule, model, customer report, employee referral, or external signal creates an alert.
2. Triage: analyst checks alert quality, severity, available data, duplicates, and immediate time sensitivity.
3. Evidence collection: gather relevant transaction events, account context, related alerts, source records, and data-quality notes within authorized access.
4. Analysis: test hypotheses using deterministic rules, timelines, graph paths, and comparison against known baseline/context.
5. Decision/recommendation: analyst documents what is supported, contradicted, unknown, and what requires follow-up.
6. Escalation: route to supervisor, fraud operations, AML/compliance, disputes, legal, or law enforcement according to institution policy and applicable law.
7. Action: any hold, restriction, customer contact, dispute handling, reporting, or account action must follow authorized procedures and human approvals.
8. Closure and learning: record disposition, rationale, evidence, and outcome; use outcomes to review rule quality.

Do not treat this sequence as a mandated universal process.

## 2. Case record structure
A case should contain:
- case ID, alert references, status, owner/role, timestamps
- concise neutral summary
- facts supported by source records
- derived calculations with formulas
- hypotheses and counter-hypotheses
- missing or contradictory evidence
- graph paths with transaction IDs
- relevant prior case outcomes if authorized and reliable
- analyst notes and review history
- recommended next investigative steps
- decision/disposition and actor, when applicable
- audit events

## 3. Evidence quality
For every claim, capture:
- evidence ID and source record ID
- source system and timestamp
- event-time semantics
- whether it is a raw fact, deterministic derivation, external signal, or hypothesis
- limitations and confidence basis
- whether source records conflict or are incomplete

Do not fabricate a source record or cite an evidence ID that was not returned by an authorized tool.

## 4. Report wording
Prefer:
- “The records available in this case show…”
- “This pattern may warrant further review because…”
- “The evidence does not establish…”
- “The dataset does not contain the settlement status…”
- “A shared beneficiary is observed; common ownership is not established.”

Avoid:
- “This customer is a criminal.”
- “Fraud is confirmed” based only on an alert.
- “The money was stolen” without an authoritative finding.
- “The current balance is…” based only on transaction deltas.
- “The bank must freeze this account” without policy/legal context.

## 5. Human-in-the-loop boundary
The app may assemble evidence, explain rules, summarize records, and recommend investigative checks. It must not autonomously freeze accounts, block payments, contact customers, file regulatory reports, or make final adverse determinations.
