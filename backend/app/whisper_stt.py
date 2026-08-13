from __future__ import annotations

import gc
from pathlib import Path

_model = None
_model_size = None


def _load(model_size: str, device: str):
    from faster_whisper import WhisperModel

    compute = "float16" if device == "cuda" else "int8"
    return WhisperModel(model_size, device=device, compute_type=compute)


def warmup(model_size: str = "base") -> None:
    global _model, _model_size
    from .config import WHISPER_DEVICE

    if _model is not None and _model_size == model_size:
        return
    try:
        _model = _load(model_size, WHISPER_DEVICE)
        _model_size = model_size
    except Exception:
        _model = _load(model_size, "cpu")
        _model_size = model_size


def transcribe_file(path: str | Path, model_size: str = "base") -> str:
    global _model, _model_size
    from .config import WHISPER_DEVICE

    if _model is None or _model_size != model_size:
        try:
            _model = _load(model_size, WHISPER_DEVICE)
            _model_size = model_size
        except Exception:
            _model = _load(model_size, "cpu")
            _model_size = model_size

    try:
        segments, _info = _model.transcribe(
            str(path),
            language="en",
            beam_size=1,
            vad_filter=True,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()
    except Exception:
        _model = _load(model_size, "cpu")
        _model_size = model_size
        segments, _info = _model.transcribe(
            str(path),
            language="en",
            beam_size=1,
            vad_filter=True,
        )
        return " ".join(segment.text.strip() for segment in segments).strip()


def unload() -> None:
    global _model, _model_size
    _model = None
    _model_size = None
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
