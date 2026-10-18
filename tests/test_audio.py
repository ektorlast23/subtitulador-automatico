import shutil
import subprocess

import pytest

from subtitulador.audio import duration, extract_audio

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg no disponible"
)


def _make_audio(path, seconds=2):
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={seconds}",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def test_extract_audio_creates_wav(tmp_path):
    source = tmp_path / "source.wav"
    _make_audio(source)
    out = tmp_path / "audio.wav"
    result = extract_audio(source, out)
    assert result.exists()
    assert result.stat().st_size > 0
    assert result.suffix == ".wav"


def test_duration_reads_generated_audio(tmp_path):
    source = tmp_path / "source.wav"
    _make_audio(source, seconds=2)
    value = duration(source)
    if value is not None:
        assert value == pytest.approx(2.0, abs=0.3)
