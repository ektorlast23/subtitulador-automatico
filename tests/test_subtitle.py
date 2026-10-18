from subtitulador.models import Cue
from subtitulador.subtitle import to_srt, to_vtt, write_srt, write_vtt


def test_to_srt_exact_format():
    cues = [
        Cue(0.0, 2.5, ["Hello world"]),
        Cue(2.5, 5.0, ["Second line"]),
    ]
    expected = (
        "1\n"
        "00:00:00,000 --> 00:00:02,500\n"
        "Hello world\n"
        "\n"
        "2\n"
        "00:00:02,500 --> 00:00:05,000\n"
        "Second line\n"
    )
    assert to_srt(cues) == expected


def test_to_srt_multiline_and_hours():
    cues = [Cue(3661.25, 3663.5, ["line one", "line two"])]
    expected = (
        "1\n"
        "01:01:01,250 --> 01:01:03,500\n"
        "line one\n"
        "line two\n"
    )
    assert to_srt(cues) == expected


def test_to_vtt_exact_format():
    cues = [Cue(0.0, 2.5, ["Hello world"])]
    expected = "WEBVTT\n\n00:00:00.000 --> 00:00:02.500\nHello world\n"
    assert to_vtt(cues) == expected


def test_write_files(tmp_path):
    cues = [Cue(0.0, 1.0, ["hi"])]
    srt = write_srt(tmp_path / "a.srt", cues)
    vtt = write_vtt(tmp_path / "a.vtt", cues)
    assert srt.read_text(encoding="utf-8").startswith("1\n00:00:00,000")
    assert vtt.read_text(encoding="utf-8").startswith("WEBVTT\n\n")
