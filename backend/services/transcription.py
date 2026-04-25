from __future__ import annotations
from faster_whisper import WhisperModel
from backend.models.schemas import TranscriptWord

# Loaded once at module level — stays warm between requests
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        print("  [whisper] Loading model (first call only)...")
        _model = WhisperModel("small.en", device="cpu", compute_type="int8")
    return _model


# Primes Whisper to transcribe filled pauses it would otherwise suppress
_FILLER_PROMPT = "Um, uh, like, you know, so, basically, actually, right, kind of."


def transcribe(wav_path: str, task: str = "free_speech") -> tuple[str, list[TranscriptWord]]:
    model = _get_model()

    # Only inject filler prompt for free speech — read_sentence and pataka don't need it
    prompt = _FILLER_PROMPT if task == "free_speech" else None

    segments, _ = model.transcribe(
        wav_path,
        beam_size=5,
        word_timestamps=True,
        language="en",
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
        initial_prompt=prompt,
        suppress_tokens=[],  # disable Whisper's built-in token suppression list
    )
    words: list[TranscriptWord] = []
    text_parts: list[str] = []
    for seg in segments:
        for w in (seg.words or []):
            cleaned = w.word.strip()
            if cleaned:
                words.append(TranscriptWord(
                    word=cleaned,
                    start=w.start,
                    end=w.end,
                    confidence=w.probability,
                ))
                text_parts.append(cleaned)
    return " ".join(text_parts), words
