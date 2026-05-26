"""
utils/handwritten_ocr.py — EasyOCR for handwritten invoices
Returns (lines_with_layout, reconstructed_text, width, height)
"""
import easyocr
from PIL import Image

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def extract_lines_with_layout(image_path):
    reader = _get_reader()
    img    = Image.open(image_path)
    w, h   = img.size

    results = reader.readtext(image_path, detail=1, paragraph=False)
    # results: list of ([bbox], text, confidence)

    lines = []
    for (bbox, text, conf) in results:
        if conf < 0.3 or not text.strip():
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        rel_top = y_min / float(h)
        zone = "header" if rel_top < 0.2 else ("footer" if rel_top > 0.8 else "body")
        lines.append({"text": text.strip(), "x_min": x_min, "y_min": y_min,
                      "x_max": x_max, "y_max": y_max, "zone": zone})

    lines.sort(key=lambda l: l["y_min"])
    reconstructed_text = "\n".join(l["text"] for l in lines)
    return lines, reconstructed_text, w, h