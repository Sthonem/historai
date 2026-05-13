"""Vercel Python runtime entry point.

Vercel looks for an ASGI ``app`` (or WSGI) exported from a function file. We
re-export the FastAPI application from ``main.py`` here so the project layout
stays clean.
"""

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from main import app  # noqa: E402  (sys.path setup must come first)

__all__ = ["app"]
