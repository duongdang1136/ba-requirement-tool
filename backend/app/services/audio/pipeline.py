"""
Audio processing pipeline:
normalize → VAD (optional) → ASR → diarize (optional) → merge

MVP 1: normalize + ASR only (no diarization)
"""
import subprocess
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.meeting import ProcessingJob, MediaFile
from app.models.transcript import TranscriptSegment


def run_pipeline(meeting_id: str, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        media = db.query(MediaFile).filter(MediaFile.meeting_id == meeting_id).order_by(MediaFile.created_at.desc()).first()

        if not media:
            job.status = "failed"
            job.error = "No media file found"
            db.commit()
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        job.step = "normalize"
        job.progress = 5
        db.commit()

        # Step 1: Normalize audio
        normalized_path = _normalize_audio(media.stored_path, meeting_id)
        if not normalized_path:
            job.status = "failed"
            job.error = "ffmpeg normalization failed"
            db.commit()
            return

        media.normalized_path = str(normalized_path)
        job.progress = 30
        job.step = "asr"
        db.commit()

        # Step 2: Run ASR
        segments = _run_asr(normalized_path, meeting_id)
        if segments is None:
            job.status = "failed"
            job.error = "ASR failed"
            db.commit()
            return

        job.progress = 80
        job.step = "merge"
        db.commit()

        # Step 3: Store transcript segments
        for i, seg in enumerate(segments):
            transcript_seg = TranscriptSegment(
                meeting_id=meeting_id,
                start=seg["start"],
                end=seg["end"],
                speaker_label="SPEAKER_00",
                original_text=seg["text"],
                sequence=i,
            )
            db.add(transcript_seg)

        job.status = "completed"
        job.progress = 100
        job.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            job.finished_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def _normalize_audio(input_path: str, meeting_id: str) -> Path | None:
    """Convert input audio to 16kHz mono WAV using ffmpeg."""
    out_dir = Path(settings.upload_dir) / meeting_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "normalized.wav"

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(out_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return None
        return out_path
    except Exception:
        return None


def _run_asr(audio_path: Path, meeting_id: str) -> list | None:
    """
    Run sherpa-onnx ASR on normalized audio.
    Returns list of {start, end, text} dicts.

    Requires sherpa-onnx to be installed and model configured.
    Falls back to mock output if sherpa-onnx not available (dev mode).
    """
    try:
        import sherpa_onnx

        model_dir = Path(settings.asr_model_dir)
        recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=str(model_dir / "model.int8.onnx"),
            tokens=str(model_dir / "tokens.txt"),
            num_threads=4,
            use_gpu=False,
        )

        stream = recognizer.create_stream()
        import soundfile as sf
        samples, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=False)
        stream.accept_waveform(sample_rate, samples)
        recognizer.decode_stream(stream)
        result = stream.result

        # sherpa-onnx SenseVoice gives timestamps per token/word
        # For MVP: return as single segment with full text
        if result.text.strip():
            return [{"start": 0.0, "end": len(samples) / sample_rate, "text": result.text.strip()}]
        return []

    except ImportError:
        # Dev fallback: mock segments
        return [
            {"start": 0.0, "end": 5.0, "text": "[sherpa-onnx not installed — mock segment 1]"},
            {"start": 5.1, "end": 10.0, "text": "[Install sherpa-onnx and configure models to get real transcription]"},
        ]
    except Exception as e:
        return None
