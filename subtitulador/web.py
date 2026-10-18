from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import Cue
from .pipeline import run

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

KINDS = {
    "srt_en": "srt_source",
    "vtt_en": "vtt_source",
    "srt_es": "srt_target",
    "vtt_es": "vtt_target",
}


def _downloads(job_id: str, files: dict) -> dict:
    available = {
        "srt_en": "srt_source",
        "vtt_en": "vtt_source",
        "srt_es": "srt_target",
        "vtt_es": "vtt_target",
    }
    return {
        kind: f"/api/download/{job_id}/{kind}"
        for kind, key in available.items()
        if key in files
    }


def _cue_to_dict(cue: Cue) -> dict:
    return {
        "start": round(cue.start, 3),
        "end": round(cue.end, 3),
        "lines": cue.lines,
        "text": cue.text,
    }


def _serialize(job_id: str, result: dict) -> dict:
    translated = result.get("translated", result["target"] != result["source"])
    return {
        "job_id": job_id,
        "status": "done",
        "source": result["source"],
        "target": result["target"],
        "translated": translated,
        "en": [_cue_to_dict(c) for c in result["source_cues"]],
        "es": [_cue_to_dict(c) for c in result["target_cues"]] if translated else [],
        "downloads": _downloads(job_id, result["files"]),
    }


def create_app(asr_backend: str = "mock", translator: str = "passthrough") -> FastAPI:
    app = FastAPI(title="Subtitulador automatico EN->ES")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    job_dir = Path(tempfile.mkdtemp(prefix="subtitulador-jobs-"))
    jobs: dict[str, dict] = {}

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def index(request: Request):
        return templates.TemplateResponse(request, "index.html")

    @app.post("/api/transcribe")
    async def transcribe(file: UploadFile = File(...), target: str = Form("es")):
        if target not in ("en", "es"):
            raise HTTPException(status_code=400, detail="Idioma destino invalido")

        job_id = uuid.uuid4().hex
        work_dir = job_dir / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename or "input").suffix or ".bin"
        input_path = work_dir / f"input{suffix}"
        data = await file.read()
        input_path.write_bytes(data)

        audio_path = work_dir / "audio.wav"
        try:
            result = run(
                input_path,
                source="en",
                target=target,
                asr_backend=asr_backend,
                translator=translator,
                out_dir=work_dir,
                audio_path=audio_path,
            )
        except Exception as exc:
            lines = [ln.strip() for ln in str(exc).splitlines() if ln.strip()]
            detail = " | ".join(lines[-3:])[:500] if lines else str(exc)
            raise HTTPException(
                status_code=500, detail=f"Fallo al procesar el archivo: {detail}"
            ) from exc

        jobs[job_id] = {
            "job_id": job_id,
            "status": "done",
            "result": result,
            "dir": str(work_dir),
        }
        return _serialize(job_id, result)

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str):
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        return _serialize(job_id, job["result"])

    @app.get("/api/download/{job_id}/{kind}")
    def download(job_id: str, kind: str):
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        key = KINDS.get(kind)
        path_str = job["result"]["files"].get(key) if key else None
        if not path_str:
            raise HTTPException(status_code=404, detail="Tipo de descarga invalido")
        path = Path(path_str)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        return FileResponse(
            path,
            filename=path.name,
            media_type="application/octet-stream",
        )

    return app


app = create_app(
    asr_backend=os.getenv("SUBTITULADOR_ASR", "mock"),
    translator=os.getenv("SUBTITULADOR_TRANSLATOR", "passthrough"),
)
