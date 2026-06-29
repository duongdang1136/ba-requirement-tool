# BA Requirement Tool

> Turn meeting recordings into reviewed, traceable requirement artifacts — fully offline.

```
Upload audio/video → Local STT → Transcript review → Edit → Export
```

## Quick Start

For most users, run the app directly with npm scripts.

**Prerequisites:**

- Node.js 20+
- Python 3.10+
- ffmpeg

```bash
git clone https://github.com/duongdang1136/ba-requirement-tool.git
cd ba-requirement-tool
npm install
npm run setup
npm run dev
```

Then open → **http://localhost:5173**

`npm run setup` installs frontend dependencies, creates the backend Python virtual environment, installs backend dependencies, and downloads the default sherpa-onnx Whisper small ASR model.

The first setup downloads roughly 600MB of model files. Later runs reuse the local model.

To stop the app, press `Ctrl+C` in the terminal running `npm run dev`.

---

## What You Can Do (MVP)

- 📁 Upload meeting audio/video (`.mp3` `.wav` `.m4a` `.mp4`)
- ⚙️ Auto-process: normalize audio → transcribe with local speech-to-text
- 📝 Review transcript by timestamp
- ✏️ Edit transcript text (preserves original + traceability)
- 💾 Export reviewed transcript to **Markdown** or **TXT**

## Install Prerequisites

### Windows

Install:

- Node.js LTS from https://nodejs.org
- Python from https://www.python.org/downloads/
- ffmpeg with one of these options:

```powershell
winget install Gyan.FFmpeg
```

or:

```powershell
choco install ffmpeg
```

After installing, open a new terminal and check:

```bash
node --version
npm --version
python --version
ffmpeg -version
```

### macOS

```bash
brew install node python ffmpeg
```

### Ubuntu / WSL

```bash
sudo apt update
sudo apt install -y nodejs npm python3 python3-venv ffmpeg
```

## Daily Usage

After setup is complete:

```bash
cd ba-requirement-tool
npm run dev
```

Open:

```text
http://localhost:5173
```

The frontend runs on port `5173`. The backend runs on port `8099`.

Local runtime data is stored in:

- `backend/ba_tool.db`
- `backend/uploads/`
- `models/`

These are ignored by git and should not be committed.

## Optional Docker Usage

Docker is still supported if you prefer a containerized setup:

```bash
git clone https://github.com/duongdang1136/ba-requirement-tool.git
cd ba-requirement-tool
docker compose up --build
```

Then open → **http://localhost:5173**

Docker stores SQLite, uploads, and ASR models in Docker volumes. Stop with `Ctrl+C`, or use `docker compose down` if running in detached mode.

## For Developers

### Manual Dev Mode

**Prerequisites:** Python 3.10+, Node 18+, ffmpeg

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8099

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open → http://localhost:5173

### Speech-to-Text (sherpa-onnx)

`npm run setup` enables real local speech recognition automatically. For manual development, install sherpa-onnx and download a model manually:

1. Install sherpa-onnx:
```bash
pip install sherpa-onnx soundfile
```

2. Download the default Whisper small model:
```bash
mkdir -p models/asr
curl -L -o models/asr/sherpa-onnx-whisper-small.tar.bz2 \
  https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2
tar -xjf models/asr/sherpa-onnx-whisper-small.tar.bz2 -C models/asr
```

3. Set in `.env`:
```
ASR_MODEL_DIR=../models/asr/sherpa-onnx-whisper-small
```

See [sherpa-onnx docs](https://k2-fsa.github.io/sherpa/onnx/index.html) for model options (Vietnamese, English, multilingual).

### Environment variables

Copy `.env.example` → `.env` and edit as needed:

```bash
cp backend/.env.example backend/.env
```

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/ba_tool.db` | Database |
| `UPLOAD_DIR` | `./uploads` | Where files are stored |
| `ASR_MODEL_DIR` | `../models/asr/sherpa-onnx-whisper-small` | sherpa-onnx model path |
| `ASR_LANGUAGE` | `vi` | Primary meeting language |
| `MAX_UPLOAD_SIZE_MB` | `500` | File size limit |
| `LLM_PROVIDER` | `openai` | For Phase 2 extraction |
| `OPENAI_API_KEY` | `` | OpenAI key (Phase 2) |

### Project structure

```
ba-requirement-tool/
├── backend/              # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/routes/   # projects, meetings, transcript, requirements, export
│   │   ├── core/         # config, database
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # audio pipeline, extraction, export
│   └── Dockerfile
├── frontend/             # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/        # App, UploadPage
│   │   ├── components/   # TranscriptReview
│   │   ├── api/          # API client
│   │   └── types/
│   ├── nginx.conf
│   └── Dockerfile
├── features/final-docs/  # BA specification docs
│   ├── Core/
│   └── Project-Management/
├── docker-compose.yml
└── README.md
```

## Roadmap

### MVP ✅
- [x] Upload audio/video
- [x] Normalize with ffmpeg
- [x] Local STT with sherpa-onnx
- [x] Transcript review + edit
- [x] Export Markdown / TXT

### Phase 2
- [ ] Speaker diarization + rename
- [ ] Voice activity detection
- [ ] LLM requirement extraction
- [ ] Requirement review workspace (approve/reject)
- [ ] Open questions, decisions, action items
- [ ] Export DOCX, CSV, Jira

## Tech Stack

| | |
|---|---|
| Backend | FastAPI (Python) |
| Database | SQLite in Docker volume |
| Speech | sherpa-onnx (offline) |
| Audio | ffmpeg |
| Frontend | React + TypeScript + Vite |
| Serve | nginx (Docker) |

## License

MIT
