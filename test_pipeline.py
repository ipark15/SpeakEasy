"""
SpeechScore — terminal test script.

Records 4 tasks from your microphone, runs the full audio pipeline,
and prints a detailed score report. No server needed.

Usage:
    .venv/bin/python test_pipeline.py
"""

import sys
import threading

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
        "title": "Task 1 of 4 — Read Aloud",
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
        "title": "Task 2 of 4 — Rhythm Test",
        "instruction": (
            'Repeat "pa-ta-ka" as quickly and clearly as you can for about 8 seconds.\n'
        ),
        "hint": "Keep a steady rhythm. Speed and consistency both matter.",
        "show_transcript": False,  # Whisper output on pataka is meaningless — suppress it
        "max_seconds": 12,
    },
    {
        "id": "sustained_vowel",
        "title": "Task 3 of 4 — Sustained Vowel",
        "instruction": (
            'Say "ahhh" in a steady, comfortable tone for as long as you can.\n'
        ),
        "hint": "Keep your pitch and volume as steady as possible.",
        "show_transcript": False,
        "max_seconds": 10,
    },
    {
        "id": "free_speech",
        "title": "Task 4 of 4 — Free Speech",
        "instruction": (
            "Describe the room you are sitting in right now.\n"
        ),
        "hint": "Speak naturally for about 20 seconds. There's no right or wrong answer.",
        "show_transcript": True,
        "max_seconds": 30,
    },
]

SAMPLE_RATE = 16000
CHUNK = 1024


# ── Recording ─────────────────────────────────────────────────────────────────

def record_until_enter(max_seconds: int) -> np.ndarray:
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16, channels=1,
        rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK,
    )
    frames: list[bytes] = []
    stop_event = threading.Event()

    def _read():
        max_chunks = int(SAMPLE_RATE / CHUNK * max_seconds)
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
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


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
    duration = len(audio) / SAMPLE_RATE
    print(f"  Recorded {duration:.1f}s — processing...\n")

    wav_path = save_temp_wav(audio)
    try:
        # ── Step 1: Transcription ─────────────────────────────────────────────
        print("  [1/4] Transcribing...")
        if task["id"] in ("pataka", "sustained_vowel"):
            # Still transcribe for word timestamp data; just don't show output
            text, words = transcribe(wav_path, task=task["id"])
        else:
            text, words = transcribe(wav_path, task=task["id"])

        if task["show_transcript"] and text:
            preview = text[:90] + ("..." if len(text) > 90 else "")
            print(f'         "{preview}"')

        # ── Step 2: Features ─────────────────────────────────────────────────
        print("  [2/4] Extracting features...")
        pauses = fe.detect_pauses(words)
        prosody = fe.extract_prosody(wav_path)
        pronunciation = fe.extract_pronunciation(words)
        avg_pause = float(np.mean([p.duration for p in pauses])) if pauses else 0.0
        max_pause = float(max((p.duration for p in pauses), default=0.0))

        wpm = filler_events = filler_count = wer = None
        acoustic_filler_count = None
        speaking_ratio = speech_rate_cv = None
        pataka_data: dict = {}

        if task["id"] == "read_sentence":
            wpm = fe.calculate_wpm(words, duration)
            wer = fe.calculate_wer(fe.READ_SENTENCE, text)
            speaking_ratio = fe.speaking_time_ratio(words, duration)

        elif task["id"] == "pataka":
            pataka_data = fe.analyze_pataka(audio)

        elif task["id"] == "sustained_vowel":
            pass  # voice quality metrics from prosody are sufficient

        elif task["id"] == "free_speech":
            wpm = fe.calculate_wpm(words, duration)
            filler_list = fe.detect_fillers(words)
            filler_count = len(filler_list)
            filler_events = filler_list
            acoustic_filler_count = fe.detect_acoustic_fillers(wav_path)
            speaking_ratio = fe.speaking_time_ratio(words, duration)
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
            speaking_time_ratio=speaking_ratio,
            speech_rate_cv=speech_rate_cv,
            word_error_rate=wer,
            syllable_intervals=pataka_data.get("syllable_intervals"),
            rhythm_regularity=pataka_data.get("rhythm_regularity"),
            ddk_rate=pataka_data.get("ddk_rate"),
            **prosody,
            **pronunciation,
        )

        print("  [3/4] Scoring...")
        scores = compute_scores(features, task["id"])
        print("  [4/4] Done.")

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
        "\033[92m" if score >= 75 else   # green
        "\033[93m" if score >= 50 else   # yellow
        "\033[91m"                        # red
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
            ("Voice Quality", s.voice_quality),
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
            print(f"    WPM:                {f.wpm:.0f}  (natural: 130–160)")
        if f.word_error_rate is not None:
            print(f"    Word error rate:    {f.word_error_rate:.1%}")

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
            print(f"    Rate variation CV:  {f.speech_rate_cv:.3f}  (natural: 0.15–0.35)")

        if f.ddk_rate is not None:
            print(f"    DDK rate:           {f.ddk_rate:.1f} syllables/sec  (normal: 5–7)")
            print(f"    Rhythm regularity:  {f.rhythm_regularity:.2f}  (1.0 = perfect)")

        if f.pitch_mean and f.pitch_mean > 0:
            print(f"    Pitch mean / std:   {f.pitch_mean:.0f} Hz / {f.pitch_std:.0f} Hz")
        if f.jitter is not None:
            jitter_flag = "  ⚠" if f.jitter > 1.0 else ""
            shimmer_flag = "  ⚠" if f.shimmer > 3.0 else ""
            hnr_flag = "  ⚠" if f.hnr < 20.0 else ""
            print(f"    Jitter:             {f.jitter:.3f}%  (normal <1%){jitter_flag}")
            print(f"    Shimmer:            {f.shimmer:.3f}%  (normal <3%){shimmer_flag}")
            print(f"    HNR:                {f.hnr:.1f} dB  (normal >20 dB){hnr_flag}")

        if f.avg_word_confidence is not None:
            print(f"    Word confidence:    {f.avg_word_confidence:.1%}")
        if f.low_confidence_words:
            low = [w["word"] for w in f.low_confidence_words[:6]]
            print(f"    Low-conf words:     {low}")

    # ── Composite radar summary ───────────────────────────────────────────────
    print(f"\n{'═'*62}")
    print("  DIMENSION AVERAGES ACROSS ALL TASKS:")
    composite_vals = []
    for label, vals in all_scores.items():
        avg = round(sum(vals) / len(vals), 1)
        composite_vals.append(avg)
        print(f"    {label:<15} {_bar(avg)}")

    composite = round(sum(composite_vals) / len(composite_vals), 1) if composite_vals else 0.0
    print(f"\n  COMPOSITE SCORE:   {_bar(composite)}")
    print(f"{'═'*62}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║           Welcome to the SpeakEasy Assessment               ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  4 short tasks — about 60 seconds total.                    ║")
    print("║  Press ENTER to start each task, ENTER again to stop.       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("\nPress ENTER to begin...")
    input()

    results = []
    for task in TASKS:
        result = run_task(task)
        results.append(result)

    print_report(results)


if __name__ == "__main__":
    main()
