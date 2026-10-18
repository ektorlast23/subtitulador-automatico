from __future__ import annotations

from .models import Cue, Segment


def _clean(text: str) -> str:
    return " ".join(text.split())


def _wrap(text: str, max_chars: int, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _words_fitting_in_lines(words: list[str], max_chars: int, max_lines: int) -> int:
    if max_lines <= 0:
        return len(words)
    lines = 0
    current = ""
    for index, word in enumerate(words):
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines += 1
            if lines >= max_lines:
                return index
            current = word
    return len(words)


def build_cues(
    segments: list[Segment],
    max_chars: int = 42,
    max_lines: int = 2,
    max_duration: float = 7.0,
    min_duration: float = 1.0,
    max_gap: float = 0.8,
) -> list[Cue]:
    cleaned = [
        (s.start, s.end, _clean(s.text))
        for s in segments
        if s.text and _clean(s.text)
    ]
    if not cleaned:
        return []

    merged: list[list[float | str]] = []
    for start, end, text in cleaned:
        if merged and start - float(merged[-1][1]) < max_gap:
            merged[-1][1] = end
            merged[-1][2] = f"{merged[-1][2]} {text}".strip()
        else:
            merged.append([start, end, text])

    cues: list[Cue] = []
    for start, end, text in merged:
        start = float(start)
        end = float(end)
        duration = max(0.0, end - start)
        words = str(text).split()
        if not words:
            continue

        total_words = len(words)
        sec_per_word = duration / total_words if total_words else 0.0

        cap_by_duration = total_words
        if max_duration and max_duration > 0 and sec_per_word > 0:
            cap_by_duration = max(1, int(max_duration / sec_per_word + 1e-9))
        cap_by_lines = max(1, _words_fitting_in_lines(words, max_chars, max_lines))
        capacity = max(1, min(cap_by_duration, cap_by_lines))

        texts: list[str] = []
        for i in range(0, total_words, capacity):
            chunk = words[i : i + capacity]
            lines = _wrap(" ".join(chunk), max_chars, max_lines)
            for j in range(0, len(lines), max_lines):
                texts.append(" ".join(lines[j : j + max_lines]))

        counts = [len(t.split()) for t in texts]
        assigned = sum(counts) or 1
        acc = 0
        for chunk_text, count in zip(texts, counts):
            a = acc
            acc += count
            c_start = start + duration * (a / assigned)
            c_end = start + duration * (acc / assigned)
            if c_end - c_start < min_duration:
                c_end = c_start + min_duration
            cues.append(Cue(c_start, c_end, _wrap(chunk_text, max_chars, max_lines)))

    for i in range(len(cues) - 1):
        if cues[i].end > cues[i + 1].start:
            cues[i].end = max(cues[i].start + 0.02, cues[i + 1].start)

    cues = [c for c in cues if c.lines and c.end > c.start]
    return cues
