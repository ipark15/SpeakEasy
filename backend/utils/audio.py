from __future__ import annotations
import io
import os
import uuid

import numpy as np
import soundfile as sf
from pydub import AudioSegment


def wav_file_to_array(path: str, target_sr: int = 16000) -> np.ndarray:
    """Read a WAV file on disk → float32 numpy array at target_sr, mono."""
    seg = AudioSegment.from_file(path)
    seg = seg.set_frame_rate(target_sr).set_channels(1)
    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
    return samples / 32768.0


def bytes_to_array(input_bytes: bytes, target_sr: int = 16000) -> np.ndarray:
    """Decode any browser audio blob (WebM/opus etc.) → float32 array."""
    seg = AudioSegment.from_file(io.BytesIO(input_bytes))
    seg = seg.set_frame_rate(target_sr).set_channels(1)
    samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
    return samples / 32768.0


def save_temp_wav(audio: np.ndarray, sr: int = 16000) -> str:
    path = f"/tmp/speech_{uuid.uuid4().hex}.wav"
    sf.write(path, audio, sr)
    return path


def cleanup_temp(path: str) -> None:
    if path and os.path.exists(path):
        os.unlink(path)
