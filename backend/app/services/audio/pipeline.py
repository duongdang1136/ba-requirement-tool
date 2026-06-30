"""
Audio processing pipeline:
normalize -> VAD -> ASR -> store transcript -> diarization.
"""
import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.meeting import MediaFile, ProcessingJob
from app.models.transcript import TranscriptSegment

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class TranscriptCandidate(TypedDict):
    start: float
    end: float
    text: str
    speaker: str


class SpeechInterval(TypedDict):
    start: float
    end: float


class SpeakerTurn(TypedDict):
    start: float
    end: float
    speaker: str


def run_pipeline(
    meeting_id: str,
    job_id: str,
    diarization_num_speakers: int | None = None,
    diarization_cluster_threshold: float | None = None,
):
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        media = (
            db.query(MediaFile)
            .filter(MediaFile.meeting_id == meeting_id)
            .order_by(MediaFile.created_at.desc())
            .first()
        )

        if not job:
            logger.error("Processing job not found for meeting_id=%s job_id=%s", meeting_id, job_id)
            return

        if not media:
            job.status = "failed"
            job.error = "No media file found"
            logger.error("No media file found for meeting_id=%s job_id=%s", meeting_id, job_id)
            db.commit()
            return

        job.status = "running"
        job.started_at = _utcnow()
        job.step = "normalize"
        job.progress = 10
        db.commit()

        normalized_path = _normalize_audio(media.stored_path, meeting_id)
        if not normalized_path:
            job.status = "failed"
            job.error = "Audio normalization failed. Check that ffmpeg is installed and the uploaded file is readable."
            logger.error("Audio normalization failed for meeting_id=%s job_id=%s path=%s", meeting_id, job_id, media.stored_path)
            db.commit()
            return

        media.normalized_path = str(normalized_path)
        job.progress = 30
        job.step = "vad"
        db.commit()

        speech_intervals = _detect_speech_intervals(normalized_path)
        if speech_intervals is None:
            job.status = "failed"
            job.error = "Voice activity detection failed. Check the VAD model path and normalized audio format."
            logger.error("VAD failed for meeting_id=%s job_id=%s audio=%s", meeting_id, job_id, normalized_path)
            db.commit()
            return

        job.progress = 45
        job.step = "asr"
        db.commit()

        segments = _run_whisper_asr(normalized_path, speech_intervals)
        if segments is None:
            job.status = "failed"
            job.error = "Speech recognition failed. Check the ASR model path and sherpa-onnx installation."
            logger.error("ASR failed for meeting_id=%s job_id=%s audio=%s", meeting_id, job_id, normalized_path)
            db.commit()
            return

        job.progress = 75
        job.step = "store_transcript"
        db.commit()

        stored_segments = _replace_transcript_segments(db, meeting_id, segments)

        job.progress = 85
        job.step = "diarize"
        db.commit()

        speaker_turns = _run_diarization(
            normalized_path,
            diarization_num_speakers,
            diarization_cluster_threshold,
        )
        if speaker_turns:
            for segment in stored_segments:
                segment.speaker_label = _assign_speaker(segment.start, segment.end, speaker_turns)
            job.step = "completed"
        else:
            job.step = "diarize_failed"
            job.error = "Transcript is available, but speaker diarization failed or models are unavailable. Speaker labels were left as SPEAKER_00."
            logger.warning("Diarization failed after transcript storage for meeting_id=%s job_id=%s", meeting_id, job_id)

        job.status = "completed"
        job.progress = 100
        job.finished_at = _utcnow()
        db.commit()

    except Exception as exc:
        db.rollback()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.finished_at = _utcnow()
            db.commit()
        logger.exception("Pipeline failed for meeting_id=%s job_id=%s", meeting_id, job_id)
    finally:
        db.close()


