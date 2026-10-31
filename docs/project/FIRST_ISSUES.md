# First issues

Drafts for the maintainer to file; not yet on GitHub. Each is sized for a first contribution and has a test that shows it is done. Labels to use: `good first issue`, plus the area.

## 1. Catch more reworded customer-information questions

- **Context:** the keyword filter missed 17 of 24 measured paraphrases ([SECURITY_LIMITATIONS.md](SECURITY_LIMITATIONS.md#customer-information-filter)).
- **Acceptance:** each listed miss gets a test in `backend/tests/unit/copilot/test_answer.py` asserting `is_customer_info_request` is true; fraud-signal questions ("Where did the money go?", "Why did the alert fire?") stay false; the limitations document is updated with the new measurement.
- **Files:** `backend/app/modules/copilot/answer.py`.

## 2. Add a "structuring" detection rule

- **Context:** only `RAPID_ONWARD_TRANSFER` exists. Several incoming transfers just under a threshold within a short time is a common signal.
- **Acceptance:** a rule following `docs/project/DETECTION_RULES.md` with positive and negative tests, a benchmark family for it, and results regenerated.
- **Files:** `backend/app/modules/detection/rules/`, `backend/app/benchmark/families.py`.

## 3. Per-IP and per-user rate limiting on sign-in

- **Context:** sign-in has no throttling ([SECURITY_LIMITATIONS.md](SECURITY_LIMITATIONS.md#no-per-ip-rate-limiting)).
- **Acceptance:** repeated failed sign-ins from one IP or for one username return 429 with `Retry-After`; an audited event; tests in `backend/tests/api/test_auth.py`.
- **Files:** `backend/app/modules/auth/`.

## 4. Per-user daily copilot budget

- **Context:** the daily budget is shared, so one user can use it up for everyone.
- **Acceptance:** a per-user budget setting enforced in `check_limits`, with a test, and a safety check in the Limits group.
- **Files:** `backend/app/modules/copilot/limits.py`, `backend/app/modules/safety/checks/limits.py`.

## 5. Pass the remaining run time into each model call

- **Context:** the run deadline is checked between calls, so a run can last about 120 s ([Run time bounds](SECURITY_LIMITATIONS.md#run-time-bounds)).
- **Acceptance:** each OpenRouter call's timeout is `min(30 s, time left)`; a harness test with a fake clock.
- **Files:** `backend/app/modules/copilot/harness.py`, `openrouter.py`.

## 6. Mask record IDs in answer text that are not citable

- **Context:** unknown IDs in answer text now trigger a repair turn; the UI could also show which ID was rejected.
- **Acceptance:** the repair reason is shown in the copilot panel's error state for an answer that failed twice; Vitest test.
- **Files:** `frontend/src/features/copilot/`.

## 7. Safety check for a second planted-text location

- **Context:** INJ-01 covers transaction text; evidence references and alert explanations are wrapped too but not attacked in a check.
- **Acceptance:** a check that plants text in an evidence `reference` (inside the run, rolled back) and asserts it reaches the model only wrapped; seen to fail with the wrapper removed.
- **Files:** `backend/app/modules/safety/checks/injection.py`.

## 8. PR-AUC baseline

- **Context:** TESTING_AND_EVALUATION.md lists PR-AUC "if implemented"; it is not.
- **Acceptance:** a simple scored baseline (e.g. onward share × speed) evaluated on the benchmark families with PR-AUC in RESULTS.md, clearly labelled as a baseline on synthetic data.
- **Files:** `backend/app/benchmark/`.
