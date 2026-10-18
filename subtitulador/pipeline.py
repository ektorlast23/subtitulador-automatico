from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import asr as asr_module
from . import translate as translate_module
from .audio import extract_audio
from .models import Segment
from .segment import build_cues
from .subtitle import write_srt, write_vtt


def _burn(video_path: Path, srt_path: Path, out_video: Path) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg no esta en el PATH; no se puede quemar subtitulos.")
    escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"subtitles='{escaped}'",
        str(out_video),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo al quemar subtitulos:\n{proc.stderr}")
    return out_video


def run(
    input_path: str | Path,
    source: str = "en",
    target: str = "es",
    asr_backend: str = "mock",
    translator: str = "passthrough",
    out_dir: str | Path = "out",
    model_size: str = "small",
    burn: bool = False,
    audio_path: str | Path | None = None,
) -> dict:
    input_path = Path(input_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = input_path.stem

    if audio_path is None:
        audio_path = out / f"{stem}.wav"
    audio_path = Path(audio_path)
    if not audio_path.exists():
        extract_audio(input_path, audio_path)

    backend = asr_module.get_backend(asr_backend)
    segments = backend.transcribe(audio_path, language=source, model_size=model_size)
    source_cues = build_cues(segments)

    trans = translate_module.get_translator(translator)
    texts = [cue.text.replace("\n", " ") for cue in source_cues]
    translated = trans.translate(texts, source=source, target=target)
    target_segments = [
        Segment(cue.start, cue.end, text)
        for cue, text in zip(source_cues, translated)
    ]
    target_cues = build_cues(target_segments)

    srt_en = write_srt(out / f"{stem}.{source}.srt", source_cues)
    srt_target = write_srt(out / f"{stem}.{target}.srt", target_cues)
    vtt_target = write_vtt(out / f"{stem}.{target}.vtt", target_cues)

    result = {
        "input": str(input_path),
        "audio": str(audio_path),
        "source": source,
        "target": target,
        "segments": len(segments),
        "source_cues": source_cues,
        "target_cues": target_cues,
        "files": {
            "srt_source": str(srt_en),
            "srt_target": str(srt_target),
            "vtt_target": str(vtt_target),
        },
    }

    if burn:
        out_video = out / f"{stem}.burned.mp4"
        result["files"]["burned"] = str(_burn(input_path, srt_target, out_video))

    return result