def _replace_transcript_segments(db, meeting_id: str, segments: list[TranscriptCandidate]) -> list[TranscriptSegment]:
    db.query(TranscriptSegment).filter(TranscriptSegment.meeting_id == meeting_id).delete()

    stored_segments: list[TranscriptSegment] = []
    for i, seg in enumerate(segments):
        text = seg["text"].strip()
        if not text:
            continue
        segment = TranscriptSegment(
            meeting_id=meeting_id,
            start=seg["start"],
            end=seg["end"],
            speaker_label=seg.get("speaker", "SPEAKER_00"),
            original_text=text,
            sequence=i,
        )
        db.add(segment)
        stored_segments.append(segment)

    db.commit()
    return stored_segments


def rerun_diarization(
    meeting_id: str,
    job_id: str,
    diarization_num_speakers: int | None = None,
    diarization_cluster_threshold: float | None = None,
):
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        media = (
            db.query(MediaFile)
            .filter(MediaFile.meeting_id == meeting_id)
            .order_by(MediaFile.created_at.desc())
            .first()
        )
        segments = (
            db.query(TranscriptSegment)
            .filter(TranscriptSegment.meeting_id == meeting_id)
            .order_by(TranscriptSegment.sequence)
            .all()
        )

        if not job:
            logger.error("Diarization job not found for meeting_id=%s job_id=%s", meeting_id, job_id)
            return
        if not media:
            job.status = "failed"
            job.error = "No media file found"
            db.commit()
            return
        if not segments:
            job.status = "failed"
            job.error = "No transcript segments found. Run meeting processing before re-running diarization."
            db.commit()
            return

        job.status = "running"
        job.started_at = _utcnow()
        job.step = "diarize"
        job.progress = 10
        db.commit()

        normalized_path = Path(media.normalized_path) if media.normalized_path else None
        if not normalized_path or not normalized_path.exists():
            normalized_path = _normalize_audio(media.stored_path, meeting_id)
            if not normalized_path:
                job.status = "failed"
                job.error = "Audio normalization failed. Check that ffmpeg is installed and the uploaded file is readable."
                db.commit()
                return
            media.normalized_path = str(normalized_path)
            db.commit()

        speaker_turns = _run_diarization(
            normalized_path,
            diarization_num_speakers,
            diarization_cluster_threshold,
        )
        if not speaker_turns:
            job.status = "failed"
            job.error = "Speaker diarization failed or models are unavailable. Existing transcript text was not changed."
            job.finished_at = _utcnow()
            db.commit()
            return

        for segment in segments:
            segment.speaker_label = _assign_speaker(segment.start, segment.end, speaker_turns)

        job.status = "completed"
        job.step = "completed"
        job.progress = 100
        job.finished_at = _utcnow()
        db.commit()

    except Exception as exc:
        db.rollback()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(exc)
            job.finished_at = _utcnow()
            db.commit()
        logger.exception("Re-run diarization failed for meeting_id=%s job_id=%s", meeting_id, job_id)
    finally:
        db.close()


def _normalize_audio(input_path: str, meeting_id: str) -> Path | None:
    """Convert any audio/video to 16kHz mono WAV using ffmpeg."""
    out_dir = Path(settings.upload_dir) / meeting_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "normalized.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(out_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.error("ffmpeg failed for input_path=%s stderr=%s", input_path, result.stderr[-500:])
            return None
        return out_path
    except FileNotFoundError:
        logger.error("ffmpeg executable not found")
        return None
    except Exception as exc:
        logger.exception("ffmpeg normalization raised for input_path=%s: %s", input_path, exc)
        return None


