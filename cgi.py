"""
Lightweight compatibility shim for Python 3.13 where the stdlib `cgi` module was removed.

Only implements `parse_header`, which is what `requests` needs for content-type parsing.
"""
from email.message import Message
from typing import Dict, Tuple

__all__ = ["parse_header"]


def parse_header(value: str) -> Tuple[str, Dict[str, str]]:
    """Return (content_type, params) similar to the old cgi.parse_header."""
    msg = Message()
    msg["content-type"] = value or ""
    params = dict(msg.get_params()[1:]) if msg.get_params() else {}
    return msg.get_content_type(), {k.lower(): v for k, v in params.items()}
