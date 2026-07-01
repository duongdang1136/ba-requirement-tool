# BA Requirement Tool

Turn meeting recordings into reviewed, traceable requirement artifacts. The app runs locally by default.

```text
Upload audio/video -> Local STT -> Transcript review -> AI summary/extraction -> Export
```

## Features

- Upload meeting audio/video: `.mp3`, `.wav`, `.m4a`, `.mp4`, `.webm`, `.ogg`
- Normalize audio with ffmpeg
- Detect speech with local VAD
- Transcribe with local sherpa-onnx Whisper
- Detect speaker turns and rename speaker labels
- Review and edit transcript segments while preserving original text
- Export transcript to Markdown or TXT
- Generate meeting summary, decisions, action items, and open questions with local Ollama
- Suggest transcript rewrites with local Ollama
- Extract requirement candidates and approve/reject/edit them

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.10+
- ffmpeg
- Ollama, optional but required for AI summary/rewrite/requirement extraction

### Windows Prerequisites

Install Node.js and Python from:

- https://nodejs.org
- https://www.python.org/downloads/

Install ffmpeg:

```powershell
winget install Gyan.FFmpeg
```

Install Ollama, optional:

```powershell
winget install --id Ollama.Ollama -e
```

Close and reopen PowerShell, then verify:

```powershell
node --version
npm --version
python --version
ffmpeg -version
```

If you installed Ollama, verify it too:

```powershell
ollama --version
```

### macOS Prerequisites

```bash
brew install node python ffmpeg
```

Install Ollama from:

```text
https://ollama.com/download
```

### Ubuntu / WSL Prerequisites

```bash
sudo apt update
sudo apt install -y nodejs npm python3 python3-venv ffmpeg
```

Install Ollama from:

```text
https://ollama.com/download
```

## Install And Run

```bash
git clone https://github.com/duongdang1136/ba-requirement-tool.git
cd ba-requirement-tool
npm install
npm run setup
npm run dev
```

Open:

```text
http://localhost:5173
```

`npm run setup` does the following:

- Installs frontend dependencies
- Creates `backend/.venv`
- Installs backend Python dependencies
- Creates `backend/.env` from `backend/.env.example` if missing
- Downloads the default local ASR, VAD, speaker segmentation, and speaker embedding models

The first setup downloads large model files. Later runs reuse the local files.

To stop the app, press `Ctrl+C` in the terminal running `npm run dev`.

## AI Setup With Ollama

AI features are local-only through Ollama. No transcript is sent to a cloud LLM by default.

For smaller machines, pull the lightweight model:

```bash
ollama pull qwen2.5:3b
```

For better quality, pull the default model:

```bash
ollama pull qwen2.5:7b
```

Check installed models:

```bash
ollama list
```

If you only pulled `qwen2.5:3b`, run the app with:

```powershell
$env:OLLAMA_MODEL="qwen2.5:3b"
$env:OLLAMA_FALLBACK_MODEL="qwen2.5:3b"
npm run dev
```

On macOS/Linux:

```bash
OLLAMA_MODEL=qwen2.5:3b OLLAMA_FALLBACK_MODEL=qwen2.5:3b npm run dev
```

Ollama usually starts automatically. If the app reports that it cannot call `http://localhost:11434`, check:

```bash
ollama list
```

or start the server manually:

```bash
ollama serve
```

## Daily Usage

After setup:

```bash
cd ba-requirement-tool
npm run dev
```

Open:

```text
http://localhost:5173
```

The dev script starts:

- FastAPI backend on `http://localhost:8099`
- Background worker for audio and AI jobs
- Vite frontend on `http://localhost:5173`

## Runtime Data

Local runtime data is stored in:

- `backend/ba_tool.db`
- `backend/uploads/`
- `models/`
- `backend/.env`
- `frontend/node_modules/`
- `backend/.venv/`

These paths are ignored by Git.

## Configuration

Default config lives in `backend/.env.example`. `npm run setup` copies it to `backend/.env` if the file does not already exist.

