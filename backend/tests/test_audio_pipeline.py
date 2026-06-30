import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import worker
from app.core.database import Base
from app.models import project  # noqa: F401
from app.models.meeting import MediaFile, ProcessingJob
from app.models.transcript import TranscriptSegment
from app.services.audio import pipeline


class AudioPipelineHelperTests(unittest.TestCase):
    def test_merge_intervals_merges_short_gaps_within_max_duration(self):
        result = pipeline._merge_intervals([
            {"start": 0.0, "end": 4.0},
            {"start": 4.5, "end": 8.0},
            {"start": 12.0, "end": 14.0},
        ], gap=1.0, max_duration=10.0)

        self.assertEqual(result, [
            {"start": 0.0, "end": 8.0},
            {"start": 12.0, "end": 14.0},
        ])

    def test_merge_intervals_does_not_exceed_max_duration(self):
        result = pipeline._merge_intervals([
            {"start": 0.0, "end": 20.0},
            {"start": 20.5, "end": 29.0},
        ], gap=1.0, max_duration=28.0)

        self.assertEqual(result, [
            {"start": 0.0, "end": 20.0},
            {"start": 20.5, "end": 29.0},
        ])

    def test_split_intervals_caps_long_chunks_with_overlap(self):
        result = pipeline._split_intervals(
            [{"start": 0.0, "end": 65.0}],
            duration=65.0,
            max_duration=28.0,
            padding=0.0,
            overlap=1.0,
        )

        self.assertEqual(result, [
            {"start": 0.0, "end": 28.0},
            {"start": 27.0, "end": 55.0},
            {"start": 54.0, "end": 65.0},
        ])

    def test_assign_speaker_uses_largest_overlap(self):
        speaker = pipeline._assign_speaker(10.0, 20.0, [
            {"start": 0.0, "end": 12.0, "speaker": "SPEAKER_00"},
            {"start": 12.0, "end": 22.0, "speaker": "SPEAKER_01"},
        ])

        self.assertEqual(speaker, "SPEAKER_01")


class AudioPipelineRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db_path = Path(self.tmp.name) / "test.db"
        self.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
        self.tmp.cleanup()

    def test_diarization_failure_keeps_transcript_and_completes_with_warning(self):
        session = self.Session()
        meeting_id = "meeting-1"
        job = ProcessingJob(id="job-1", meeting_id=meeting_id, step="normalize", status="queued")
        media = MediaFile(
            id="media-1",
            meeting_id=meeting_id,
            original_name="meeting.wav",
            stored_path="meeting.wav",
            file_size=123,
            mime_type="audio/wav",
        )
        session.add_all([job, media])
        session.commit()
        session.close()

        with (
            patch.object(pipeline, "SessionLocal", self.Session),
            patch.object(pipeline, "_normalize_audio", return_value=Path(self.tmp.name) / "normalized.wav"),
            patch.object(pipeline, "_detect_speech_intervals", return_value=[{"start": 0.0, "end": 2.0}]),
            patch.object(pipeline, "_run_whisper_asr", return_value=[
                {"start": 0.0, "end": 2.0, "text": "hello", "speaker": "SPEAKER_00"},
            ]),
            patch.object(pipeline, "_run_diarization", return_value=None),
        ):
            pipeline.run_pipeline(meeting_id, "job-1")

        session = self.Session()
        stored_job = session.query(ProcessingJob).filter(ProcessingJob.id == "job-1").one()
        segments = session.query(TranscriptSegment).filter(TranscriptSegment.meeting_id == meeting_id).all()

        self.assertEqual(stored_job.status, "completed")
        self.assertEqual(stored_job.step, "diarize_failed")
        self.assertIn("Transcript is available", stored_job.error)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].original_text, "hello")
        self.assertEqual(segments[0].speaker_label, "SPEAKER_00")
        session.close()

    def test_rerun_diarization_updates_existing_segments_only(self):
        normalized_path = Path(self.tmp.name) / "normalized.wav"
        normalized_path.write_bytes(b"placeholder")

        session = self.Session()
        meeting_id = "meeting-2"
        job = ProcessingJob(id="job-2", meeting_id=meeting_id, step="diarize", status="queued")
        media = MediaFile(
            id="media-2",
            meeting_id=meeting_id,
            original_name="meeting.wav",
            stored_path="meeting.wav",
            normalized_path=str(normalized_path),
            file_size=123,
            mime_type="audio/wav",
        )
        segment = TranscriptSegment(
            id="segment-1",
            meeting_id=meeting_id,
            start=10.0,
            end=20.0,
            speaker_label="SPEAKER_00",
            original_text="keep me",
            sequence=0,
        )
        session.add_all([job, media, segment])
        session.commit()
        session.close()

        with (
            patch.object(pipeline, "SessionLocal", self.Session),
            patch.object(pipeline, "_run_diarization", return_value=[
                {"start": 0.0, "end": 12.0, "speaker": "SPEAKER_00"},
                {"start": 12.0, "end": 25.0, "speaker": "SPEAKER_01"},
            ]) as diarize,
        ):
            pipeline.rerun_diarization(meeting_id, "job-2", 2, 0.4)

        diarize.assert_called_once_with(normalized_path, 2, 0.4)

        session = self.Session()
        stored_job = session.query(ProcessingJob).filter(ProcessingJob.id == "job-2").one()
        stored_segment = session.query(TranscriptSegment).filter(TranscriptSegment.id == "segment-1").one()

        self.assertEqual(stored_job.status, "completed")
        self.assertEqual(stored_segment.original_text, "keep me")
        self.assertEqual(stored_segment.speaker_label, "SPEAKER_01")
        session.close()

    def test_worker_dispatches_queued_pipeline_job_with_payload(self):
        session = self.Session()
        job = ProcessingJob(
            id="job-3",
            meeting_id="meeting-3",
            step="pipeline",
            status="queued",
            job_payload='{"diarization_num_speakers": 2, "diarization_cluster_threshold": 0.45}',
        )
        session.add(job)
        session.commit()
        session.close()

        with (
            patch.object(worker, "SessionLocal", self.Session),
            patch.object(worker, "run_pipeline") as run_pipeline,
        ):
            claimed = worker.claim_next_job()
            worker.run_job(claimed)

        run_pipeline.assert_called_once_with("meeting-3", "job-3", 2, 0.45)


if __name__ == "__main__":
    unittest.main()
