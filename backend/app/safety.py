from .config import EMERGENCY_PHRASES

ADVICE_MARKERS = (
    "you should take",
    "this could be serious",
    "you must go to a&e",
    "i diagnose",
    "this is a stroke",
    "this is a heart attack",
)


def is_emergency(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in EMERGENCY_PHRASES)


def strip_advice(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in ADVICE_MARKERS):
        return (
            "I have organised your notes. I cannot give medical advice. "
            "Please take this log to the GP or memory clinic."
        )
    return text
