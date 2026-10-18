# Subtitulador automatico de videos EN -> ES

MVP que toma un video (o audio), transcribe el audio en ingles con ASR,
traduce el texto al espanol y genera subtitulos en formato SRT y VTT.
Incluye una interfaz web minima (FastAPI) y una CLI.

El nucleo (FastAPI, orquestacion, segmentado y generacion de subtitulos)
funciona **sin GPU y sin red**. Los componentes pesados (ASR real con
faster-whisper y traduccion con NLLB) se importan de forma **perezosa** y son
**opcionales**.

## Pipeline

1. **Extraccion de audio** (`audio.py`): ffmpeg convierte el video a WAV mono 16 kHz.
2. **ASR** (`asr.py`): `WhisperBackend` (faster-whisper) o `MockBackend` (demo/tests)
   produce `Segment(start, end, text)`.
3. **Segmentado** (`segment.py`): agrupa y parte los segmentos en `Cue` con
   maximo de caracteres por linea, maximo de lineas, tiempos y fusion por huecos.
4. **Traduccion** (`translate.py`): `PassthroughTranslator`, `MarianTranslator`
   (Helsinki-NLP/opus-mt-en-es, transformers/torch, lazy), `DeepLTranslator`
   (httpx + `DEEPL_API_KEY`) o `NLLBTranslator` (transformers/torch, lazy).
5. **Salida** (`subtitle.py`): SRT (`HH:MM:SS,mmm`) y VTT (`WEBVTT` + `HH:MM:SS.mmm`).

## Instalacion (nucleo, sin GPU)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Requiere `ffmpeg` y `ffprobe` en el PATH.

## Direcciones

La app soporta dos direcciones (se eligen en la web o con `--target` en la CLI):

- **Ingles -> Ingles** (`--target en`): solo transcripcion, sin traducir. Genera
  `<stem>.en.srt` y `<stem>.en.vtt`.
- **Ingles -> Espanol** (`--target es`, por defecto): traduce de verdad. Genera
  `<stem>.en.srt`, `<stem>.en.vtt`, `<stem>.es.srt` y `<stem>.es.vtt`.

## Uso de la CLI

```powershell
# Ingles -> Ingles (solo transcripcion)
python -m subtitulador video.mp4 --asr whisper --target en --out out

# Ingles -> Espanol (traduccion real con MarianMT)
python -m subtitulador video.mp4 --asr whisper --translator marian --target es --out out

python -m subtitulador --help
```

Opciones: `--source`, `--target`, `--asr whisper|mock`,
`--translator marian|nllb|deepl|passthrough`, `--model-size`, `--out`, `--burn`.

Con `--burn` se quema el SRT traducido en el video con ffmpeg.

## Uso de la web

```powershell
uvicorn subtitulador.web:app --reload
```

Abre http://127.0.0.1:8000 , sube un archivo, elige la **Direccion**
(Ingles->Ingles o Ingles->Espanol), pulsa "Generar subtitulos" y descarga los
SRT/VTT disponibles.

El backend ASR y el traductor se eligen con variables de entorno:
`SUBTITULADOR_ASR` (`whisper`|`mock`, por defecto `mock`) y
`SUBTITULADOR_TRANSLATOR` (`marian`|`nllb`|`deepl`|`passthrough`, por defecto
`passthrough`). Ejemplo en PowerShell:

```powershell
$env:SUBTITULADOR_ASR="whisper"; $env:SUBTITULADOR_TRANSLATOR="marian"
uvicorn subtitulador.web:app
```

Endpoints:

- `GET /` interfaz
- `POST /api/transcribe` (multipart, campo `file`)
- `GET /api/jobs/{job_id}`
- `GET /api/download/{job_id}/{srt_en|srt_es|vtt_es}`
- `GET /static/...`

## Instalacion GPU (opcional, CUDA)

Verificado en **GTX 1050 (Pascal, sm_61) + Python 3.14 + CUDA 12.6**:

```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu126
pip install faster-whisper
pip install transformers sentencepiece sacremoses
```

`transformers` es opcional: se importa de forma perezosa y solo hace falta para
`--translator marian|nllb`. El modelo de traduccion (`Helsinki-NLP/opus-mt-en-es`,
~300 MB) se descarga la primera vez y se cachea en `HF_HOME`.

Luego usa `--asr whisper --translator nllb` (o `passthrough` sin motor de
traduccion).

Notas tecnicas (ya resueltas en el codigo):

- `WhisperBackend` elige `compute_type` segun lo que soporte la GPU via
  `ctranslate2.get_supported_compute_types('cuda')`. Pascal no soporta
  `int8_float16`, asi que cae a `int8_float32`; si no hay GPU, usa CPU `int8`.
- Antes de cargar el modelo se registran las DLLs CUDA de `torch/lib`
  (`cublas64_12`, `cudnn64_9`, ...) con `os.add_dll_directory`, necesarias para
  `ctranslate2`.
- La decodificacion de audio se hace con ffmpeg (float32 a 16 kHz) en vez de la
  ruta de `av`, evitando incompatibilidades entre `faster-whisper` y `av`.
- El cache del modelo de Whisper usa `HF_HOME` (p.ej. `setx HF_HOME H:\hf_cache`)
  para no llenar el disco del sistema.

## Limitaciones

- GPU de ejemplo **GTX 1050 4GB**: usa `--model-size small` o `base` para
  evitar problemas de memoria; `large` no es recomendable.
- DeepL requiere `DEEPL_API_KEY` en el entorno.
- NLLB y faster-whisper necesitan las dependencias de `requirements-gpu.txt`
  (no instaladas por defecto).

## Tests

```powershell
python -m pytest -q
```

Los tests generan audio real con ffmpeg y no requieren GPU, red ni torch.
