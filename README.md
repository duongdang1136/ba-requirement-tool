# BA Requirement Tool

> An AI-powered Business Analyst assistant that transforms meeting audio/video recordings into structured, reviewable, and exportable requirement artifacts.

---

## Overview

The **BA Requirement Tool** automates the most tedious part of a BA's job: turning meeting recordings into actionable requirement documents. It transcribes audio, extracts candidate requirements using LLMs, lets BAs review and approve them, and exports polished documentation in multiple formats.

### Key Capabilities

| Capability | MVP (Phase 1) | Phase 2+ |
|---|---|---|
| Upload audio/video | ✅ | ✅ |
| Audio normalization (ffmpeg) | ✅ | ✅ |
| Speech-to-text (offline, sherpa-onnx) | ✅ | ✅ |
| Transcript preview & editing | ✅ | ✅ |
| Speaker diarization | ❌ | ✅ |
| LLM requirement extraction | ❌ | ✅ |
| Requirement review workspace | ❌ | ✅ |
| Export (MD, DOCX, CSV, JSON, Jira) | MD/TXT only | ✅ all formats |
| Project management | Basic | Full |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| Database | SQLite (MVP) → PostgreSQL (Phase 2) |
| Speech Processing | sherpa-onnx (offline STT) |
| Audio Normalization | ffmpeg |
| LLM Integration | Configurable — local (Ollama) or cloud |
| Frontend | React + TypeScript (Vite) |

---

## Documentation Structure

```
features/final-docs/
├── Core/
│   ├── Meeting-Processing/       # Upload, normalize, transcribe audio
│   │   ├── README.md
│   │   ├── product/functional-specification.md
│   │   ├── api/technical-contract.md
│   │   └── design/design-contract.md
│   ├── Transcript-Review/        # Preview, edit, correct transcript
│   │   ├── README.md
│   │   ├── product/functional-specification.md
│   │   ├── api/technical-contract.md
│   │   └── design/design-contract.md
│   ├── Requirement-Extraction/   # LLM-powered extraction of FRs, NFRs, etc.
│   │   ├── README.md
│   │   ├── product/functional-specification.md
│   │   ├── api/technical-contract.md
│   │   └── design/design-contract.md
│   ├── Requirement-Review/       # Approve/reject/edit candidate requirements
│   │   ├── README.md
│   │   ├── product/functional-specification.md
│   │   ├── api/technical-contract.md
│   │   └── design/design-contract.md
│   └── Export/                   # Export finalized docs in multiple formats
│       ├── README.md
│       ├── product/functional-specification.md
│       ├── api/technical-contract.md
│       └── design/design-contract.md
└── Project-Management/
    └── Project-and-Meeting/      # Project & meeting lifecycle management
        ├── README.md
        ├── product/functional-specification.md
        ├── api/technical-contract.md
        └── design/design-contract.md
```

---

## Core Data Model

```
Project
  └── Meeting
        ├── MediaFile
        ├── ProcessingJob
        ├── TranscriptSegment (original_text / edited_text)
        ├── Speaker
        └── RequirementCandidate
              └── Requirement (approved)
                    ├── OpenQuestion
                    ├── Decision
                    ├── ActionItem
                    └── GlossaryTerm
ExportJob (belongs to Project)
```

---

## Feature Map & Status

| Feature | Phase | Status |
|---|---|---|
| Project & Meeting Management | MVP | 🟡 In Design |
| Meeting Processing (Upload + STT) | MVP | 🟡 In Design |
| Transcript Review & Edit | MVP | 🟡 In Design |
| Requirement Extraction (LLM) | Phase 2 | 🔵 Planned |
| Requirement Review Workspace | Phase 2 | 🔵 Planned |
| Export (all formats) | Phase 2 | 🔵 Planned |

---

## Getting Started (Development)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

---

*Last updated: 2026-06-29*
*Authors: BA Team / Pulse Labs*
