from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class FFmpegError(RuntimeError):
    pass


def _require(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise FFmpegError(
            f"No se encontro '{tool}' en el PATH. Instala ffmpeg y anadelo al PATH."
        )
    return path


def extract_audio(video_path: str | Path, out_wav: str | Path) -> Path:
    ffmpeg = _require("ffmpeg")
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "wav",
        str(out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise FFmpegError(
            f"ffmpeg fallo al extraer audio (codigo {proc.returncode}):\n{proc.stderr}"
        )
    if not out.exists() or out.stat().st_size == 0:
        raise FFmpegError("ffmpeg no genero un archivo de audio valido.")
    return out


def duration(path: str | Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None
