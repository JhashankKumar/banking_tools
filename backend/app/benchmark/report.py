"""Builds the benchmark report and writes results.json + RESULTS.md."""

import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.benchmark.families import CONFIG, FAMILIES, generate
from app.benchmark.grounding import score_grounding
from app.benchmark.metrics import score_paths, score_rule
from app.modules.detection.rules.rapid_onward_transfer import RapidOnwardTransfer
from app.modules.graph.paths import PathParams

NOT_RUN = {"status": "not run (no key)"}
CAVEATS = (
    "This is a **regression benchmark** on scenario families written by this project. It is "
    "**not real-world** performance and says nothing about how the rule would do on real bank "
    "data. The rule was **not tuned** on these variants: its parameters are the defaults in "
    "`rapid_onward_transfer.py`. Labels follow the rule's written contract (see "
    "`docs/evaluation/README.md`), so a score of 1.0 means the code does what its contract "
    "says, not that it catches fraud."
)


def command(seed: int, variants: int) -> str:
    return f"cd backend && uv run python -m app.benchmark --seed {seed} --variants {variants}"


def build_report(seed: int, variants: int, *, live: dict[str, Any] | None = None) -> dict[str, Any]:
    generated = generate(seed, variants)
    path = PathParams()
    return {
        "meta": {
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%d"),
            "python": platform.python_version(),
        },
        "parameters": {
            "seed": seed,
            "variants_per_family": variants,
            "command": command(seed, variants),
            "rule": f"RAPID_ONWARD_TRANSFER v{RapidOnwardTransfer.version}",
            "rule_window_seconds": int(CONFIG.window.total_seconds()),
            "rule_min_onward_ratio": f"{CONFIG.min_onward_ratio:.2f}",
            "rule_min_incoming_inr": f"{CONFIG.min_incoming_amount['INR']:.2f}",
            "path_window_hours": int(path.window.total_seconds() // 3600),
            "path_max_hops": path.max_hops,
        },
        "variants": {f.name: sum(v.family == f.name for v in generated) for f in FAMILIES},
        "metrics": {
            "rule": score_rule(generated),
            "paths": score_paths(generated),
            "grounding": score_grounding(generated),
        },
        "live": live or NOT_RUN,
    }


def _fmt(rate: float | None) -> str:
    return "n/a" if rate is None else f"{rate:.4f}"


def _markdown(r: dict[str, Any]) -> str:
    p, m = r["parameters"], r["metrics"]
    labels = {f.name: f.label_rule for f in FAMILIES}
    rule, paths, grounding = m["rule"], m["paths"], m["grounding"]
    o = rule["overall"]
    lines = [
        "# Benchmark results",
        "",
        CAVEATS,
        "",
        f"Reproduce: `{p['command']}` (then compare `metrics` in `results.json`; only `meta` "
        "may differ).",
        "",
        f"Generated {r['meta']['generated_at']} by the code in the commit that contains this "
        f"file · Python "
        f"{r['meta']['python']} · seed {p['seed']} · {p['variants_per_family']} variants per "
        f"family · {sum(r['variants'].values())} variants in all.",
        "",
        f"## Detection rule ({p['rule']})",
        "",
        f"Window {p['rule_window_seconds']} s, minimum onward share {p['rule_min_onward_ratio']}, "
        f"minimum incoming INR {p['rule_min_incoming_inr']}.",
        "",
        f"Overall, per variant: precision {_fmt(o['precision'])}, recall {_fmt(o['recall'])} "
        f"(TP {o['variants']['tp']}, FP {o['variants']['fp']}, FN {o['variants']['fn']}, "
        f"TN {o['variants']['tn']}). Per (incoming, onward) pair: TP {o['pairs']['tp']}, "
        f"FP {o['pairs']['fp']}, FN {o['pairs']['fn']}.",
        "",
        "| Family | Label | TP | FP | FN | TN | Precision | Recall | Pairs TP/FP/FN |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, s in rule["families"].items():
        c, pr = s["variants"], s["pairs"]
        lines.append(
            f"| {name} | {labels[name]} | {c['tp']} | {c['fp']} | {c['fn']} | {c['tn']} | "
            f"{_fmt(s['precision'])} | {_fmt(s['recall'])} | {pr['tp']}/{pr['fp']}/{pr['fn']} |"
        )
    po = paths["overall"]
    lines += [
        "",
        "## Money paths",
        "",
        f"Path finder defaults: {p['path_window_hours']} h window, {p['path_max_hops']} hops, "
        f"completed hops only. Overall: precision {_fmt(po['precision'])}, recall "
        f"{_fmt(po['recall'])} over {po['variants_scored']} variants.",
        "",
        "| Family | Variants | TP | FP | FN | Precision | Recall |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, s in paths["families"].items():
        c = s["paths"]
        lines.append(
            f"| {name} | {s['variants_scored']} | {c['tp']} | {c['fp']} | {c['fn']} | "
            f"{_fmt(s['precision'])} | {_fmt(s['recall'])} |"
        )
    f = grounding["faithful"]
    lines += [
        "",
        "## Answer grounding (validator)",
        "",
        "For each variant with a money path, one faithful answer built from its records and one "
        "tampered copy per kind. The validator should pass the first and catch the rest.",
        "",
        f"Faithful answers: {f['answers']}, wrongly rejected {f['false_rejections']} "
        f"(rate {_fmt(f['false_rejection_rate'])}).",
        "",
        "| Tamper | Answers | Caught | Rate |",
        "|---|---|---|---|",
    ]
    for kind, t in grounding["tampered"].items():
        lines.append(f"| {kind} | {t['answers']} | {t['rejected']} | {_fmt(t['rejection_rate'])} |")
    lines += ["", "## Live model", ""]
    live = r["live"]
    if live.get("status"):
        lines.append(
            f"{live['status'].capitalize()}. Run with `--live --models <ids> --cap-usd 1.00` "
            "once `OPENROUTER_API_KEY` is set."
        )
    else:
        lines += [
            "| Model | Questions | Answered | Failed | Cost USD | Mean latency ms |",
            "|---|---|---|---|---|---|",
        ]
        for model, s in live["models"].items():
            lines.append(
                f"| {model} | {s['questions']} | {s['answered']} | {s['failed']} | "
                f"{s['cost_usd']} | {s['mean_latency_ms']} |"
            )
    lines += [
        "",
        "## Not measured",
        "",
        "PR-AUC (no ML baseline is implemented), real-world detection rates, analyst time "
        "saved. Safety checks are not part of this benchmark: run them on the Safety checks "
        "page or with `uv run pytest -q tests/security`.",
        "",
    ]
    return "\n".join(lines)


def write_report(report: dict[str, Any], out: Path) -> None:
    """Writes each file to a temporary name first, so a failed write never leaves a half file."""
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "results.json": json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "RESULTS.md": _markdown(report),
    }
    staged: list[tuple[Path, Path]] = []
    try:
        for name, text in files.items():
            tmp = out / f".{name}.tmp"
            tmp.write_text(text, encoding="utf-8")
            staged.append((tmp, out / name))
        for tmp, final in staged:
            tmp.replace(final)
    finally:
        for tmp, _ in staged:
            tmp.unlink(missing_ok=True)
