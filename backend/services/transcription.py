from __future__ import annotations
import json
import os
import subprocess
import tempfile

from backend.models.schemas import TranscriptWord

_WHISPER_CLI = "/opt/homebrew/bin/whisper-cli"
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/ggml-small.en.bin")
_MODEL_PATH = os.path.normpath(_MODEL_PATH)

# Primes Whisper to transcribe filled pauses it would otherwise suppress
_FILLER_PROMPT = "Um, uh, like, you know, so, basically, actually, right, kind of."


def _transcribe_cpp(wav_path: str, prompt: str | None) -> tuple[str, list[TranscriptWord]]:
    cmd = [
        _WHISPER_CLI,
        "--model", _MODEL_PATH,
        "--file", wav_path,
        "--output-json",
        "--word-thold", "0.01",   # emit word-level timestamps
        "--language", "en",
        "--no-prints",            # suppress progress output
        "--output-file", wav_path,  # writes <wav_path>.json next to the wav
    ]
    if prompt:
        cmd += ["--prompt", prompt]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    json_path = wav_path + ".json"

    if result.returncode != 0 or not os.path.exists(json_path):
        raise RuntimeError(f"whisper-cli failed: {result.stderr[:200]}")

    try:
        with open(json_path) as f:
            data = json.load(f)
    finally:
        if os.path.exists(json_path):
            os.unlink(json_path)

    words: list[TranscriptWord] = []
    text_parts: list[str] = []

    for segment in data.get("transcription", []):
        for token in segment.get("tokens", []):
            word = token.get("text", "").strip()
            if not word or word.startswith("["):
                continue
            t_from = token.get("timestamps", {}).get("from", "00:00:00,000")
            t_to   = token.get("timestamps", {}).get("to",   "00:00:00,000")
            p      = token.get("p", 1.0)
            words.append(TranscriptWord(
                word=word,
                start=_ts_to_sec(t_from),
                end=_ts_to_sec(t_to),
                confidence=float(p),
            ))
            text_parts.append(word)

    return " ".join(text_parts), words


def _ts_to_sec(ts: str) -> float:
    # "HH:MM:SS,mmm"
    try:
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0
    except Exception:
        return 0.0


# Fallback: faster-whisper (used if whisper.cpp model not yet downloaded)
_fw_model = None


def _transcribe_fw(wav_path: str, prompt: str | None) -> tuple[str, list[TranscriptWord]]:
    global _fw_model
    if _fw_model is None:
        from faster_whisper import WhisperModel
        print("  [whisper] Loading fallback model...")
        _fw_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

    segments, _ = _fw_model.transcribe(
        wav_path,
        beam_size=5,
        word_timestamps=True,
        language="en",
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
        initial_prompt=prompt,
        suppress_tokens=[],
    )
    words: list[TranscriptWord] = []
    text_parts: list[str] = []
    for seg in segments:
        for w in (seg.words or []):
            cleaned = w.word.strip()
            if cleaned:
                words.append(TranscriptWord(
                    word=cleaned, start=w.start, end=w.end,
                    confidence=w.probability,
                ))
                text_parts.append(cleaned)
    return " ".join(text_parts), words


def transcribe(wav_path: str, task: str = "free_speech") -> tuple[str, list[TranscriptWord]]:
    prompt = _FILLER_PROMPT if task == "free_speech" else None

    if os.path.exists(_WHISPER_CLI) and os.path.exists(_MODEL_PATH):
        return _transcribe_cpp(wav_path, prompt)

    # Model not downloaded yet — fall back to faster-whisper
    print("  [whisper] whisper.cpp model not found, using CPU fallback...")
    return _transcribe_fw(wav_path, prompt)
