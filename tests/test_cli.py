import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None, reason="ffmpeg no disponible"
)


def _make_audio(path, seconds=1):
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


def test_cli_help():
    proc = subprocess.run(
        [sys.executable, "-m", "subtitulador", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert "--asr" in proc.stdout


def test_cli_runs_pipeline(tmp_path):
    audio = tmp_path / "input.wav"
    _make_audio(audio)
    out_dir = tmp_path / "out"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "subtitulador",
            str(audio),
            "--asr",
            "mock",
            "--translator",
            "passthrough",
            "--out",
            str(out_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert (out_dir / "input.en.srt").exists()
    assert (out_dir / "input.es.srt").exists()
    assert (out_dir / "input.es.vtt").exists()
