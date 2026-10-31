# Testing and Evaluation Strategy

## Test layers
1. Unit tests: money arithmetic, rule evaluation, graph traversal, evidence validation, policy decisions.
2. API tests: validation, pagination, error responses, database behavior, authorization.
3. UI tests: filters, graph rendering, loading/error states, evidence navigation.
4. End-to-end tests: seed synthetic data, open case, trace path, ask AI, inspect citations.
5. Adversarial tests: prompt injection, malformed tool calls, unauthorized access, fabricated evidence IDs.
6. Reproducible evaluation: fixed synthetic scenarios and a versioned scoring script.

## Synthetic scenarios
Include at least:
- direct transfer with a triggered rule,
- two-hop and multi-hop transfer path,
- circular transfer pattern,
- rapid movement through several entities,
- innocent high-value transaction,
- duplicate transaction,
- pending/failed/reversed transaction,
- multiple currencies (ensure no invalid summation),
- missing destination or incomplete history,
- conflicting timestamps or status,
- prompt injection in a transaction description,
- analyst requests a case outside their scope,
- model attempts unknown tool or malformed arguments.

## Metrics to report
Measured results: [docs/evaluation/results/RESULTS.md](../evaluation/results/RESULTS.md) (how: [docs/evaluation/README.md](../evaluation/README.md)). Adversarial suite: Safety checks page and `backend/tests/security/`.

- Rule precision and recall on labeled synthetic scenarios.
- PR-AUC for an ML baseline if implemented and labels support it (not implemented).
- Graph path recall/precision against known generated paths.
- Evidence citation validity rate.
- Unsupported factual claim rate in a curated evaluation set.
- Unauthorized access attempts denied.
- Audit event completeness for defined audited actions.
- Latency and token/model cost for the tested hardware/model.
- Human investigation task completion time only if measured through a documented protocol.

## Targets versus results
You may define goals such as zero unauthorized disclosures in the adversarial suite and a high evidence-grounding rate, but label them as targets until measured. Never invent benchmark results or claim a synthetic score represents real-world bank performance.

## Avoid leakage
- Generate scenarios with deterministic seeds.
- Split evaluation by scenario family or time, not merely random rows when related transactions can leak across splits.
- Keep generation logic and labels documented.
- Report sample size, model version, parameters, hardware, limitations, and exact commands.
- Do not tune and report on the same held-out test cases without disclosing it.

## Definition of a useful benchmark
A new contributor should be able to:
1. install dependencies,
2. generate or load the synthetic dataset,
3. run the tests,
4. run the evaluation command,
5. reproduce the documented metrics,
6. understand limitations from the report.
