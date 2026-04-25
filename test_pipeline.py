"""
SpeechScore — terminal test script.

Records 3 tasks from your microphone, runs the full audio pipeline,
and prints a detailed score report. No server needed.

Usage:
    python test_pipeline.py

Requirements:
    pip install -r requirements.txt
    brew install ffmpeg portaudio
    pip install pyaudio   # for microphone recording
"""

import sys
import time
import wave
import threading

import numpy as np

# ── Try importing pyaudio early so we fail fast with a clear message ─────────
try:
    import pyaudio
except ImportError:
    print("\n[error] pyaudio is not installed.")
    print("  Run: pip install pyaudio")
    print("  macOS: brew install portaudio && pip install pyaudio\n")
    sys.exit(1)

from backend.utils.audio import save_temp_wav, cleanup_temp, wav_file_to_array
from backend.services.transcription import transcribe
from backend.services import feature_extraction as fe
from backend.services.scoring import compute_scores

# ── Task definitions ──────────────────────────────────────────────────────────

TASKS = [
    {
        "id": "read_sentence",
        "title": "Task 1 of 3 — Read Aloud",
        "instruction": (
            "Read the following sentence clearly at a natural pace.\n"
            "Press ENTER to start recording, then press ENTER again to stop.\n\n"
            '  "Please call Stella and ask her to bring these things\n'
            '   with her from the store."\n'
        ),
        "max_seconds": 15,
    },
    {
        "id": "pataka",
        "title": "Task 2 of 3 — Rhythm Test (pa-ta-ka)",
        "instruction": (
            'Repeat "pa-ta-ka" as quickly and clearly as you can.\n'
            "Press ENTER to start, ENTER again to stop (aim for ~8 seconds).\n"
        ),
        "max_seconds": 12,
    },
    {
        "id": "free_speech",
        "title": "Task 3 of 3 — Free Speech",
        "instruction": (
            "Speak naturally about what you did yesterday.\n"
            "Press ENTER to start, ENTER again to stop (aim for ~20 seconds).\n"
        ),
        "max_seconds": 30,
    },
]

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK = 1024


# ── Recording ─────────────────────────────────────────────────────────────────

def record_until_enter(max_seconds: int) -> np.ndarray:
    """Records from the default microphone until Enter is pressed or max_seconds reached."""
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    frames: list[bytes] = []
    stop_event = threading.Event()

    def _read():
        max_chunks = int(SAMPLE_RATE / CHUNK * max_seconds)
        count = 0
        while not stop_event.is_set() and count < max_chunks:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            count += 1

    reader = threading.Thread(target=_read, daemon=True)
    reader.start()

    input()  # user presses Enter to stop
    stop_event.set()
    reader.join(timeout=2)

    stream.stop_stream()
    stream.close()
    pa.terminate()

    raw = b"".join(frames)
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return audio


# ── Pipeline ─────────────────────────────────────────────────────────────────

def run_task(task: dict) -> dict:
    print(f"\n{'='*60}")
    print(f"  {task['title']}")
    print(f"{'='*60}")
    print(f"\n{task['instruction']}")
    print("  Press ENTER to start recording...")
    input()
    print("  🔴 Recording... (press ENTER to stop)")

    audio = record_until_enter(task["max_seconds"])
    duration = len(audio) / SAMPLE_RATE

    print(f"  ✓ Recorded {duration:.1f}s — processing...\n")

    wav_path = save_temp_wav(audio)
    try:
        print("  [1/4] Transcribing...")
        text, words = transcribe(wav_path)
        print(f"        → \"{text[:80]}{'...' if len(text) > 80 else ''}\"")

        print("  [2/4] Extracting features...")
        pauses = fe.detect_pauses(words)
        prosody = fe.extract_prosody(wav_path)
        pronunciation = fe.extract_pronunciation(words)

        avg_pause = float(np.mean([p.duration for p in pauses])) if pauses else 0.0
        max_pause = float(max((p.duration for p in pauses), default=0.0))

        wpm = filler_events = filler_count = wer = None
        speaking_ratio = None
        pataka_data: dict = {}

        if task["id"] == "read_sentence":
            wpm = fe.calculate_wpm(words, duration)
            wer = fe.calculate_wer(fe.READ_SENTENCE, text)
            speaking_ratio = fe.speaking_time_ratio(words, duration)

        elif task["id"] == "pataka":
            pataka_data = fe.analyze_pataka(audio)

        elif task["id"] == "free_speech":
            wpm = fe.calculate_wpm(words, duration)
            filler_list = fe.detect_fillers(words)
            filler_count = len(filler_list)
            filler_events = filler_list
            speaking_ratio = fe.speaking_time_ratio(words, duration)

        from backend.models.schemas import FeatureResult
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
            filler_words=filler_events,
            speaking_time_ratio=speaking_ratio,
            word_error_rate=wer,
            syllable_intervals=pataka_data.get("syllable_intervals"),
            rhythm_regularity=pataka_data.get("rhythm_regularity"),
            ddk_rate=pataka_data.get("ddk_rate"),
            **prosody,
            **pronunciation,
        )

        print("  [3/4] Scoring...")
        scores = compute_scores(features, task["id"])

        print("  [4/4] Done.\n")

        return {"task": task, "features": features, "scores": scores}

    finally:
        cleanup_temp(wav_path)