def _detect_speech_intervals(audio_path: Path) -> list[SpeechInterval] | None:
    """Return speech intervals in the original audio timeline."""
    try:
        import numpy as np
        import sherpa_onnx
        import soundfile as sf

        vad_model = Path(settings.vad_model_path)
        if not vad_model.exists():
            logger.error("VAD model not found at %s", vad_model)
            return None

        samples, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=True)
        samples = np.ascontiguousarray(samples[:, 0])
        if sample_rate != 16000:
            logger.error("VAD expected 16kHz normalized audio, got %s", sample_rate)
            return None

        config = sherpa_onnx.VadModelConfig()
        config.silero_vad.model = str(vad_model)
        config.silero_vad.threshold = 0.5
        config.silero_vad.min_silence_duration = 0.7
        config.silero_vad.min_speech_duration = 0.25
        config.silero_vad.max_speech_duration = 28
        config.sample_rate = sample_rate

        vad = sherpa_onnx.VoiceActivityDetector(config, buffer_size_in_seconds=60)
        window_size = config.silero_vad.window_size
        offset = 0
        intervals: list[SpeechInterval] = []

        while offset + window_size <= len(samples):
            vad.accept_waveform(samples[offset: offset + window_size])
            offset += window_size
            while not vad.empty():
                segment = vad.front
                intervals.append({
                    "start": round(segment.start / sample_rate, 2),
                    "end": round((segment.start + len(segment.samples)) / sample_rate, 2),
                })
                vad.pop()

        if offset < len(samples):
            vad.accept_waveform(samples[offset:])

        vad.flush()
        while not vad.empty():
            segment = vad.front
            intervals.append({
                "start": round(segment.start / sample_rate, 2),
                "end": round((segment.start + len(segment.samples)) / sample_rate, 2),
            })
            vad.pop()

        return _merge_intervals(intervals)

    except ImportError:
        logger.exception("VAD dependencies are not installed")
        return None
    except Exception as exc:
        logger.exception("VAD failed: %s", exc)
        return None


def _merge_intervals(intervals: list[SpeechInterval], gap: float = 1.2, max_duration: float = 28.0) -> list[SpeechInterval]:
    if not intervals:
        return []

    merged: list[SpeechInterval] = []
    current = dict(intervals[0])
    for interval in intervals[1:]:
        would_merge = interval["start"] - current["end"] <= gap
        would_fit = interval["end"] - current["start"] <= max_duration
        if would_merge and would_fit:
            current["end"] = max(current["end"], interval["end"])
        else:
            merged.append({"start": current["start"], "end": current["end"]})
            current = dict(interval)

    merged.append({"start": current["start"], "end": current["end"]})
    return merged


def _split_intervals(
    intervals: list[SpeechInterval],
    duration: float,
    max_duration: float = 28.0,
    padding: float = 0.6,
    overlap: float = 1.0,
) -> list[SpeechInterval]:
    """Whisper ONNX only accepts chunks under 30s, so enforce a hard cap with context."""
    split: list[SpeechInterval] = []
    for interval in intervals:
        start = max(0.0, interval["start"] - padding)
        end = min(duration, interval["end"] + padding)
        while end - start > max_duration:
            split.append({"start": round(start, 2), "end": round(start + max_duration, 2)})
            start += max_duration - overlap
        if end > start:
            split.append({"start": round(start, 2), "end": round(end, 2)})
    return split


def _run_whisper_asr(audio_path: Path, speech_intervals: list[SpeechInterval]) -> list[TranscriptCandidate] | None:
    """Run sherpa-onnx Whisper ASR and return transcript candidates."""
    try:
        import sherpa_onnx
        import soundfile as sf

        model_dir = Path(settings.asr_model_dir)
        encoder = model_dir / "small-encoder.int8.onnx"
        decoder = model_dir / "small-decoder.int8.onnx"
        tokens = model_dir / "small-tokens.txt"

        if not encoder.exists():
            logger.error("ASR Whisper model not found at %s", model_dir)
            return None

        recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=str(encoder),
            decoder=str(decoder),
            tokens=str(tokens),
            num_threads=settings.asr_num_threads,
            decoding_method="greedy_search",
            language=settings.asr_language,
            task="transcribe",
        )

        samples, sample_rate = sf.read(str(audio_path), dtype="float32", always_2d=False)
        duration = len(samples) / sample_rate

        if not speech_intervals:
            return [{"start": 0.0, "end": duration, "text": "(No speech detected)", "speaker": "SPEAKER_00"}]

        segments: list[TranscriptCandidate] = []
        for interval in _split_intervals(speech_intervals, duration):
            start_sec = max(0.0, interval["start"])
            end_sec = min(duration, interval["end"])
            start_sample = int(start_sec * sample_rate)
            end_sample = int(end_sec * sample_rate)
            chunk = samples[start_sample:end_sample]
            if len(chunk) == 0:
                continue

            stream = recognizer.create_stream()
            stream.accept_waveform(sample_rate, chunk)
            recognizer.decode_stream(stream)
            text = stream.result.text.strip()

            if text:
                segments.append({
                    "start": round(start_sec, 2),
                    "end": round(end_sec, 2),
                    "text": text,
                    "speaker": "SPEAKER_00",
                })

        return segments if segments else [{"start": 0.0, "end": duration, "text": "(No recognizable audio)", "speaker": "SPEAKER_00"}]

    except ImportError:
        logger.exception("ASR dependencies are not installed")
        return None
    except Exception as exc:
        logger.exception("ASR failed: %s", exc)
        return None


