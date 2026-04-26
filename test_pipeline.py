"""
SpeakEasy — terminal test script.

Records 3 tasks from your microphone, runs the full audio pipeline,
and prints a detailed score report. No server needed.

Usage:
    .venv/bin/python test_pipeline.py
"""

import json
import sys
import threading
from datetime import datetime, timezone

import numpy as np

try:
    import pyaudio
except ImportError:
    print("\n[error] pyaudio not installed. Run: brew install portaudio && pip install pyaudio\n")
    sys.exit(1)

from backend.models.schemas import FeatureResult
from backend.utils.audio import cleanup_temp, save_temp_wav
from backend.services.transcription import transcribe
from backend.services import feature_extraction as fe
from backend.services.scoring import compute_scores

# ── Task definitions ──────────────────────────────────────────────────────────

TASKS = [
    {
        "id": "read_sentence",
        "title": "Task 1 of 3 — Read Aloud",
        "instruction": (
            "Read the following sentence clearly at a natural pace:\n\n"
            '  "Please call Stella and ask her to bring these things\n'
            '   with her from the store."\n'
        ),
        "hint": "Speak at your normal pace — not too fast, not too slow.",
        "show_transcript": True,
        "max_seconds": 15,
    },
    {
        "id": "pataka",
        "title": "Task 2 of 3 — Rhythm Test",
        "instruction": (
            'Say "pa-ta-ka" 5 times clearly, at a steady pace.\n'
        ),
        "hint": "Keep a steady rhythm — not too fast, not too slow.",
        "show_transcript": False,
        "max_seconds": 12,
    },
    {
        "id": "free_speech",
        "title": "Task 3 of 3 — Free Speech",
        "instruction": (
            "Describe the room you are sitting in right now.\n"
        ),
        "hint": "Speak naturally for about 20 seconds. There's no right or wrong answer.",
        "show_transcript": True,
        "max_seconds": 30,
    },
]

TARGET_RATE = 16000
CHUNK = 1024


# ── Recording ─────────────────────────────────────────────────────────────────

def record_until_enter(max_seconds: int) -> np.ndarray:
    pa = pyaudio.PyAudio()
    # Prefer MacBook built-in mic — AirPods Bluetooth degrades to SCO (8kHz internally)
    device_index = None
    for i in range(pa.get_device_count()):
        d = pa.get_device_info_by_index(i)
        if d["maxInputChannels"] > 0 and "MacBook" in d["name"]:
            device_index = i
            break
    device_info = pa.get_device_info_by_index(device_index) if device_index is not None \
                  else pa.get_default_input_device_info()
    native_rate = int(device_info["defaultSampleRate"])

    stream = pa.open(
        format=pyaudio.paInt16, channels=1,
        rate=native_rate, input=True,
        input_device_index=device_index,
        frames_per_buffer=CHUNK,
    )
    frames: list[bytes] = []
    stop_event = threading.Event()

    def _read():
        max_chunks = int(native_rate / CHUNK * max_seconds)
        for _ in range(max_chunks):
            if stop_event.is_set():
                break
            frames.append(stream.read(CHUNK, exception_on_overflow=False))

    reader = threading.Thread(target=_read, daemon=True)
    reader.start()
    input()
    stop_event.set()
    reader.join(timeout=2)
    stream.stop_stream()
    stream.close()
    pa.terminate()

    raw = b"".join(frames)
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    # Resample to 16kHz if needed (Whisper expects 16kHz)
    if native_rate != TARGET_RATE:
        import librosa
        audio = librosa.resample(audio, orig_sr=native_rate, target_sr=TARGET_RATE)

    return audio


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_task(task: dict) -> dict:
    print(f"\n{'='*62}")
    print(f"  {task['title']}")
    print(f"{'='*62}")
    print(f"\n  {task['instruction']}")
    print(f"  Hint: {task['hint']}\n")
    print("  Press ENTER to start recording...")
    input()
    print("  Recording... (press ENTER to stop)\n")

    audio = record_until_enter(task["max_seconds"])
    duration = len(audio) / TARGET_RATE
    print(f"  Recorded {duration:.1f}s — processing...\n")

    wav_path = save_temp_wav(audio)
    try:
        # ── Step 1: Transcription ─────────────────────────────────────────────
        print("  [1/3] Transcribing...")
        text, words = transcribe(wav_path, task=task["id"])

        if task["id"] == "pataka":
            preview = text[:80] + ("..." if len(text) > 80 else "")
            print(f'         Whisper raw (ignored for scoring): "{preview}"')
        elif task["show_transcript"]:
            if text:
                preview = text[:120] + ("..." if len(text) > 120 else "")
                print(f'         Transcript: "{preview}"')
            else:
                print('         Transcript: (empty — check mic or recording)')

        # ── Step 2: Features ─────────────────────────────────────────────────
        print("  [2/3] Extracting features...")
        pauses = fe.detect_pauses(words)
        prosody = fe.extract_prosody(wav_path)
        pronunciation = fe.extract_pronunciation(words)
        avg_pause = float(np.mean([p.duration for p in pauses])) if pauses else 0.0
        max_pause = float(max((p.duration for p in pauses), default=0.0))

        wpm = filler_events = filler_count = wer = None
        acoustic_filler_count = None
        speech_rate_cv = None
        pataka_data: dict = {}

        if task["id"] == "read_sentence":
            wpm = fe.calculate_wpm(words, duration)
            wer = fe.calculate_wer(fe.READ_SENTENCE, text)

        elif task["id"] == "pataka":
            pataka_data = fe.analyze_pataka(audio)

        elif task["id"] == "free_speech":
            wpm = fe.calculate_wpm(words, duration)
            filler_list = fe.detect_fillers(words)
            filler_count = len(filler_list)
            filler_events = filler_list
            acoustic_filler_count = fe.detect_acoustic_fillers(wav_path)
            speech_rate_cv = fe.speech_rate_variation(words)

        # ── Step 3: Build FeatureResult ───────────────────────────────────────
        features = FeatureResult(
            transcript=text,
            word_timestamps=words,
            audio_duration=duration,
            pauses=pauses,
            pause_count=len(pauses),
            avg_pause_duration=avg_pause,
            max_pause_duration=max_pause,
            wpm=wpm,
            filler_count=filler_count,
            acoustic_filler_count=acoustic_filler_count,
            filler_words=filler_events,
            speech_rate_cv=speech_rate_cv,
            word_error_rate=wer,
            syllable_intervals=pataka_data.get("syllable_intervals"),
            rhythm_regularity=pataka_data.get("rhythm_regularity"),
            ddk_rate=pataka_data.get("ddk_rate"),
            **prosody,
            **pronunciation,
        )

        print("  [3/3] Scoring...")
        scores = compute_scores(features, task["id"])
        print("  Done.")

        return {"task": task, "features": features, "scores": scores}

    finally:
        cleanup_temp(wav_path)


