import os
import shutil
import threading
from pathlib import Path
from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.models.meeting import Meeting, MediaFile, ProcessingJob
from app.models.project import Project

router = APIRouter()


class MeetingCreate(BaseModel):
    project_id: str
    title: str
    meeting_date: Optional[date] = None
    participants: str = "[]"
    notes: str = ""


class MeetingOut(BaseModel):
    id: str
    project_id: str
    title: str
    meeting_date: Optional[date]
    participants: str
    notes: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcessingStatusOut(BaseModel):
    meeting_id: str
    step: str
    status: str
    progress: int
    error: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


@router.post("", response_model=MeetingOut, status_code=201)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    meeting = Meeting(**payload.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("/project/{project_id}", response_model=List[MeetingOut])
def list_meetings(project_id: str, db: Session = Depends(get_db)):
    return db.query(Meeting).filter(Meeting.project_id == project_id).order_by(Meeting.created_at.desc()).all()


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/{meeting_id}/media")
async def upload_media(
    meeting_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    upload_dir = Path(settings.upload_dir) / meeting_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / file.filename

    with open(stored_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = stored_path.stat().st_size
    if file_size > settings.max_upload_size_mb * 1024 * 1024:
        stored_path.unlink()
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    media = MediaFile(
        meeting_id=meeting_id,
        original_name=file.filename,
        stored_path=str(stored_path),
        file_size=file_size,
        mime_type=file.content_type or "",
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return {"media_id": media.id, "file_name": file.filename, "size": file_size}


@router.post("/{meeting_id}/process")
def process_meeting(meeting_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Kick off the full processing pipeline: normalize → ASR → merge."""
    from app.services.audio.pipeline import run_pipeline

    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    job = ProcessingJob(meeting_id=meeting_id, step="normalize", status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_pipeline, meeting_id, job.id)
    return {"job_id": job.id, "status": "queued"}


@router.get("/{meeting_id}/status", response_model=ProcessingStatusOut)
def get_processing_status(meeting_id: str, db: Session = Depends(get_db)):
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.meeting_id == meeting_id)
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="No processing job found for this meeting")
    return ProcessingStatusOut(
        meeting_id=meeting_id,
        step=job.step,
        status=job.status,
        progress=job.progress,
        error=job.error,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )
