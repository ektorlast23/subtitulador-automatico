from subtitulador.models import Segment
from subtitulador.segment import build_cues


def test_wrap_by_max_chars_and_two_lines():
    cues = build_cues(
        [Segment(0.0, 3.0, "hello world foo bar")],
        max_chars=12,
        max_lines=2,
    )
    assert len(cues) == 1
    assert len(cues[0].lines) <= 2
    assert all(len(line) <= 12 for line in cues[0].lines)


def test_merge_when_gap_small():
    segments = [
        Segment(0.0, 1.0, "first part"),
        Segment(1.5, 2.5, "second part"),
    ]
    merged = build_cues(segments, max_gap=0.8)
    assert len(merged) == 1
    assert "first part" in merged[0].text
    assert "second part" in merged[0].text


def test_no_merge_when_gap_large():
    segments = [
        Segment(0.0, 1.0, "first part"),
        Segment(3.0, 4.0, "second part"),
    ]
    cues = build_cues(segments, max_gap=0.8)
    assert len(cues) == 2


def test_max_duration_splits_cues():
    cues = build_cues([Segment(0.0, 20.0, "one two three four five six seven")], max_duration=7.0)
    assert len(cues) > 1
    assert all(cue.end - cue.start <= 7.0 + 1e-6 for cue in cues)


def test_min_duration_enforced():
    cues = build_cues([Segment(0.0, 0.2, "short")], min_duration=1.0)
    assert len(cues) == 1
    assert cues[0].end - cues[0].start >= 1.0


def test_empty_text_discarded():
    segments = [
        Segment(0.0, 1.0, ""),
        Segment(1.0, 2.0, "   "),
        Segment(2.0, 3.0, "real text"),
    ]
    cues = build_cues(segments)
    assert len(cues) == 1
    assert cues[0].text == "real text"


def test_no_text_loss_when_words_exceed_two_lines():
    text = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen"
    cues = build_cues([Segment(0.0, 1.0, text)], max_chars=12, max_lines=2)
    recovered = " ".join(cue.text for cue in cues)
    assert recovered.split() == text.split()


def test_no_text_loss_on_long_fast_segment():
    text = " ".join(f"w{i}" for i in range(40))
    cues = build_cues([Segment(0.0, 1.0, text)], max_chars=10, max_lines=2)
    recovered = " ".join(cue.text for cue in cues)
    assert recovered.split() == text.split()
    assert all(len(cue.lines) <= 2 for cue in cues)