# ── Report ────────────────────────────────────────────────────────────────────

def _bar(score: float | None, width: int = 22) -> str:
    if score is None:
        return "N/A"
    filled = int(round((score / 100.0) * width))
    bar = "█" * filled + "░" * (width - filled)
    color = (
        "\033[92m" if score >= 75 else
        "\033[93m" if score >= 50 else
        "\033[91m"
    )
    return f"{color}[{bar}]\033[0m {score:.1f}"


def print_report(results: list[dict]) -> None:
    print("\n\n╔══════════════════════════════════════════════════════════════╗")
    print("║            S P E A K E A S Y   R E P O R T                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    all_scores: dict[str, list[float]] = {}

    for r in results:
        task = r["task"]
        f: FeatureResult = r["features"]
        s = r["scores"]

        print(f"\n── {task['title']} {'─' * (44 - len(task['title']))}")

        score_lines = [
            ("Overall",       s.overall),
            ("Fluency",       s.fluency),
            ("Clarity",       s.clarity),
            ("Rhythm",        s.rhythm),
            ("Prosody",       s.prosody),
            ("Pronunciation", s.pronunciation),
        ]
        for label, val in score_lines:
            if val is not None:
                print(f"  {label:<15} {_bar(val)}")
                all_scores.setdefault(label, []).append(val)

        print()
        print("  Metrics:")
        print(f"    Duration:           {f.audio_duration:.1f}s")

        if f.wpm is not None:
            print(f"    WPM:                {f.wpm:.0f}  (ideal: 120–160)")
        if f.word_error_rate is not None:
            print(f"    Word error rate:    {f.word_error_rate:.1%}  (excellent <5%, good <15%)")
        if f.pause_count > 0:
            print(f"    Pauses (≥400ms):    {f.pause_count}  (longest: {f.max_pause_duration:.2f}s)")
        if f.filler_count is not None:
            transcript_n = f.filler_count
            acoustic_n = f.acoustic_filler_count or 0
            best = max(transcript_n, acoustic_n)
            words_detected = [e.word for e in (f.filler_words or [])]
            detail = f"  {words_detected}" if words_detected else ""
            acoustic_note = f"  (acoustic backup: {acoustic_n})" if acoustic_n > transcript_n else ""
            print(f"    Filler words:       {best}{detail}{acoustic_note}")
        if f.speech_rate_cv is not None:
            print(f"    Rate variation CV:  {f.speech_rate_cv:.3f}  (natural: 0.10–0.80, higher = more expressive)")
        if f.ddk_rate is not None:
            print(f"    DDK rate:           {f.ddk_rate:.1f} syl/sec  (normal: 4.5–8.0)")
            print(f"    Rhythm regularity:  {f.rhythm_regularity:.2f}  (good speech ~0.5, max ~0.9)")
        if f.pitch_mean and f.pitch_mean > 0:
            print(f"    Pitch mean / std:   {f.pitch_mean:.0f} Hz / {f.pitch_std:.0f} Hz  (expressive: 20–55 Hz std)")
        if f.avg_word_confidence is not None:
            print(f"    Word confidence:    {f.avg_word_confidence:.1%}")
        if f.low_confidence_words:
            low = [w["word"] for w in f.low_confidence_words[:6]]
            print(f"    Low-conf words:     {low}")

    # ── Composite summary ─────────────────────────────────────────────────────
    print(f"\n{'═'*62}")
    print("  DIMENSION AVERAGES ACROSS ALL TASKS:")
    for label, vals in all_scores.items():
        if label == "Overall":
            continue
        avg = round(sum(vals) / len(vals), 1)
        print(f"    {label:<15} {_bar(avg)}")

    composite = _composite_score(results)
    print(f"\n  COMPOSITE SCORE:   {_bar(composite)}  (read/free_speech 40% each, pataka 20%)")
    print(f"{'═'*62}\n")


# ── JSON export ──────────────────────────────────────────────────────────────

_TASK_WEIGHTS = {"read_sentence": 0.40, "pataka": 0.20, "free_speech": 0.40}


def _composite_score(results: list[dict]) -> float:
    total = weight_sum = 0.0
    for r in results:
        w = _TASK_WEIGHTS.get(r["task"]["id"], 0.33)
        total += r["scores"].overall * w
        weight_sum += w
    return round(total / weight_sum, 1) if weight_sum > 0 else 0.0


def save_assessment_json(results: list[dict]) -> None:
    composite = _composite_score(results)

    payload = {
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "composite_score": composite,
        "scores_summary": {},
        "tasks": [],
    }

    for r in results:
        task = r["task"]
        f = r["features"]
        s = r["scores"]
        tid = task["id"]

        # Flat scores dict — only non-null dimensions
        scores = {k: v for k, v in {
            "overall":       s.overall,
            "fluency":       s.fluency,
            "clarity":       s.clarity,
            "rhythm":        s.rhythm,
            "prosody":       s.prosody,
            "pronunciation": s.pronunciation,
        }.items() if v is not None}

        # Track per-dimension scores for orchestrator routing
        for dim, val in scores.items():
            if dim == "overall":
                continue
            payload["scores_summary"].setdefault(dim, []).append(val)

        # Metadata for orchestrator context
        meta: dict = {"instruction": task["instruction"].strip()}
        if tid == "read_sentence":
            meta["reference_sentence"] = fe.READ_SENTENCE

        # Key metrics — exclude pitch from pataka (not meaningful there)
        metrics: dict = {"audio_duration": round(f.audio_duration, 2)}
        if f.wpm is not None:
            metrics["wpm"] = f.wpm
        if f.word_error_rate is not None:
            metrics["word_error_rate"] = f.word_error_rate
        if f.pause_count:
            metrics["pause_count"] = f.pause_count
            metrics["max_pause_duration"] = f.max_pause_duration
        if f.filler_count is not None:
            metrics["filler_count"] = max(f.filler_count, f.acoustic_filler_count or 0)
        if f.speech_rate_cv is not None:
            metrics["speech_rate_cv"] = f.speech_rate_cv
        if f.ddk_rate is not None:
            metrics["ddk_rate"] = f.ddk_rate
            metrics["rhythm_regularity"] = f.rhythm_regularity
        if tid != "pataka" and f.pitch_std is not None:
            metrics["pitch_mean_hz"] = f.pitch_mean
            metrics["pitch_std_hz"] = f.pitch_std
        if f.avg_word_confidence is not None:
            metrics["avg_word_confidence"] = round(f.avg_word_confidence, 3)
        if f.low_confidence_words:
            metrics["low_confidence_words"] = [
                {"word": w["word"], "confidence": round(w["confidence"], 3)}
                for w in f.low_confidence_words
            ]
        if f.transcript:
            metrics["transcript"] = f.transcript

        payload["tasks"].append({
            "task_id": tid,
            "metadata": meta,
            "scores": scores,
            "metrics": metrics,
        })

    # Aggregate each dimension to a single score (mean across tasks that have it)
    payload["scores_summary"] = {
        dim: round(sum(vals) / len(vals), 1)
        for dim, vals in payload["scores_summary"].items()
    }

    out_path = f"assessment_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f_out:
        json.dump(payload, f_out, indent=2)
    print(f"  Assessment saved → {out_path}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║           Welcome to the SpeakEasy Assessment               ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  3 short tasks — about 45 seconds total.                    ║")
    print("║  Press ENTER to start each task, ENTER again to stop.       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("\nPress ENTER to begin...")
    input()

    results = []
    for task in TASKS:
        result = run_task(task)
        results.append(result)

    print_report(results)
    save_assessment_json(results)


if __name__ == "__main__":
    main()
