from app.benchmark.families import generate
from app.benchmark.grounding import TAMPERS, score_grounding


def test_tampered_answers_rejected_faithful_kept() -> None:
    variants = [v for v in generate(5, 3) if v.expected_paths]

    s = score_grounding(variants)

    assert s["faithful"]["false_rejections"] == 0
    assert s["faithful"]["answers"] == len(variants)
    for kind in TAMPERS:
        assert s["tampered"][kind]["rejected"] == s["tampered"][kind]["answers"] == len(variants)
