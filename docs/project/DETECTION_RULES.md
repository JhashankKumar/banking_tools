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
- **Currency-safe.** Amounts in different currencies are compared only through a conversion **recorded on the transaction** (`converted_amount`, `converted_currency`, `fx_rate`: the amount and rate the source system applied). Rules never look up, estimate or invent an exchange rate; without a recorded conversion, different currencies are not compared. Thresholds are per currency; a currency without a configured threshold is out of scope for that rule.
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

## RAPID_ONWARD_TRANSFER (v2, code `ROT`)

**Condition.** For each completed transfer `out`, find the most recent completed transfer `inc` such that:

- `inc` was received by the party that sends `out` (`inc.destination == out.source`);
- `inc` happened at or before `out`, and no more than **window** earlier;
- both amounts can be put in one currency C: the same currency, or one of the two records carries a recorded conversion into the other's currency (that converted amount is used);
- C has a minimum incoming amount configured;
- `inc` in C ≥ `min_incoming_amount[C]`;
- `out` in C ≥ `inc` in C × `min_onward_ratio`;
- `inc` is not itself a reversal record (a reversal returns funds; it is not new incoming money);
- `out` does not go to **anyone** who sent the party a completed transfer within the window (that looks like a refund, not onward movement), even if a different incoming would otherwise pair.

At most one hit per outgoing transfer. Ties at the same timestamp are ordered by transaction ID.

**Parameters (defaults).**

| Parameter             | Default                              |
| --------------------- | ------------------------------------ |
| `window`              | 30 minutes (`window_seconds = 1800`) |
| `min_onward_ratio`    | `0.50`                               |
| `min_incoming_amount` | `INR: 10000.00`                      |

**Metrics.** `elapsed_seconds`, `incoming_transaction_id`, `incoming_amount`, `outgoing_transaction_id`, `outgoing_amount`, `currency` (C, the currency compared in), `window_seconds`, `min_onward_ratio`. When a recorded conversion was used, also `incoming_currency`, `outgoing_currency`, `converted_transaction_id`, `converted_amount` (in C) and `fx_rate`; the explanation then names them, e.g. "sent USD 1000.00 (INR 83450.00 at the recorded rate 83.45)".

**Version history.** v1 compared same-currency transfers only. v2 (2026-11-01) adds recorded conversions; same-currency results are unchanged. Alerts keep the version they were raised with.

**False-positive caveats.** Salary, payroll, or business pass-through accounts; payment aggregators and merchants settling onward; family or household transfers in quick succession; records missing from the dataset (fees, other transfers, holds).

**Examples (synthetic casebook).**

| Case     | Records                                                                                                                      | Result                                                                                                                                                                           |
| -------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FR-10482 | TX-1001 ACC-001 → BEN-B INR 48,500.00; TX-1002 BEN-B → ACC-C INR 45,000.00, 5 min 28 s later                                 | Alert `AL-ROT-TX-1002`: "BEN-B received INR 48500.00 in TX-1001 and sent INR 45000.00 in TX-1002 5 minutes 28 seconds later. Signal for analyst review; not a finding of fraud." |
| FR-10483 | TX-3001 ACC-301 → BEN-301 INR 950,000.00, scheduled supplier payment                                                         | No alert: a high amount alone is not onward movement.                                                                                                                            |
| FR-10485 | TX-5001 ACC-501 → BEN-501 INR 20,000.00; TX-5003 BEN-501 → ACC-502 INR 19,000.00 ten minutes later; TX-5002 reverses TX-5001 | No alert: the incoming transfer was reversed, so it does not count as completed.                                                                                                 |
| FR-10486 | Single transfer with instruction-like description                                                                            | No alert.                                                                                                                                                                        |
| FR-10490 | INR 2,00,000 in, then five transfers of INR 38,000–40,000                                                                    | No ROT alert: no single onward transfer reaches 50 %. FAN_OUT_SPLIT covers this shape (`AL-FOS-TX-9006`).                                                                        |
| FR-10493 | TX-9301 → BEN-932 INR 85,000.00; TX-9302 BEN-932 → ACC-933 USD 1,000.00 recorded as INR 83,450.00 at 83.45, 8 min later      | Alert `AL-ROT-TX-9302` through the recorded conversion (98 % sent on).                                                                                                           |

---

## FAN_OUT_SPLIT (v1, code `FOS`)

**Condition.** For each completed transfer `inc` received by a party P that is not itself a reversal record and is at least `min_incoming_amount` in its currency C, walk P's completed outgoing transfers made at or after `inc` and no more than **window** later, in time order (ties by transaction ID). Skip reversal records, transfers back to `inc`'s sender (refund-shaped), and transfers that cannot be put in C (C itself, or a conversion into C recorded on the transfer). The first outgoing transfer at which **both** at least `min_transfers` transfers are counted **and** their total reaches `inc` × `min_onward_share` is the trigger.

At most one hit per incoming transfer, and at most one per trigger: when two incoming transfers would reach the threshold at the same outgoing transfer, only the earlier incoming raises the alert.

**Parameters (defaults).**

| Parameter             | Default                              |
| --------------------- | ------------------------------------ |
| `window`              | 30 minutes (`window_seconds = 1800`) |
| `min_incoming_amount` | `INR: 50000.00`                      |
| `min_transfers`       | `3`                                  |
| `min_onward_share`    | `0.80`                               |