Important variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./ba_tool.db` | Local SQLite database path, relative to `backend/` |
| `UPLOAD_DIR` | `./uploads` | Uploaded and normalized media directory |
| `MAX_UPLOAD_SIZE_MB` | `1024` | Upload size limit |
| `UPLOAD_CHUNK_SIZE_MB` | `8` | Browser upload chunk size |
| `ASR_MODEL_DIR` | `../models/asr/sherpa-onnx-whisper-small` | sherpa-onnx Whisper model |
| `ASR_LANGUAGE` | `vi` | Primary ASR language |
| `ASR_NUM_THREADS` | `8` | ASR CPU threads |
| `ASR_PROVIDER` | `cpu` | sherpa-onnx provider. Use `coreml` on supported macOS devices |
| `VAD_MODEL_PATH` | `../models/vad/silero_vad.onnx` | Silero VAD model |
| `DIARIZATION_SEGMENTATION_MODEL` | `../models/diarization/sherpa-onnx-pyannote-segmentation-3-0/model.onnx` | Speaker segmentation model |
| `DIARIZATION_EMBEDDING_MODEL` | `../models/diarization/3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx` | Speaker embedding model |
| `DIARIZATION_CLUSTER_THRESHOLD` | `0.5` | Speaker clustering threshold |
| `DIARIZATION_CHUNK_MINUTES` | `25` | Diarization chunk size |
| `DIARIZATION_SPEAKER_MATCH_THRESHOLD` | `0.62` | Cross-chunk speaker matching threshold |
| `LLM_PROVIDER` | `ollama` | Local AI provider |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Primary Ollama model |
| `OLLAMA_FALLBACK_MODEL` | `qwen2.5:3b` | Fallback Ollama model |
| `OLLAMA_TIMEOUT_SECONDS` | `300` | LLM request timeout |
| `OLLAMA_CONTEXT_TOKENS` | `8192` | Ollama context window |
| `LLM_TEMPERATURE` | `0.2` | Lower values keep extraction more stable |

## Developer Commands

Run the full app:

```bash
npm run dev
```

Build frontend:

```bash
npm run build
```

Clean generated caches and build artifacts:

```bash
npm run cleanup
```

Clean local npm/pip/temp caches as well:

```bash
npm run cleanup -- --system-cache
```

Run backend tests:

```bash
cd backend
.venv\Scripts\python.exe -m unittest discover -s tests
```

On macOS/Linux:

```bash
cd backend
.venv/bin/python -m unittest discover -s tests
```

## Manual Development Mode

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8099
```

Worker, in another terminal:

```bash
cd backend
.venv\Scripts\activate
python -m app.worker
```

Frontend, in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Troubleshooting

### `vite` is not recognized

Frontend dependencies are missing. Run:

```bash
npm --prefix frontend install
```

### Cannot call Ollama at `http://localhost:11434`

Ollama is not running or the model is missing. Check:

```bash
ollama list
```

Pull a model:

```bash
ollama pull qwen2.5:3b
```

### ffmpeg not found

Install ffmpeg and reopen the terminal:

```powershell
winget install Gyan.FFmpeg
```

### First setup is slow

This is expected. The setup downloads ASR, VAD, and speaker diarization models. The files are reused after the first run.

## Project Structure

```text
ba-requirement-tool/
|-- backend/              # FastAPI + SQLAlchemy
|   |-- app/
|   |   |-- api/routes/   # projects, meetings, transcript, requirements, export
|   |   |-- core/         # config, database
|   |   |-- models/       # SQLAlchemy models
|   |   `-- services/     # audio pipeline, extraction, export
|   `-- tests/
|-- frontend/             # React + TypeScript + Vite
|   |-- src/
|   |   |-- pages/
|   |   |-- components/
|   |   |-- api/
|   |   `-- types/
|-- scripts/
|-- package.json
`-- README.md
```

## Tech Stack

| Area | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy |
| Database | SQLite local file |
| Speech-to-text | sherpa-onnx Whisper |
| Speaker diarization | sherpa-onnx diarization models |
| AI | Ollama |
| Audio/video | ffmpeg |
| Frontend | React, TypeScript, Vite |

## License

MIT