# ── Report printer ────────────────────────────────────────────────────────────

def _bar(score: float | None, width: int = 20) -> str:
    if score is None:
        return "  N/A"
    filled = int(round((score / 100.0) * width))
    bar = "█" * filled + "░" * (width - filled)
    return f"  [{bar}] {score:.1f}"


def print_report(results: list[dict]) -> None:
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║              S P E E C H S C O R E   R E P O R T        ║")
    print("╚══════════════════════════════════════════════════════════╝")

    for r in results:
        task = r["task"]
        f: "FeatureResult" = r["features"]
        s = r["scores"]

        print(f"\n── {task['title']} ──────────────────────────────")
        print(f"  Overall:        {_bar(s.overall)}")
        if s.fluency is not None:
            print(f"  Fluency:        {_bar(s.fluency)}")
        if s.clarity is not None:
            print(f"  Clarity:        {_bar(s.clarity)}")
        if s.rhythm is not None:
            print(f"  Rhythm:         {_bar(s.rhythm)}")
        if s.prosody is not None:
            print(f"  Prosody:        {_bar(s.prosody)}")
        if s.voice_quality is not None:
            print(f"  Voice Quality:  {_bar(s.voice_quality)}")
        if s.pronunciation is not None:
            print(f"  Pronunciation:  {_bar(s.pronunciation)}")

        print()
        print("  Key Metrics:")
        print(f"    Duration:         {f.audio_duration:.1f}s")
        print(f"    Pauses (≥400ms):  {f.pause_count}")
        if f.max_pause_duration > 0:
            print(f"    Longest pause:    {f.max_pause_duration:.2f}s")
        if f.wpm is not None:
            print(f"    WPM:              {f.wpm:.0f}")
        if f.filler_count is not None:
            fillers = [e.word for e in (f.filler_words or [])]
            print(f"    Filler words:     {f.filler_count}  {fillers if fillers else ''}")
        if f.word_error_rate is not None:
            print(f"    Word error rate:  {f.word_error_rate:.1%}")
        if f.ddk_rate is not None:
            print(f"    DDK rate:         {f.ddk_rate:.1f} syllables/sec  (normal: 5–7)")
        if f.rhythm_regularity is not None:
            print(f"    Rhythm regularity:{f.rhythm_regularity:.2f}  (1.0 = perfect)")
        if f.pitch_mean and f.pitch_mean > 0:
            print(f"    Pitch mean/std:   {f.pitch_mean:.0f} Hz / {f.pitch_std:.0f} Hz")
        if f.jitter is not None:
            print(f"    Jitter:           {f.jitter:.3f}%  (normal <1%)")
            print(f"    Shimmer:          {f.shimmer:.3f}%  (normal <3%)")
            print(f"    HNR:              {f.hnr:.1f} dB  (normal >20 dB)")
        if f.avg_word_confidence is not None:
            print(f"    Word confidence:  {f.avg_word_confidence:.1%}")
        if f.low_confidence_words:
            low = [w["word"] for w in f.low_confidence_words[:5]]
            print(f"    Low-conf words:   {low}")

    # Composite summary
    overalls = [r["scores"].overall for r in results]
    composite = round(sum(overalls) / len(overalls), 1)
    print(f"\n{'='*60}")
    print(f"  COMPOSITE SCORE:  {composite:.1f} / 100")
    print(f"{'='*60}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║         Welcome to the SpeechScore Assessment           ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  You will complete 3 short tasks (~60 seconds total).   ║")
    print("║  Speak clearly at a natural pace.                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("\nPress ENTER to begin...")
    input()

    results = []
    for task in TASKS:
        result = run_task(task)
        results.append(result)

    print_report(results)


if __name__ == "__main__":
    main()
