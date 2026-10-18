from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subtitulador",
        description="Subtitulador automatico de videos EN->ES (ASR + traduccion + SRT/VTT).",
    )
    parser.add_argument("input", help="Ruta del video o audio de entrada.")
    parser.add_argument("--source", default="en", help="Idioma origen (default: en).")
    parser.add_argument("--target", default="es", help="Idioma destino (default: es).")
    parser.add_argument(
        "--asr",
        default="whisper",
        choices=["whisper", "mock"],
        help="Backend ASR (default: whisper).",
    )
    parser.add_argument(
        "--translator",
        default="passthrough",
        choices=["nllb", "deepl", "passthrough"],
        help="Traductor (default: passthrough).",
    )
    parser.add_argument(
        "--model-size", default="small", help="Tamano de modelo Whisper (default: small)."
    )
    parser.add_argument("--out", default="out", help="Directorio de salida (default: out).")
    parser.add_argument(
        "--burn", action="store_true", help="Quema los subtitulos en el video con ffmpeg."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"El archivo de entrada no existe: {input_path}")

    print(f"[1/4] Extrayendo audio y transcribiendo ({args.asr})...")
    result = run(
        input_path,
        source=args.source,
        target=args.target,
        asr_backend=args.asr,
        translator=args.translator,
        out_dir=args.out,
        model_size=args.model_size,
        burn=args.burn,
    )
    print(f"[2/4] Segmentos transcritos: {result['segments']}")
    print(f"[3/4] Cues origen: {len(result['source_cues'])} | destino: {len(result['target_cues'])}")
    print("[4/4] Archivos generados:")
    for name, path in result["files"].items():
        print(f"      {name}: {path}")
    return 0
