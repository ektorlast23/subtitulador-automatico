from __future__ import annotations

import subprocess
from pathlib import Path

from .audio import _require
from .models import Segment


class ASRError(RuntimeError):
    pass


class MockBackend:
    name = "mock"

    def __init__(self, segments: list[Segment] | None = None) -> None:
        self._segments = segments

    def transcribe(
        self, audio_path: str | Path, language: str = "en", model_size: str = "small"
    ) -> list[Segment]:
        if self._segments is not None:
            return [Segment(s.start, s.end, s.text) for s in self._segments]
        return [
            Segment(0.0, 2.5, "Hello and welcome to the demo."),
            Segment(2.5, 5.0, "This is a mock transcription backend."),
            Segment(5.0, 8.0, "It does not read the audio file at all."),
        ]


_CUDA_COMPUTE_PREFERENCE = ("int8_float16", "float16", "int8_float32", "int8", "float32")


def _cuda_compute_type() -> str | None:
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() <= 0:
            return None
        supported = ctranslate2.get_supported_compute_types("cuda")
    except Exception:
        return None
    return next((t for t in _CUDA_COMPUTE_PREFERENCE if t in supported), None)


def _decode_audio_16k(audio_path: str | Path):
    ffmpeg = _require("ffmpeg")
    cmd = [
        ffmpeg,
        "-nostdin",
        "-i",
        str(audio_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-f",
        "s16le",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        raise ASRError(
            "No se pudo decodificar el audio con ffmpeg:\n"
            + proc.stderr.decode("utf-8", "ignore")
        )
    import numpy as np

    return np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def _ensure_cuda_libs() -> None:
    import os

    if os.name != "nt":
        return
    try:
        import torch

        lib = Path(torch.__file__).resolve().parent / "lib"
        if lib.is_dir():
            os.add_dll_directory(str(lib))
            os.environ["PATH"] = str(lib) + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


class WhisperBackend:
    name = "whisper"

    def _load_model(self, whisper_model_cls, model_size: str):
        cuda_compute = _cuda_compute_type()
        if cuda_compute:
            _ensure_cuda_libs()
            try:
                return whisper_model_cls(model_size, device="cuda", compute_type=cuda_compute)
            except Exception:
                pass
        return whisper_model_cls(model_size, device="cpu", compute_type="int8")

    def transcribe(
        self, audio_path: str | Path, language: str = "en", model_size: str = "small"
    ) -> list[Segment]:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ASRError(
                "faster_whisper no esta instalado. Instala las dependencias GPU con "
                "'pip install -r requirements-gpu.txt'."
            ) from exc

        model = self._load_model(WhisperModel, model_size)
        audio = _decode_audio_16k(audio_path)
        segments, _info = model.transcribe(audio, language=language)
        return [
            Segment(float(seg.start), float(seg.end), str(seg.text).strip())
            for seg in segments
        ]


def _whisper() -> WhisperBackend:
    return WhisperBackend()


def _mock() -> MockBackend:
    return MockBackend()


BACKENDS = {
    "whisper": _whisper,
    "mock": _mock,
}


def get_backend(name: str):
    try:
        factory = BACKENDS[name]
    except KeyError as exc:
        raise ASRError(
            f"Backend ASR desconocido: {name!r}. Opciones: {sorted(BACKENDS)}"
        ) from exc
    return factory()


def transcribe(
    audio_path: str | Path,
    language: str = "en",
    model_size: str = "small",
    backend: str = "whisper",
) -> list[Segment]:
    return get_backend(backend).transcribe(audio_path, language, model_size)
