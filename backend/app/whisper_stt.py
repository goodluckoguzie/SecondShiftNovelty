from __future__ import annotations

import gc
from pathlib import Path

_model = None


def transcribe_file(path: str | Path, model_size: str = "small") -> str:
    global _model
    from faster_whisper import WhisperModel

    from .config import WHISPER_DEVICE

    device = WHISPER_DEVICE
    try:
        if _model is None:
            _model = WhisperModel(model_size, device=device, compute_type="float16" if device == "cuda" else "int8")
        segments, _info = _model.transcribe(str(path), language="en")
        text = " ".join(segment.text.strip() for segment in segments).strip()
    except Exception:
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _info = _model.transcribe(str(path), language="en")
        text = " ".join(segment.text.strip() for segment in segments).strip()
    finally:
        unload()
    return text


def unload() -> None:
    global _model
    _model = None
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
