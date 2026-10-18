from __future__ import annotations

from pathlib import Path

from .models import Cue


def _format_timestamp(seconds: float, sep: str) -> str:
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{millis:03d}"


def to_srt(cues: list[Cue]) -> str:
    blocks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        start = _format_timestamp(cue.start, ",")
        end = _format_timestamp(cue.end, ",")
        text = "\n".join(cue.lines)
        blocks.append(f"{index}\n{start} --> {end}\n{text}\n")
    return "\n".join(blocks)


def to_vtt(cues: list[Cue]) -> str:
    lines = ["WEBVTT", ""]
    for cue in cues:
        start = _format_timestamp(cue.start, ".")
        end = _format_timestamp(cue.end, ".")
        lines.append(f"{start} --> {end}")
        lines.extend(cue.lines)
        lines.append("")
    return "\n".join(lines)


def write_srt(path: str | Path, cues: list[Cue]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_srt(cues), encoding="utf-8")
    return out


def write_vtt(path: str | Path, cues: list[Cue]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_vtt(cues), encoding="utf-8")
    return out
