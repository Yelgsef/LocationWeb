"""Translation helpers powered by deep_translator."""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _get_translator():
    """Return a cached GoogleTranslator instance that auto-detects source language."""
    try:
        from deep_translator import GoogleTranslator
    except ImportError as exc:
        # Make the API error message actionable without crashing app startup.
        raise RuntimeError("Thiếu thư viện deep-translator. Cài đặt: pip install deep-translator.") from exc
    return GoogleTranslator(source="auto", target="vi")


def translate_to_vietnamese(text: str) -> str:
    """Translate arbitrary text to Vietnamese."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Vui lòng nhập nội dung cần dịch.")
    try:
        return _get_translator().translate(cleaned)
    except Exception as exc:  # pragma: no cover - network/translator failures
        # Hide provider-specific errors from clients.
        raise RuntimeError("Không thể dịch văn bản ngay bây giờ.") from exc
