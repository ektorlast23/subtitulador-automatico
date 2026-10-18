import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from subtitulador.web import create_app

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


def test_index_page():
    client = TestClient(create_app(asr_backend="mock", translator="passthrough"))
    response = client.get("/")
    assert response.status_code == 200
    assert "Subtitulador" in response.text


def test_transcribe_and_download(tmp_path):
    audio = tmp_path / "input.wav"
    _make_audio(audio)
    data = audio.read_bytes()

    client = TestClient(create_app(asr_backend="mock", translator="passthrough"))
    response = client.post(
        "/api/transcribe",
        files={"file": ("input.wav", data, "audio/wav")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert len(payload["en"]) > 0
    assert len(payload["es"]) > 0
    assert "downloads" in payload

    job_id = payload["job_id"]
    status = client.get(f"/api/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] == "done"

    download = client.get(f"/api/download/{job_id}/srt_es")
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"]
    assert "-->" in download.text


def test_direction_en_only(tmp_path):
    audio = tmp_path / "input.wav"
    _make_audio(audio)
    data = audio.read_bytes()

    client = TestClient(create_app(asr_backend="mock", translator="passthrough"))
    response = client.post(
        "/api/transcribe",
        files={"file": ("input.wav", data, "audio/wav")},
        data={"target": "en"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["translated"] is False
    assert len(payload["en"]) > 0
    assert payload["es"] == []
    assert "srt_en" in payload["downloads"]
    assert "vtt_en" in payload["downloads"]
    assert "srt_es" not in payload["downloads"]

    job_id = payload["job_id"]
    assert client.get(payload["downloads"]["vtt_en"]).status_code == 200
    assert client.get(f"/api/download/{job_id}/srt_es").status_code == 404


def test_download_unknown_job():
    client = TestClient(create_app(asr_backend="mock", translator="passthrough"))
    response = client.get("/api/download/nope/srt_es")
    assert response.status_code == 404
