# Benchmark results

This is a **regression benchmark** on scenario families written by this project. It is **not real-world** performance and says nothing about how the rule would do on real bank data. The rule was **not tuned** on these variants: its parameters are the defaults in `rapid_onward_transfer.py`. Labels follow the rule's written contract (see `docs/evaluation/README.md`), so a score of 1.0 means the code does what its contract says, not that it catches fraud.

Reproduce: `cd backend && uv run python -m app.benchmark --seed 20261101 --variants 50` (then compare `metrics` in `results.json`; only `meta` may differ).

Generated 2026-11-01 by the code in the commit that contains this file · Python 3.12.3 · seed 20261101 · 50 variants per family · 800 variants in all.

## Detection rule (RAPID_ONWARD_TRANSFER v2)

Window 1800 s, minimum onward share 0.50, minimum incoming INR 10000.00.

Overall, per variant: precision 1.0000, recall 1.0000 (TP 300, FP 0, FN 0, TN 500). Per (incoming, onward) pair: TP 460, FP 0, FN 0.

| Family | Label | TP | FP | FN | TN | Precision | Recall | Pairs TP/FP/FN |
|---|---|---|---|---|---|---|---|---|
| rapid_onward | positive | 50 | 0 | 0 | 0 | 1.0000 | 1.0000 | 50/0/0 |
| two_hop | positive, 2 pairs | 50 | 0 | 0 | 0 | 1.0000 | 1.0000 | 100/0/0 |
| multi_hop | positive, every qualifying pair; paths truncated at 3 hops | 50 | 0 | 0 | 0 | 1.0000 | 1.0000 | 110/0/0 |
| circular | positive, 2 pairs; one cycle path | 50 | 0 | 0 | 0 | 1.0000 | 1.0000 | 100/0/0 |
| duplicate_incoming | positive; pair is the most recent incoming | 50 | 0 | 0 | 0 | 1.0000 | 1.0000 | 50/0/0 |
| onward_after_window | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| incoming_below_threshold | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| onward_below_ratio | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| return_to_sender | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| reversed_incoming | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| pending_incoming | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| failed_incoming | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| currency_mismatch | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| onward_before_incoming | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| benign_high_value | negative | 0 | 0 | 0 | 50 | n/a | n/a | 0/0/0 |
| converted_onward | positive | 50 | 0 | 0 | 0 | 1.0000 | 1.0000 | 50/0/0 |

## Money paths

Path finder defaults: 24 h window, 3 hops, completed hops only. Overall: precision 1.0000, recall 1.0000 over 200 variants.

| Family | Variants | TP | FP | FN | Precision | Recall |
|---|---|---|---|---|---|---|
| rapid_onward | 50 | 50 | 0 | 0 | 1.0000 | 1.0000 |
| two_hop | 50 | 50 | 0 | 0 | 1.0000 | 1.0000 |
| multi_hop | 50 | 50 | 0 | 0 | 1.0000 | 1.0000 |
| circular | 50 | 50 | 0 | 0 | 1.0000 | 1.0000 |

## Answer grounding (validator)

For each variant with a money path, one faithful answer built from its records and one tampered copy per kind. The validator should pass the first and catch the rest.

Faithful answers: 200, wrongly rejected 0 (rate 0.0000).

| Tamper | Answers | Caught | Rate |
|---|---|---|---|
| fabricated_citation | 200 | 200 | 1.0000 |
| changed_value | 200 | 200 | 1.0000 |
| unknown_id | 200 | 200 | 1.0000 |
| conclusion_wording | 200 | 200 | 1.0000 |

## Live model

Not run (no key). Run with `--live --models <ids> --cap-usd 1.00` once `OPENROUTER_API_KEY` is set.

## Not measured

PR-AUC (no ML baseline is implemented), real-world detection rates, analyst time saved. Safety checks are not part of this benchmark: run them on the Safety checks page or with `uv run pytest -q tests/security`.
