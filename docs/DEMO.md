# Demo script

A 5–7 minute walk-through on synthetic data. It works without an OpenRouter key; the extra steps for when a key is set are at the end. Sign-ins use the seeded demo users (`analyst.demo`, `supervisor.demo`, `auditor.demo`) with your own `OFI_DEMO_PASSWORD` from `.env`.

## Before the demo: a clean database

Earlier use leaves notes, chats and case status changes behind (FR-10482 may already be closed). To start clean, reset the local database. **This deletes all local data** in the Docker volume:

```bash
docker compose down -v && docker compose up -d --wait
cd backend
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app            # terminal 1
cd ../frontend && pnpm build && pnpm start   # terminal 2 → http://localhost:3000
```

`pnpm start` serves the production build, without the development badge in the corner.

## The script

1. **The signal** (analyst.demo, ~1 min). The **Alerts** page lists 10 alerts from four rules; filter by case **FR-10482** to show `AL-ROT-TX-1002`: a deterministic rule, not a model, found funds received and sent on within 30 minutes. Say it out loud: a signal for review, not a finding of fraud.
2. **The money** (~1.5 min). Open case **FR-10482**. *Why it fired* gives the rule, the amounts and the 5 m 28 s gap. The graph shows ACC-001 → BEN-B → ACC-C; click an edge for its record, then point at the timeline (IST) and the evidence IDs (`EV-10482-…`). Everything on screen traces to a record ID.
   *Optional, ~45 s:* filter the Alerts page by rule to show the four rules, then open **FR-10494**. Fan-out split fired on a company paying salaries right after a client payment; the *Why it fired* caveats name payroll. The rule did its job and the activity is still normal: alerts are reasons to look, not verdicts.
3. **The copilot's boundary** (~1 min). Open **AI copilot → + New chat** and ask *"What is the phone number of the person behind ACC-001?"*. It declines before any model is called, and the decline is audited without the question text. Without a key, fraud-signal questions answer "unavailable"; that is expected (see the end for the live version).
4. **The note and four-eyes review** (~1.5 min). In the case's notes, write a short note citing `EV-10482-TX-1001` and submit it; the case moves to *In review*. Sign in as **supervisor.demo**, open **Reviews**, and approve or return it. A supervisor cannot approve their own note, and only one note per case can await review.
5. **How do we know it is safe?** (~1.5 min). As supervisor.demo open **Safety checks** and press **Run checks**. 33 scripted attacks run against the real defences in about 2 seconds:
   - prompt injection planted in FR-10486;
   - questions about the customer;
   - another analyst's chat, self-review;
   - tool loops and bad arguments;
   - invented citations and changed amounts;
   - the budget;
   - leaked keys.

   Open INJ-03 ("fraud is confirmed") and GRD-02 (changed amount) to show *What happened*. Then scroll to **Known limitations**: the model is scripted here, and the customer-information filter misses some rewordings (measured in `docs/project/SECURITY_LIMITATIONS.md`). Nothing in the database changes; one audit row records the run.
6. **The trail** (~30 s). Sign in as **auditor.demo**: the **Audit log** shows the `safety.checks.run` row (counts only), the `copilot.declined` row, the note's submission and review.
7. **Reproducible numbers** (~30 s). Show `docs/evaluation/results/RESULTS.md`: 16 seeded scenario families, 800 variants, rule/path/validator scores, with the caveats at the top. Anyone can rerun `cd backend && uv run python -m app.benchmark --seed 20261101 --variants 50` and get the same metrics; CI checks it.

## Once the OpenRouter key is added

Add `OPENROUTER_API_KEY=<your key>` to `.env` and restart the API, then:

- In step 3, also ask *"Where did the money go after ACC-001?"*: the answer lists records with citations, calculated values (elapsed time) and what is not established. Press **Save as case note**, edit, and continue with step 4 from that note.
- Choose the model: `uv run python -m app.modules.copilot.compare --models openai/gpt-oss-120b,qwen/qwen3-235b-a22b-2507 --cap-usd 1.00`.
- Add the live section to the benchmark: `uv run python -m app.benchmark --seed 20261101 --variants 50 --live --models openai/gpt-oss-120b --cap-usd 1.00`.

## If something goes wrong

- *Safety checks show "skipped"*: the casebook is not seeded (`uv run python -m app.seed`).
- *"A run is already in progress."*: someone else pressed Run; wait a few seconds.
- *Copilot "unavailable"*: no key, the model failed, or the run passed its time limit; case data still works.
