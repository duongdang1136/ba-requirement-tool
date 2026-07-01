import json
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.meeting import MediaFile, Meeting, ProcessingJob
from app.models.project import Project
from app.models.requirement import ActionItem, Decision, MeetingSummary, OpenQuestion

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


class MeetingSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    meeting_id: str
    summary: str
    key_points: str
    model_name: str
    created_at: datetime
    updated_at: datetime

class DecisionOut(BaseModel):
    id: str
    project_id: str
    meeting_id: Optional[str]
    title: str
    description: str
    owner: str
    source_quote: str
    created_at: datetime

    class Config:
        from_attributes = True


class ActionItemOut(BaseModel):
    id: str
    project_id: str
    meeting_id: Optional[str]
    task: str
    owner: str
    status: str
    source_quote: str
    created_at: datetime

    class Config:
        from_attributes = True


class OpenQuestionOut(BaseModel):
    id: str
    project_id: str
    meeting_id: Optional[str]
    question: str
    owner: str
    status: str
    source_quote: str
    created_at: datetime

    class Config:
        from_attributes = True


class MeetingArtifactsOut(BaseModel):
    summary: Optional[MeetingSummaryOut]
    decisions: List[DecisionOut]
    action_items: List[ActionItemOut]
    open_questions: List[OpenQuestionOut]


class ChunkUploadStatusOut(BaseModel):
    meeting_id: str
    file_name: str
    total_chunks: int
    received_chunks: list[int]
    complete: bool


