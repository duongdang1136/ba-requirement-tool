from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.meeting import Meeting, ProcessingJob
from app.models.requirement import RequirementCandidate, Requirement

router = APIRouter()


class CandidateOut(BaseModel):
    id: str
    meeting_id: str
    title: str
    description: str
    type: str
    priority: str
    source_quote: str
    source_segment_ids: str
    review_state: str
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    source_quote: Optional[str] = None


class ApprovePayload(BaseModel):
    actor: str = ""
    business_value: str = ""
    acceptance_criteria: str = ""
    priority: Optional[str] = None


class RejectPayload(BaseModel):
    reason: str


class RequirementOut(BaseModel):
    id: str
    project_id: str
    meeting_id: str
    title: str
    description: str
    type: str
    priority: str
    status: str
    actor: str
    business_value: str
    acceptance_criteria: str
    source_quote: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/candidates/meeting/{meeting_id}", response_model=List[CandidateOut])
def list_candidates(meeting_id: str, db: Session = Depends(get_db)):
    return (
        db.query(RequirementCandidate)
        .filter(RequirementCandidate.meeting_id == meeting_id)
        .order_by(RequirementCandidate.created_at)
        .all()
    )


@router.post("/meeting/{meeting_id}/extract")
def enqueue_extract_requirements(meeting_id: str, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    job = ProcessingJob(
        meeting_id=meeting_id,
        step="extract_requirements",
        status="queued",
        job_payload="{}",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"job_id": job.id, "status": "queued"}


@router.patch("/candidates/{candidate_id}", response_model=CandidateOut)
def edit_candidate(candidate_id: str, payload: CandidateUpdate, db: Session = Depends(get_db)):
    c = db.query(RequirementCandidate).filter(RequirementCandidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@router.post("/candidates/{candidate_id}/approve", response_model=RequirementOut)
def approve_candidate(candidate_id: str, payload: ApprovePayload, db: Session = Depends(get_db)):
    c = db.query(RequirementCandidate).filter(RequirementCandidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")

    from app.models.meeting import Meeting
    meeting = db.query(Meeting).filter(Meeting.id == c.meeting_id).first()

    req = Requirement(
        project_id=meeting.project_id,
        meeting_id=c.meeting_id,
        candidate_id=c.id,
        title=c.title,
        description=c.description,
        type=c.type,
        priority=payload.priority or c.priority,
        status="approved",
        actor=payload.actor,
        business_value=payload.business_value,
        acceptance_criteria=payload.acceptance_criteria,
        source_quote=c.source_quote,
        source_segments=c.source_segment_ids,
    )
    db.add(req)
    c.review_state = "approved"
    db.commit()
    db.refresh(req)
    return req


@router.post("/candidates/{candidate_id}/reject")
def reject_candidate(candidate_id: str, payload: RejectPayload, db: Session = Depends(get_db)):
    c = db.query(RequirementCandidate).filter(RequirementCandidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    c.review_state = "rejected"
    c.rejection_reason = payload.reason
    db.commit()
    return {"status": "rejected", "candidate_id": candidate_id}


@router.get("/project/{project_id}", response_model=List[RequirementOut])
def list_requirements(project_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Requirement)
        .filter(Requirement.project_id == project_id)
        .order_by(Requirement.created_at)
        .all()
    )
