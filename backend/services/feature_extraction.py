from __future__ import annotations
import re

import librosa
import numpy as np
import parselmouth
import parselmouth.praat

from backend.models.schemas import FillerEvent, PauseInfo, TranscriptWord

PAUSE_THRESHOLD_MS = 400

FILLER_WORDS = {
    "uh", "um", "like", "basically", "actually", "literally",
    "so", "right", "kind", "sort",
}

READ_SENTENCE = (
    "please call stella and ask her to bring these things with her from the store"
)


# ── Pauses ───────────────────────────────────────────────────────────────────

def detect_pauses(words: list[TranscriptWord]) -> list[PauseInfo]:
    pauses: list[PauseInfo] = []
    for i in range(len(words) - 1):
        gap = words[i + 1].start - words[i].end
        if gap * 1000 >= PAUSE_THRESHOLD_MS:
            pauses.append(PauseInfo(
                start=words[i].end,
                end=words[i + 1].start,
                duration=round(gap, 3),
            ))
    return pauses


# ── Fillers ───────────────────────────────────────────────────────────────────

def detect_fillers(words: list[TranscriptWord]) -> list[FillerEvent]:
    return [
        FillerEvent(word=w.word.lower().strip(",.!?"), time=w.start)
        for w in words
        if w.word.lower().strip(",.!?") in FILLER_WORDS
    ]


# ── WPM ───────────────────────────────────────────────────────────────────────

def calculate_wpm(words: list[TranscriptWord], duration: float) -> float:
    if not words or duration <= 0:
        return 0.0
    pauses = detect_pauses(words)
    long_pause_time = sum(p.duration for p in pauses if p.duration > 1.0)
    speaking_time = max(duration - long_pause_time, 1.0)
    return round((len(words) / speaking_time) * 60.0, 1)


def speaking_time_ratio(words: list[TranscriptWord], duration: float) -> float:
    if not words or duration <= 0:
        return 0.0
    total_pause = sum(p.duration for p in detect_pauses(words))
    return round(max(0.0, (duration - total_pause) / duration), 3)


def speech_rate_variation(words: list[TranscriptWord]) -> float:
    """
    Std of per-word speaking rates across 3-word windows.
    High variation = natural speech. Flat = robotic or monotone delivery.
    Returns coefficient of variation (std/mean), lower = more monotone.
    """
    if len(words) < 6:
        return 0.0
    window = 3
    rates = []
    for i in range(len(words) - window):
        chunk = words[i:i + window]
        span = chunk[-1].end - chunk[0].start
        if span > 0:
            rates.append(window / span * 60.0)
    if len(rates) < 2:
        return 0.0
    mean_r = float(np.mean(rates))
    return round(float(np.std(rates)) / mean_r, 3) if mean_r > 0 else 0.0


# ── WER ───────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> list[str]:
    return re.sub(r"[^a-z\s]", "", text.lower()).split()


def calculate_wer(reference: str, hypothesis: str) -> float:
    ref = _normalize(reference)
    hyp = _normalize(hypothesis)
    if not ref:
        return 1.0
    r, h = len(ref), len(hyp)
    d = np.zeros((r + 1, h + 1))
    for i in range(r + 1):
        d[i][0] = i
    for j in range(h + 1):
        d[0][j] = j
    for i in range(1, r + 1):
        for j in range(1, h + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + cost)
    return round(float(d[r][h] / r), 3)


# ── Pa-ta-ka DDK ──────────────────────────────────────────────────────────────

def analyze_pataka(audio: np.ndarray, sr: int = 16000) -> dict:
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=128)
    onset_times = librosa.onset.onset_detect(
        onset_envelope=onset_env, sr=sr, hop_length=128,
        backtrack=True, units="time",
    )
    if len(onset_times) < 3:
        return {"syllable_intervals": [], "rhythm_regularity": 0.0, "ddk_rate": 0.0}

    intervals_ms = np.diff(onset_times) * 1000

    # Within-syllable intervals: 50–300ms (pa-ta-ka at normal speed = ~130-200ms each)
    # Intervals >300ms are pauses between groups — excluded from DDK rate
    syllable = intervals_ms[(intervals_ms > 50) & (intervals_ms < 300)]
    # All sub-500ms intervals used for regularity (includes slightly slower speech)
    all_valid = intervals_ms[(intervals_ms > 50) & (intervals_ms < 500)]

    if len(syllable) < 2:
        return {"syllable_intervals": [], "rhythm_regularity": 0.0, "ddk_rate": 0.0}

    mean_i = float(np.mean(syllable))
    # Regularity penalizes variance across ALL valid intervals including group boundaries —
    # intentional pauses between groups inflate std, correctly lowering the score
    std_i = float(np.std(all_valid)) if len(all_valid) > 1 else float(np.std(syllable))
    regularity = round(max(0.0, 1.0 - (std_i / mean_i)), 3) if mean_i > 0 else 0.0
    ddk_rate = round(1000.0 / mean_i, 2) if mean_i > 0 else 0.0
    return {
        "syllable_intervals": [round(v, 1) for v in all_valid.tolist()],
        "rhythm_regularity": regularity,
        "ddk_rate": ddk_rate,
    }


