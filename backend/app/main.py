from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import projects, meetings, transcript, requirements, export, config

app = FastAPI(
    title="BA Requirement Tool",
    description="Turn meeting recordings into reviewed, traceable requirement artifacts.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(meetings.router, prefix="/api/meetings", tags=["meetings"])
app.include_router(transcript.router, prefix="/api/transcript-segments", tags=["transcript"])
app.include_router(requirements.router, prefix="/api/requirements", tags=["requirements"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.on_event("startup")
async def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
