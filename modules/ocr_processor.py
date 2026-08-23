"""
ocr_processor.py
------------------
Extracts text from uploaded screenshot images using Tesseract OCR
(via pytesseract). Tesseract is free, runs fully offline, and requires no
API key -- matching the "no paid APIs" requirement.

NOTE: This requires the Tesseract binary to be installed on the host
machine (not just the Python wrapper). See README.md for install
instructions per OS. If Tesseract is not found, a clear, actionable error
is returned instead of a crash.
"""

import os
from typing import Dict
from PIL import Image

try:
    import pytesseract
    _PYTESSERACT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYTESSERACT_AVAILABLE = False

if _PYTESSERACT_AVAILABLE:
    _CANDIDATE_TESSERACT_PATHS = [
        os.environ.get("TESSERACT_PATH"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for _candidate in _CANDIDATE_TESSERACT_PATHS:
        if _candidate and os.path.exists(_candidate):
            pytesseract.pytesseract.tesseract_cmd = _candidate
            break


def extract_text_from_image(image: Image.Image) -> Dict:
    """
    Run OCR on a PIL Image and return the extracted text.

    Returns:
        {
            "success": bool,
            "text": str,
            "error": str or None,
        }
    """
    if not _PYTESSERACT_AVAILABLE:
        return {
            "success": False,
            "text": "",
            "error": (
                "The 'pytesseract' Python package is not installed. "
                "Run: pip install pytesseract"
            ),
        }

    try:
        # Basic preprocessing: convert to grayscale to improve OCR accuracy
        processed = image.convert("L")
        text = pytesseract.image_to_string(processed)
        text = text.strip()

        if not text:
            return {
                "success": False,
                "text": "",
                "error": (
                    "OCR ran successfully but could not detect any readable "
                    "text in this image. Try a clearer, higher-resolution "
                    "screenshot."
                ),
            }

        return {"success": True, "text": text, "error": None}

    except Exception as exc:
        error_message = str(exc)
        if "tesseract is not installed" in error_message.lower() or \
           "not in your path" in error_message.lower():
            hint = (
                "Tesseract OCR engine was not found on this system. "
                "Install it separately (see README.md) -- this is a system "
                "binary, not just a Python package."
            )
        else:
            hint = f"OCR failed: {error_message}"

        return {"success": False, "text": "", "error": hint}
