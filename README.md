# BA Requirement Tool

> Turn meeting recordings into reviewed, traceable requirement artifacts — fully offline.

```
Upload audio/video → Local STT → Transcript review → Edit → Export
```

## Quick Start (Docker)

**Requires:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
git clone https://github.com/duongdang1136/ba-requirement-tool.git
cd ba-requirement-tool
docker compose up --build
```

Then open → **http://localhost:5173**

That's it. No Python, no Node, no ffmpeg setup needed.

---

## What You Can Do (MVP)

- 📁 Upload meeting audio/video (`.mp3` `.wav` `.m4a` `.mp4`)
- ⚙️ Auto-process: normalize audio → transcribe with local speech-to-text
- 📝 Review transcript by timestamp
- ✏️ Edit transcript text (preserves original + traceability)
- 💾 Export reviewed transcript to **Markdown** or **TXT**

## For Developers

### Dev mode (without Docker)

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

The app ships with a **mock ASR** for testing. To enable real local speech recognition:

1. Install sherpa-onnx:
```bash
pip install sherpa-onnx soundfile
```

2. Download a model (example — SenseVoice multilingual):
```bash
mkdir -p models/asr
# Download from: https://github.com/k2-fsa/sherpa-onnx/releases
# Place model.int8.onnx + tokens.txt in models/asr/
```

3. Set in `.env`:
```
ASR_MODEL_DIR=./models/asr
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
| `ASR_MODEL_DIR` | `./models/asr` | sherpa-onnx model path |
| `ASR_LANGUAGE` | `en` | Primary meeting language |
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
| Database | SQLite → PostgreSQL |
| Speech | sherpa-onnx (offline) |
| Audio | ffmpeg |
| Frontend | React + TypeScript + Vite |
| Serve | nginx (Docker) |

## License

MIT
