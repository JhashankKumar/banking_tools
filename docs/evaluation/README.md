# Evaluation

A reproducible benchmark of the deterministic parts of OpenFraud Investigator: the detection rule, the money-path finder, and the copilot's answer validator. It uses generated synthetic data only, no database and no model.

Published results: [results/RESULTS.md](results/RESULTS.md) (tables) and [results/results.json](results/results.json) (every number).

## Reproduce

```bash
cd backend
uv sync
uv run python -m app.benchmark --seed 20261101 --variants 50
```

This rewrites `docs/evaluation/results/`. With the same seed and variant count, the `parameters`, `variants`, `metrics` and `live` blocks of `results.json` are identical on every run and machine; only `meta` (date, Python version) changes. `--out <dir>` writes somewhere else. `uv run pytest -q tests/unit/benchmark` checks the generator, scorers and command.

Live model section (optional, costs money, needs `OPENROUTER_API_KEY` and the seeded database):

```bash
uv run python -m app.benchmark --seed 20261101 --variants 50 \
  --live --models openai/gpt-oss-120b,qwen/qwen3-235b-a22b-2507 --cap-usd 1.00
```

It asks each model the fixed questions in `app/modules/copilot/compare.py` through the real harness and reports answered/failed counts, cost and latency. Without a key the report says "not run (no key)".

## What is generated

`backend/app/benchmark/families.py` builds each variant in memory as `TransactionFact` records, from a random generator seeded with `"<seed>:<family>"` (adding a family never changes another family's data). IDs are synthetic: transactions `TX-8…`, parties `ACC-B…` / `BEN-B…`. Amounts are INR unless the family says otherwise. Near-threshold variants are included: in each threshold family variant 0 sits one step past its boundary (1 s past the window, INR 0.01 below the threshold or the 50 % share); in rapid_onward, variant 0 is exactly at the window, variant 1 exactly at the threshold and variant 2 exactly at 50 %.

| Family | What it is | Label |
|---|---|---|
| rapid_onward | Received, then sent on within the window | positive |
| two_hop | A → B → C → D, each hop qualifying | positive, 2 pairs |
| multi_hop | Chains of 3 hops, or 4 in one variant of five | positive, every qualifying pair; expected path truncated to 3 hops |
| circular | S → M → N → S | positive, 2 pairs; one cycle path |
| duplicate_incoming | Same incoming recorded twice, then sent on | positive; the pair is the most recent incoming |
| onward_after_window | Sent on 1–600 s after the 30-minute window | negative |
| incoming_below_threshold | Incoming below INR 10,000.00 | negative |
| onward_below_ratio | Onward below 50 % of incoming | negative |
| return_to_sender | Sent back to the sender | negative |
| reversed_incoming | Incoming later undone by a reversal record | negative |
| pending_incoming | Incoming still pending | negative |
| failed_incoming | Incoming failed | negative |
| currency_mismatch | INR in, USD out, no recorded conversion | negative |
| onward_before_incoming | Onward timestamp earlier than the incoming one | negative |
| benign_high_value | One large transfer, nothing sent on | negative |
| converted_onward | INR in, USD out; the transfer records its INR cost and rate (variant 0 exactly at 50 %) | positive |

## How labels are set

From the rule's written contract (`RapidOnwardTransfer.description`), never from what the rule outputs: completed transfers only, same currency or a conversion recorded on one of the two transfers, onward within the window (inclusive), onward at least the minimum share, incoming at least the per-currency threshold, transfers back to the sender ignored. Where the contract is silent we decided: a duplicated incoming record still alerts (the pair is the most recent incoming); money sent before it arrived is not "sent onward"; in a chain every qualifying hop is its own pair; the path finder's 3-hop limit truncates longer chains.

## What is scored

- **Rule:** per variant (should it alert?) as TP/FP/FN/TN with precision and recall, and per (incoming, onward) pair. Rates are "n/a" when there is nothing to divide by (a family with no positives has no recall).
- **Paths:** for path families, paths found from the variant's first transfer with the copilot tool defaults (24 h, 3 hops, completed hops only) against the generated path.
- **Grounding:** for each variant with a path, one faithful answer built from its records and four tampered copies (invented citation, changed amount, unknown transaction ID, "fraud is confirmed" wording), run through the production validator. Faithful answers should pass; tampered ones should be caught.

## Caveats

The families are written by this project to match the rule's contract, so this is a regression benchmark: a score of 1.0 means the code does what its contract says. It is not real-world performance, the rule's parameters were not tuned on these variants, and nothing here measures how often a real model misbehaves (see the live section and [SECURITY_LIMITATIONS.md](../project/SECURITY_LIMITATIONS.md)). PR-AUC is not reported: no ML baseline is implemented. The safety checks are separate: run them on the Safety checks page or with `uv run pytest -q tests/security`.
