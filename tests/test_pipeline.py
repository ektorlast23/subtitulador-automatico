from subtitulador.pipeline import run


def test_run_writes_all_subtlitle_files(tmp_path):
    input_path = tmp_path / "sample.mp4"
    input_path.write_bytes(b"fake video")
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake audio")

    result = run(
        input_path,
        asr_backend="mock",
        translator="passthrough",
        out_dir=tmp_path / "out",
        audio_path=audio_path,
    )

    out_dir = tmp_path / "out"
    srt_en = out_dir / "sample.en.srt"
    srt_es = out_dir / "sample.es.srt"
    vtt_es = out_dir / "sample.es.vtt"

    assert srt_en.exists()
    assert srt_es.exists()
    assert vtt_es.exists()

    content = srt_en.read_text(encoding="utf-8")
    assert content.startswith("1\n00:00:00,000 -->")
    assert "-->" in content

    assert result["segments"] == 3
    assert len(result["source_cues"]) == len(result["target_cues"])
    assert result["files"]["srt_target"] == str(srt_es)


def test_run_en_to_en_skips_translation(tmp_path):
    input_path = tmp_path / "sample.mp4"
    input_path.write_bytes(b"fake video")
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake audio")

    result = run(
        input_path,
        source="en",
        target="en",
        asr_backend="mock",
        translator="marian",
        out_dir=tmp_path / "out",
        audio_path=audio_path,
    )

    out_dir = tmp_path / "out"
    assert (out_dir / "sample.en.srt").exists()
    assert (out_dir / "sample.en.vtt").exists()
    assert not (out_dir / "sample.es.srt").exists()
    assert result["translated"] is False
    assert result["target_cues"] == result["source_cues"]
    assert "srt_target" not in result["files"]
    assert "vtt_target" not in result["files"]