**Metrics.** `incoming_transaction_id`, `incoming_amount`, `currency` (C), `outgoing_count`, `outgoing_total` (in C), `onward_share` (total ÷ incoming, rounded down to 2 dp), `elapsed_seconds` (incoming to trigger), `window_seconds`, `min_transfers`, `min_onward_share`. `transaction_ids` holds the incoming transfer and every counted outgoing transfer.

**Version history.** v1 (2026-11-01).

**False-positive caveats.** Payroll or vendor batch payments made right after funding arrives; a business distributing funds to its own accounts; loan or grant disbursements paid on to several suppliers; records missing from the dataset.

**Examples (synthetic casebook).**

| Case     | Records                                                                          | Result                                                                                             |
| -------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| FR-10490 | INR 2,00,000 in (TX-9001), then five transfers of INR 38,000–40,000 in 12 m 30 s | Alert `AL-FOS-TX-9006`: INR 1,95,000 (97 %) sent on in 5 transfers. Silent for ROT.                |
| FR-10494 | INR 5,00,000 client payment, then five salaries totalling INR 4,04,000 in 20 min | Alert `AL-FOS-TX-9406` (80 %). A benign look-alike: the payroll caveat is what the analyst weighs. |
| FR-10491 | Each hop sends on one transfer                                                   | No FOS alert: fewer than three outgoing transfers.                                                 |

---

## FAN_IN_COLLECT (v1, code `FIC`)

**Condition.** For each completed outgoing transfer `out` from a party P that is not a reversal record, compare in `out`'s currency C. Count P's completed incoming transfers made at or before `out` and no more than **window** earlier, that are not reversal records and can be put in C (C itself, or a conversion into C recorded on the incoming transfer). If any of them came from `out`'s recipient, skip `out` (refund-shaped, as ROT does). Hit when the incoming transfers come from at least `min_payers` different senders, total at least `min_total_incoming[C]`, and `out` ≥ total × `min_onward_ratio`. At most one hit per outgoing transfer.

**Parameters (defaults).**

| Parameter            | Default                              |
| -------------------- | ------------------------------------ |
| `window`             | 30 minutes (`window_seconds = 1800`) |
| `min_payers`         | `3`                                  |
| `min_total_incoming` | `INR: 25000.00`                      |
| `min_onward_ratio`   | `0.50`                               |

**Metrics.** `payer_count`, `incoming_count`, `incoming_total`, `outgoing_transaction_id`, `outgoing_amount`, `currency` (C), `onward_share` (outgoing ÷ total, rounded down to 2 dp), `elapsed_seconds` (first counted incoming to `out`), `window_seconds`, `min_payers`, `min_onward_ratio`. `transaction_ids` holds every counted incoming transfer and `out`.

**Version history.** v1 (2026-11-01).

**False-positive caveats.** Merchants and payment aggregators settling collected payments; group collections such as shared rent, events or savings groups; business receivables swept to an operating account; records missing from the dataset.

**Examples (synthetic casebook).**

| Case     | Records                                                                             | Result                                                                                            |
| -------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| FR-10489 | Five payers send INR 71,000 in 18 min; INR 68,000 sent on 24 m 12 s after the first | Alert `AL-FIC-TX-8906` linking all five payments. ROT's `AL-ROT-TX-8906` pairs only the last one. |
| FR-10495 | Six UPI payments (INR 31,000) to a merchant; settled 3 h later                      | No alert: the settlement is outside the window. A benign look-alike.                              |

---

## CIRCULAR_FLOW (v1, code `CIR`)

**Condition.** Three completed transfers A → B, B → C, C → A between three different parties, in that order (by time, ties by transaction ID), all in one currency with a configured threshold, with the closing transfer no more than **window** after the first. The first transfer is at least `min_start_amount`, and the closing transfer at least first × `min_return_ratio`. Reversal records never count as a hop. When several cycles close on the same transfer, the one with the latest first hop (then the latest middle hop) is reported. At most one hit per closing transfer.

Not covered in v1: two-hop round trips (A → B → A, which look like refunds), cycles longer than three hops, and cycles across currencies.

**Parameters (defaults).**

| Parameter          | Default                             |
| ------------------ | ----------------------------------- |
| `window`           | 24 hours (`window_seconds = 86400`) |
| `min_start_amount` | `INR: 10000.00`                     |
| `min_return_ratio` | `0.50`                              |
| `hops`             | `3` (fixed in v1)                   |

**Metrics.** `hops`, `start_transaction_id`, `start_amount`, `returned_amount`, `currency`, `return_ratio` (returned ÷ start, rounded down to 2 dp), `elapsed_seconds` (first hop to closing transfer), `window_seconds`, `min_return_ratio`. `transaction_ids` holds the three hops in order.

**Version history.** v1 (2026-11-01).

**False-positive caveats.** Cash or treasury sweeps between one company's own accounts; a loan repaid through an intermediary; family members pooling and returning funds; records missing from the dataset.

**Examples (synthetic casebook).**

| Case     | Records                                                                                       | Result                                                                     |
| -------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| FR-10484 | ACC-401 → BEN-402 INR 30,000; BEN-402 → ACC-403 INR 29,000; ACC-403 → ACC-401 INR 28,000, 5 h | Alert `AL-CIR-TX-4003` (93 % returned). Silent for ROT (hops hours apart). |
