import json
from pathlib import Path

import pytest

from app.benchmark.__main__ import main
from app.benchmark.report import build_report, write_report


def test_report_metrics_deterministic() -> None:
    a, b = build_report(11, 4), build_report(11, 4)

    assert {k: v for k, v in a.items() if k != "meta"} == {
        k: v for k, v in b.items() if k != "meta"
    }
    assert a["live"] == {"status": "not run (no key)"}


def test_results_md_has_caveats(tmp_path: Path) -> None:
    write_report(build_report(11, 2), tmp_path)

    md = (tmp_path / "RESULTS.md").read_text()
    for phrase in (
        "regression benchmark",
        "not real-world",
        "not tuned",
        "python -m app.benchmark --seed 11 --variants 2",
    ):
        assert phrase in md
    assert json.loads((tmp_path / "results.json").read_text())["parameters"]["seed"] == 11


@pytest.mark.parametrize("args", [["--variants", "0"], ["--variants", "-1"], ["--seed", "x"]])
def test_cli_rejects_bad_arguments(tmp_path: Path, args: list[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--out", str(tmp_path), *args])

    assert raised.value.code == 2
    assert list(tmp_path.iterdir()) == []


def test_cli_rejects_unwritable_out(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("x")

    with pytest.raises(SystemExit) as raised:
        main(["--variants", "1", "--out", str(blocker / "sub")])

    assert raised.value.code == 2


def test_live_without_key_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    from app.core.config import get_settings

    get_settings.cache_clear()
    with pytest.raises(SystemExit) as raised:
        main(["--variants", "1", "--out", str(tmp_path), "--live", "--models", "a/x"])

    assert raised.value.code == 2
    assert "OPENROUTER_API_KEY is not set" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_cli_writes_both_files(tmp_path: Path) -> None:
    main(["--seed", "3", "--variants", "2", "--out", str(tmp_path)])

    assert sorted(p.name for p in tmp_path.iterdir()) == ["RESULTS.md", "results.json"]


def test_report_does_not_claim_a_commit(tmp_path: Path) -> None:
    """Results are generated before they are committed, so any SHA in them names other code."""
    report = build_report(11, 1)
    write_report(report, tmp_path)

    assert "git_sha" not in report["meta"]
    assert "code `" not in (tmp_path / "RESULTS.md").read_text()


def test_report_names_the_rule_version_in_use() -> None:
    from app.benchmark.report import build_report
    from app.modules.detection.rules.rapid_onward_transfer import RapidOnwardTransfer

    report = build_report(20261101, 1)

    assert report["parameters"]["rule"] == f"RAPID_ONWARD_TRANSFER v{RapidOnwardTransfer.version}"