def _run_diarization(
    audio_path: Path,
    num_speakers: int | None = None,
    cluster_threshold: float | None = None,
) -> list[SpeakerTurn] | None:
    try:
        import numpy as np
        import sherpa_onnx
        import soundfile as sf

        segmentation_model = Path(settings.diarization_segmentation_model)
        embedding_model = Path(settings.diarization_embedding_model)
        if not segmentation_model.exists() or not embedding_model.exists():
            logger.error("Diarization models not found: segmentation=%s embedding=%s", segmentation_model, embedding_model)
            return None

        config = sherpa_onnx.OfflineSpeakerDiarizationConfig(
            segmentation=sherpa_onnx.OfflineSpeakerSegmentationModelConfig(
                pyannote=sherpa_onnx.OfflineSpeakerSegmentationPyannoteModelConfig(
                    model=str(segmentation_model),
                ),
            ),
            embedding=sherpa_onnx.SpeakerEmbeddingExtractorConfig(
                model=str(embedding_model),
            ),
            clustering=sherpa_onnx.FastClusteringConfig(
                num_clusters=num_speakers if num_speakers else -1,
                threshold=cluster_threshold if cluster_threshold is not None else settings.diarization_cluster_threshold,
            ),
            min_duration_on=0.3,
            min_duration_off=0.5,
        )
        if not config.validate():
            logger.error("Diarization config is invalid")
            return None

        diarizer = sherpa_onnx.OfflineSpeakerDiarization(config)
        chunk_seconds = max(60, settings.diarization_chunk_minutes * 60)
        turns: list[SpeakerTurn] = []

        with sf.SoundFile(str(audio_path)) as audio_file:
            sample_rate = audio_file.samplerate
            if sample_rate != diarizer.sample_rate:
                logger.error("Diarization expected %sHz audio, got %s", diarizer.sample_rate, sample_rate)
                return None

            chunk_frames = int(chunk_seconds * sample_rate)
            start_frame = 0
            while start_frame < len(audio_file):
                audio_file.seek(start_frame)
                data = audio_file.read(frames=chunk_frames, dtype="float32", always_2d=True)
                if len(data) == 0:
                    break

                samples = np.ascontiguousarray(data[:, 0])
                chunk_offset = start_frame / sample_rate
                result = diarizer.process(samples).sort_by_start_time()
                turns.extend(
                    {
                        "start": round(chunk_offset + float(turn.start), 2),
                        "end": round(chunk_offset + float(turn.end), 2),
                        "speaker": f"SPEAKER_{int(turn.speaker):02d}",
                    }
                    for turn in result
                )
                start_frame += len(data)

        return sorted(turns, key=lambda turn: turn["start"])

    except ImportError:
        logger.exception("Diarization dependencies are not installed")
        return None
    except Exception as exc:
        logger.exception("Diarization failed: %s", exc)
        return None


def _assign_speaker(start: float, end: float, speaker_turns: list[SpeakerTurn]) -> str:
    best_speaker = "SPEAKER_00"
    best_overlap = 0.0
    for turn in speaker_turns:
        overlap = max(0.0, min(end, turn["end"]) - max(start, turn["start"]))
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = turn["speaker"]
    return best_speaker
