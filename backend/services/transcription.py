from __future__ import annotations
import json
import os
import subprocess
import threading

from backend.models.schemas import TranscriptWord

_WHISPER_CLI = "/opt/homebrew/bin/whisper-cli"
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/ggml-tiny.en.bin")
_MODEL_PATH = os.path.normpath(_MODEL_PATH)

_FILLER_PROMPT = "Um, uh, like, you know, so, basically, actually, right, kind of."

# ── whisper.cpp — fast transcript + timestamps via Metal ─────────────────────

def _transcribe_cpp(wav_path: str, prompt: str | None) -> tuple[str, list[TranscriptWord]]:
    cmd = [
        _WHISPER_CLI,
        "--model", _MODEL_PATH,
        "--file", wav_path,
        "--output-json",
        "--split-on-word",
        "--max-len", "1",
        "--language", "en",
        "--no-prints",
        "--output-file", wav_path,
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
        seg_text = segment.get("text", "").strip()
        if not seg_text or seg_text.startswith("["):
            continue
        t_from = segment.get("timestamps", {}).get("from", "00:00:00,000")
        t_to   = segment.get("timestamps", {}).get("to",   "00:00:00,000")
        seg_start = _ts_to_sec(t_from)
        seg_end   = _ts_to_sec(t_to)

        seg_words = seg_text.split()
        n = len(seg_words)
        duration = max(seg_end - seg_start, 0.01)
        step = duration / n
        for i, w in enumerate(seg_words):
            words.append(TranscriptWord(
                word=w,
                start=round(seg_start + i * step, 3),
                end=round(seg_start + (i + 1) * step, 3),
                confidence=0.85,  # placeholder — overwritten by _merge_confidence
            ))
            text_parts.append(w)

    return " ".join(text_parts), words


def _ts_to_sec(ts: str) -> float:
    try:
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0
    except Exception:
        return 0.0


# ── faster-whisper — real per-word confidence scores ─────────────────────────

_fw_model = None
_fw_lock = threading.Lock()


def _get_fw_model():
    global _fw_model
    with _fw_lock:
        if _fw_model is None:
            from faster_whisper import WhisperModel
            _fw_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    return _fw_model


def _get_confidence_scores(wav_path: str, prompt: str | None) -> dict[str, float]:
    """Returns {word_lower: confidence} from faster-whisper. Used to enrich cpp output."""
    try:
        model = _get_fw_model()
        segments, _ = model.transcribe(
            wav_path,
            beam_size=3,          # faster than 5, confidence scores are still accurate
            word_timestamps=True,
            language="en",
            vad_filter=False,
            initial_prompt=prompt,
            suppress_tokens=[],
        )
        scores: dict[str, float] = {}
        for seg in segments:
            for w in (seg.words or []):
                cleaned = w.word.strip().lower().strip(",.!?")
                if cleaned:
                    # keep highest confidence if word appears multiple times
                    scores[cleaned] = max(scores.get(cleaned, 0.0), w.probability)
        return scores
    except Exception:
        return {}


def _merge_confidence(
    words: list[TranscriptWord],
    scores: dict[str, float],
) -> list[TranscriptWord]:
    """Replace placeholder confidence with real faster-whisper scores where available."""
    merged = []
    for w in words:
        key = w.word.lower().strip(",.!?")
        conf = scores.get(key, w.confidence)
        merged.append(TranscriptWord(
            word=w.word, start=w.start, end=w.end, confidence=conf,
        ))
    return merged


# ── Public API ────────────────────────────────────────────────────────────────

def transcribe(wav_path: str, task: str = "free_speech") -> tuple[str, list[TranscriptWord]]:
    prompt = _FILLER_PROMPT if task == "free_speech" else None

    cpp_available = os.path.exists(_WHISPER_CLI) and os.path.exists(_MODEL_PATH)

    if not cpp_available:
        # Pure faster-whisper fallback (no whisper.cpp binary or model)
        return _transcribe_fw_full(wav_path, prompt)

    # Run whisper.cpp (fast, Metal) and faster-whisper (confidence) in parallel
    conf_result: dict = {}

    def _run_fw():
        conf_result.update(_get_confidence_scores(wav_path, prompt))

    fw_thread = threading.Thread(target=_run_fw, daemon=True)
    fw_thread.start()

    text, words = _transcribe_cpp(wav_path, prompt)

    fw_thread.join(timeout=15)  # don't block forever; confidence is best-effort

    if conf_result:
        words = _merge_confidence(words, conf_result)

    return text, words


def _transcribe_fw_full(wav_path: str, prompt: str | None) -> tuple[str, list[TranscriptWord]]:
    """Full faster-whisper path used when whisper.cpp is unavailable."""
    model = _get_fw_model()
    segments, _ = model.transcribe(
        wav_path,
        beam_size=5,
        word_timestamps=True,
        language="en",
        vad_filter=False,
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