# ── Prosody — parselmouth ─────────────────────────────────────────────────────

def extract_prosody(wav_path: str) -> dict:
    snd = parselmouth.Sound(wav_path)

    # F0
    pitch_obj = snd.to_pitch(time_step=0.01, pitch_floor=75.0, pitch_ceiling=500.0)
    f0 = pitch_obj.selected_array["frequency"]
    voiced = f0[f0 > 0]
    times = pitch_obj.xs()
    voiced_mask = f0 > 0
    step = max(1, int(voiced_mask.sum() // 100))
    contour_vals = [round(v, 1) for v in f0[voiced_mask][::step].tolist()]
    contour_times = [round(t, 3) for t in times[voiced_mask][::step].tolist()]

    # Jitter / shimmer / HNR
    pp = parselmouth.praat.call(snd, "To PointProcess (periodic, cc)", 75.0, 500.0)
    jitter = parselmouth.praat.call(pp, "Get jitter (local)", 0.0, 0.0, 0.0001, 0.02, 1.3)
    shimmer = parselmouth.praat.call([snd, pp], "Get shimmer (local)", 0.0, 0.0, 0.0001, 0.02, 1.3, 1.6)
    harmonicity = snd.to_harmonicity_cc(time_step=0.01, minimum_pitch=75.0)
    hnr_vals = harmonicity.values[harmonicity.values != -200.0]

    # RMS energy via librosa — kept for visualization, not used in scoring
    audio_arr, _ = librosa.load(wav_path, sr=16000)
    rms = librosa.feature.rms(y=audio_arr, frame_length=2048, hop_length=512)[0]

    return {
        "pitch_mean": round(float(np.mean(voiced)), 1) if len(voiced) > 0 else 0.0,
        "pitch_std": round(float(np.std(voiced)), 1) if len(voiced) > 0 else 0.0,
        "pitch_contour": contour_vals,
        "pitch_times": contour_times,
        "jitter": round(float(jitter * 100), 4),
        "shimmer": round(float(shimmer * 100), 4),
        "hnr": round(float(np.mean(hnr_vals)), 2) if len(hnr_vals) > 0 else 0.0,
        "energy_mean": round(float(np.mean(rms)), 4),
        "energy_std": round(float(np.std(rms)), 4),  # kept for frontend chart only
    }


def detect_acoustic_fillers(wav_path: str) -> int:
    """
    Backup filler detection via acoustic analysis when Whisper suppresses um/uh.
    Detects voiced low-energy segments (filled pauses) using parselmouth:
    - Voiced (F0 present) but low intensity = likely um/uh/hmm
    Returns estimated count of filled pauses.
    """
    snd = parselmouth.Sound(wav_path)
    pitch_obj = snd.to_pitch(time_step=0.02, pitch_floor=75.0, pitch_ceiling=300.0)
    intensity_obj = snd.to_intensity(minimum_pitch=75.0, time_step=0.02)

    f0 = pitch_obj.selected_array["frequency"]
    times = pitch_obj.xs()

    # Get intensity at each pitch frame time
    intensities = np.array([
        parselmouth.praat.call(intensity_obj, "Get value at time", t, "Cubic")
        for t in times
    ])

    # Filled pause = voiced (f0 > 0) but quiet (intensity below mean - 10dB)
    mean_intensity = float(np.mean(intensities[intensities > 0])) if np.any(intensities > 0) else 60.0
    threshold = mean_intensity - 10.0

    voiced_quiet = (f0 > 0) & (intensities < threshold) & (intensities > 0)

    # Count contiguous runs of voiced-quiet frames as single events (min 3 frames = 60ms)
    count = 0
    run = 0
    for v in voiced_quiet:
        if v:
            run += 1
        else:
            if run >= 3:
                count += 1
            run = 0
    if run >= 3:
        count += 1

    return count


# ── Pronunciation — Whisper confidence ───────────────────────────────────────

def extract_pronunciation(words: list[TranscriptWord]) -> dict:
    if not words:
        return {"avg_word_confidence": None, "low_confidence_words": []}
    confidences = [w.confidence for w in words]
    avg = round(float(np.mean(confidences)), 3)
    low = [
        {"word": w.word, "confidence": round(w.confidence, 3), "time": round(w.start, 2)}
        for w in words if w.confidence < 0.6
    ]
    return {"avg_word_confidence": avg, "low_confidence_words": low}
