# Detection Rules

Detection rules turn transaction records into **alerts**: signals that something deserves an analyst's attention. An alert is never a finding of fraud, a label for a person, or a reason to act automatically. This file is the contract every rule follows and the specification of each registered rule.

Code: `backend/app/modules/detection/` (contract, facts, registry, rules) and `app/modules/alerts/` (API).

## The rule contract

Every rule implements `DetectionRule` (`detection/contract.py`) and must define:

| Field                    | Meaning                                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| `rule_id`                | Stable upper-snake ID, e.g. `RAPID_ONWARD_TRANSFER`. Never reused for a different condition.         |
| `version`                | Bumped whenever the condition or defaults change. Old alerts keep the version they were raised with. |
| `code`                   | 2–6 uppercase letters, used in alert IDs (`AL-<code>-<trigger transaction>`).                        |
| `title`, `description`   | Plain-language name and exact condition.                                                             |
| `required_fields`        | Transaction fields the rule reads.                                                                   |
| `false_positive_caveats` | Known legitimate situations that also match. Shown to analysts.                                      |
| `parameters`             | Effective configuration as strings (window, thresholds). Shown in `GET /api/v1/rules`.               |
| `evaluate(facts)`        | Returns `RuleHit`s.                                                                                  |

Rules must be:

- **Pure and deterministic.** `evaluate` reads only the `TransactionFact`s it is given: no database, clock, network, or randomness. The same facts in any order give the same hits in the same order.
- **Completed-movement only.** Only normalized status `posted` or `settled` counts as money that moved, and a transaction with a reversal record pointing at it is treated as not completed (`facts.is_completed`). Pending, failed, reversed, returned, and disputed records never satisfy a condition.
- **Currency-safe.** Amounts in different currencies are never compared or combined. Thresholds are per currency; a currency without a configured threshold is out of scope for that rule.
- **Decimal-only** for money arithmetic.
- **Explained.** Each hit carries `metrics` (the numbers that satisfied the condition, as strings) and an `explanation` sentence built only from those numbers, ending with "Signal for analyst review; not a finding of fraud."
- **Traceable.** `transaction_ids` lists every record the hit rests on.

## How detection records hits

`detection.service.run_detection(session)`:

1. Loads every transaction as a `TransactionFact`, with `reversed_by` filled from reversal records.
2. Runs each registered rule.
3. Inserts each hit as alert `AL-<code>-<trigger transaction id>`. If that alert (or another alert for the same rule and trigger) already exists, nothing changes. Re-running detection is safe.
4. Records one `detection.run` audit event per run (no actor; per-rule hit counts, rule versions, and the number of new alerts).
5. Links the alert to a case only if the trigger transaction belongs to **exactly one** case, and then adds evidence `EV-<case number>-<alert id>` (type `alert`, label `indicator`). Otherwise the alert has no case and an analyst decides.

Run it with `uv run python -m app.modules.detection`. The seed runs it automatically, so alerts are never hand-written in seed data.

## Adding a rule

1. Implement the contract in `detection/rules/<rule_name>.py`.
2. Add an instance to `RULES` in `detection/registry.py`.
3. Document it below: condition, parameters, metrics, caveats, examples.
4. Test positive cases, boundaries (exactly at each threshold), and the negatives in the contract above (non-completed statuses, reversals, mixed currencies), plus shuffled-input determinism.
5. If the alert shape needs new data, add it to `metrics` before adding columns.

---

## RAPID_ONWARD_TRANSFER (v1, code `ROT`)

**Condition.** For each completed transfer `out`, find the most recent completed transfer `inc` such that:

- `inc` was received by the party that sends `out` (`inc.destination == out.source`);
- `inc` happened at or before `out`, and no more than **window** earlier;
- same currency, and that currency has a minimum incoming amount configured;
- `inc.amount ≥ min_incoming_amount[currency]`;
- `out.amount ≥ inc.amount × min_onward_ratio`;
- `inc` is not itself a reversal record (a reversal returns funds; it is not new incoming money);
- `out` does not go to **anyone** who sent the party a completed transfer within the window (that looks like a refund, not onward movement), even if a different incoming would otherwise pair.

At most one hit per outgoing transfer. Ties at the same timestamp are ordered by transaction ID.

**Parameters (defaults).**

| Parameter             | Default                              |
| --------------------- | ------------------------------------ |
| `window`              | 30 minutes (`window_seconds = 1800`) |
| `min_onward_ratio`    | `0.50`                               |
| `min_incoming_amount` | `INR: 10000.00`                      |

**Metrics.** `elapsed_seconds`, `incoming_transaction_id`, `incoming_amount`, `outgoing_transaction_id`, `outgoing_amount`, `currency`, `window_seconds`, `min_onward_ratio`.

**False-positive caveats.** Salary, payroll, or business pass-through accounts; payment aggregators and merchants settling onward; family or household transfers in quick succession; records missing from the dataset (fees, other transfers, holds).

**Examples (synthetic casebook).**

| Case     | Records                                                                                                                      | Result                                                                                                                                                                           |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-10482 | TX-1001 ACC-001 → BEN-B INR 48,500.00; TX-1002 BEN-B → ACC-C INR 45,000.00, 5 min 28 s later                                 | Alert `AL-ROT-TX-1002`: "BEN-B received INR 48500.00 in TX-1001 and sent INR 45000.00 in TX-1002 5 minutes 28 seconds later. Signal for analyst review; not a finding of fraud." |
| FR-10483 | TX-3001 ACC-301 → BEN-301 INR 950,000.00, scheduled supplier payment                                                         | No alert: a high amount alone is not onward movement.                                                                                                                            |
| FR-10485 | TX-5001 ACC-501 → BEN-501 INR 20,000.00; TX-5003 BEN-501 → ACC-502 INR 19,000.00 ten minutes later; TX-5002 reverses TX-5001 | No alert: the incoming transfer was reversed, so it does not count as completed.                                                                                                 |
| FR-10486 | Single transfer with instruction-like description                                                                            | No alert.                                                                                                                                                                        |