class DiarizationOptions(BaseModel):
    diarization_num_speakers: Optional[int] = None
    diarization_cluster_threshold: Optional[float] = None

    def normalized_num_speakers(self) -> Optional[int]:
        if self.diarization_num_speakers is None or self.diarization_num_speakers <= 0:
            return None
        return self.diarization_num_speakers

    def normalized_threshold(self) -> Optional[float]:
        if self.diarization_cluster_threshold is None:
            return None
        return min(max(self.diarization_cluster_threshold, 0.0), 1.0)

    def normalized_payload(self) -> dict:
        return {
            "diarization_num_speakers": self.normalized_num_speakers(),
            "diarization_cluster_threshold": self.normalized_threshold(),
        }


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

    file_name = _safe_filename(file.filename)
    ext = Path(file_name).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    upload_dir = Path(settings.upload_dir) / meeting_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / file_name

    with open(stored_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = stored_path.stat().st_size
    if file_size > settings.max_upload_size_mb * 1024 * 1024:
        stored_path.unlink()
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    media = MediaFile(
        meeting_id=meeting_id,
        original_name=file_name,
        stored_path=str(stored_path),
        file_size=file_size,
        mime_type=file.content_type or "",
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return {"media_id": media.id, "file_name": file_name, "size": file_size}


def _validate_upload(meeting_id: str, filename: str, db: Session) -> Meeting:
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    return meeting


def _safe_filename(filename: str) -> str:
    safe = Path(filename).name
    if not safe or safe in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid file name")
    return safe


def _chunk_dir(meeting_id: str, upload_id: str) -> Path:
    safe_upload_id = "".join(ch for ch in upload_id if ch.isalnum() or ch in ("-", "_"))
    if not safe_upload_id:
        raise HTTPException(status_code=400, detail="Invalid upload_id")
    return Path(settings.upload_dir) / meeting_id / ".chunks" / safe_upload_id


@router.get("/{meeting_id}/media/chunks/{upload_id}", response_model=ChunkUploadStatusOut)
def get_chunk_upload_status(
    meeting_id: str,
    upload_id: str,
    file_name: str,
    total_chunks: int,
    db: Session = Depends(get_db),
):
    file_name = _safe_filename(file_name)
    _validate_upload(meeting_id, file_name, db)
    chunk_dir = _chunk_dir(meeting_id, upload_id)
    received = sorted(
        int(path.name.split(".")[0])
        for path in chunk_dir.glob("*.part")
        if path.name.split(".")[0].isdigit()
    ) if chunk_dir.exists() else []
    return ChunkUploadStatusOut(
        meeting_id=meeting_id,
        file_name=file_name,
        total_chunks=total_chunks,
        received_chunks=received,
        complete=len(received) == total_chunks,
    )


@router.post("/{meeting_id}/media/chunks", response_model=ChunkUploadStatusOut)
async def upload_media_chunk(
    meeting_id: str,
    upload_id: str = Form(...),
    file_name: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    file_size: int = Form(...),
    chunk: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_name = _safe_filename(file_name)
    _validate_upload(meeting_id, file_name, db)
    if total_chunks <= 0:
        raise HTTPException(status_code=400, detail="total_chunks must be greater than zero")
    if chunk_index < 0 or chunk_index >= total_chunks:
        raise HTTPException(status_code=400, detail="chunk_index is out of range")
    if file_size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    chunk_dir = _chunk_dir(meeting_id, upload_id)
    chunk_dir.mkdir(parents=True, exist_ok=True)
    part_path = chunk_dir / f"{chunk_index:08d}.part"
    with open(part_path, "wb") as f:
        shutil.copyfileobj(chunk.file, f)

    received = sorted(
        int(path.name.split(".")[0])
        for path in chunk_dir.glob("*.part")
        if path.name.split(".")[0].isdigit()
    )
    return ChunkUploadStatusOut(
        meeting_id=meeting_id,
        file_name=file_name,
        total_chunks=total_chunks,
        received_chunks=received,
        complete=len(received) == total_chunks,
    )


@router.post("/{meeting_id}/media/chunks/{upload_id}/complete")
def complete_chunk_upload(
    meeting_id: str,
    upload_id: str,
    file_name: str,
    total_chunks: int,
    file_size: int,
    mime_type: str = "",
    db: Session = Depends(get_db),
):
    file_name = _safe_filename(file_name)
    _validate_upload(meeting_id, file_name, db)
    if file_size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    upload_dir = Path(settings.upload_dir) / meeting_id
    chunk_dir = _chunk_dir(meeting_id, upload_id)
    stored_path = upload_dir / file_name
    missing = [i for i in range(total_chunks) if not (chunk_dir / f"{i:08d}.part").exists()]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing chunks: {missing[:10]}")

    with open(stored_path, "wb") as output:
        for i in range(total_chunks):
            with open(chunk_dir / f"{i:08d}.part", "rb") as part:
                shutil.copyfileobj(part, output)

    actual_size = stored_path.stat().st_size
    if actual_size != file_size:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Assembled file size mismatch: expected {file_size}, got {actual_size}")

    shutil.rmtree(chunk_dir, ignore_errors=True)
    media = MediaFile(
        meeting_id=meeting_id,
        original_name=file_name,
        stored_path=str(stored_path),
        file_size=actual_size,
        mime_type=mime_type,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return {"media_id": media.id, "file_name": file_name, "size": actual_size}


@router.post("/{meeting_id}/process")
def process_meeting(
    meeting_id: str,
    payload: Optional[DiarizationOptions] = None,
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    job = ProcessingJob(
        meeting_id=meeting_id,
        step="pipeline",
        status="queued",
        job_payload=json.dumps(payload.normalized_payload() if payload else {}),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"job_id": job.id, "status": "queued"}


@router.post("/{meeting_id}/diarization")
def enqueue_diarization(
    meeting_id: str,
    payload: Optional[DiarizationOptions] = None,
    db: Session = Depends(get_db),
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    job = ProcessingJob(
        meeting_id=meeting_id,
        step="diarize",
        status="queued",
        job_payload=json.dumps(payload.normalized_payload() if payload else {}),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"job_id": job.id, "status": "queued"}


@router.post("/{meeting_id}/summary")
def enqueue_meeting_summary(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    job = ProcessingJob(
        meeting_id=meeting_id,
        step="summary",
        status="queued",
        job_payload="{}",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"job_id": job.id, "status": "queued"}


@router.get("/{meeting_id}/artifacts", response_model=MeetingArtifactsOut)
def get_meeting_artifacts(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    summary = (
        db.query(MeetingSummary)
        .filter(MeetingSummary.meeting_id == meeting_id)
        .order_by(MeetingSummary.created_at.desc())
        .first()
    )
    decisions = (
        db.query(Decision)
        .filter(Decision.meeting_id == meeting_id)
        .order_by(Decision.created_at)
        .all()
    )
    action_items = (
        db.query(ActionItem)
        .filter(ActionItem.meeting_id == meeting_id)
        .order_by(ActionItem.created_at)
        .all()
    )
    open_questions = (
        db.query(OpenQuestion)
        .filter(OpenQuestion.meeting_id == meeting_id)
        .order_by(OpenQuestion.created_at)
        .all()
    )
    return MeetingArtifactsOut(
        summary=summary,
        decisions=decisions,
        action_items=action_items,
        open_questions=open_questions,
    )


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
