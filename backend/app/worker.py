import json
import logging
import time
from datetime import timedelta

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.meeting import ProcessingJob
from app.services.audio.pipeline import _utcnow, rerun_diarization, run_pipeline
from app.services.extraction.ollama_service import extract_requirement_candidates, generate_meeting_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def _payload(job: ProcessingJob) -> dict:
    try:
        return json.loads(job.job_payload or "{}")
    except json.JSONDecodeError:
        logger.warning("Invalid job payload for job_id=%s: %s", job.id, job.job_payload)
        return {}


def recover_stale_jobs() -> int:
    db = SessionLocal()
    try:
        cutoff = _utcnow() - timedelta(minutes=settings.job_timeout_minutes)
        jobs = (
            db.query(ProcessingJob)
            .filter(ProcessingJob.status == "running", ProcessingJob.started_at < cutoff)
            .all()
        )
        for job in jobs:
            job.status = "failed"
            job.error = f"Job was marked failed after running longer than {settings.job_timeout_minutes} minutes."
            job.finished_at = _utcnow()
        db.commit()
        return len(jobs)
    finally:
        db.close()


def claim_next_job() -> ProcessingJob | None:
    db = SessionLocal()
    try:
        job = (
            db.query(ProcessingJob)
            .filter(ProcessingJob.status == "queued")
            .order_by(ProcessingJob.created_at)
            .first()
        )
        if not job:
            return None

        job.status = "running"
        job.started_at = _utcnow()
        db.commit()
        db.refresh(job)
        db.expunge(job)
        return job
    finally:
        db.close()


def run_job(job: ProcessingJob):
    payload = _payload(job)
    num_speakers = payload.get("diarization_num_speakers")
    threshold = payload.get("diarization_cluster_threshold")

    logger.info("Running job_id=%s meeting_id=%s step=%s", job.id, job.meeting_id, job.step)
    if job.step == "pipeline":
        run_pipeline(job.meeting_id, job.id, num_speakers, threshold)
    elif job.step == "diarize":
        rerun_diarization(job.meeting_id, job.id, num_speakers, threshold)
    elif job.step == "summary":
        run_summary_job(job.meeting_id, job.id)
    elif job.step == "extract_requirements":
        run_requirement_extraction_job(job.meeting_id, job.id)
    else:
        db = SessionLocal()
        try:
            stored = db.query(ProcessingJob).filter(ProcessingJob.id == job.id).first()
            if stored:
                stored.status = "failed"
                stored.error = f"Unknown queued job step: {job.step}"
                stored.finished_at = _utcnow()
                db.commit()
        finally:
            db.close()


def _run_llm_job(job_id: str, step: str, work):
    db = SessionLocal()
    try:
        stored = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not stored:
            return
        stored.status = "running"
        stored.step = step
        stored.started_at = stored.started_at or _utcnow()
        stored.progress = 20
        db.commit()

        work(db)

        stored.status = "completed"
        stored.progress = 100
        stored.finished_at = _utcnow()
        db.commit()
    except Exception as exc:
        db.rollback()
        stored = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if stored:
            stored.status = "failed"
            stored.error = str(exc)
            stored.finished_at = _utcnow()
            db.commit()
        logger.exception("LLM job failed job_id=%s step=%s", job_id, step)
    finally:
        db.close()


def run_summary_job(meeting_id: str, job_id: str):
    def work(db):
        generate_meeting_summary(db, meeting_id)

    _run_llm_job(job_id, "summary", work)


def run_requirement_extraction_job(meeting_id: str, job_id: str):
    def work(db):
        extract_requirement_candidates(db, meeting_id)

    _run_llm_job(job_id, "extract_requirements", work)


def run_worker():
    init_db()
    logger.info("Worker started")
    while True:
        recovered = recover_stale_jobs()
        if recovered:
            logger.warning("Recovered %s stale job(s)", recovered)

        job = claim_next_job()
        if job:
            run_job(job)
            continue

        time.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    run_worker()
