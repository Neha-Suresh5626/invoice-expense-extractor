"""
utils/ocr.py — Layout-aware Tesseract OCR (from your existing code, enhanced)
"""
import pytesseract
from pytesseract import Output
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def _preprocess(image_path):
    """OpenCV preprocessing: denoise, deskew, sharpen, binarize."""
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        return image_path   # fallback: use original

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # Deskew
    coords = np.column_stack(np.where(gray < 128))
    if len(coords) > 10:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) > 0.5:
            h, w = gray.shape[:2]
            M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
            gray = cv2.warpAffine(gray, M, (w, h),
                                  flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)

    # Sharpen
    pil = Image.fromarray(gray)
    pil = ImageEnhance.Sharpness(pil).enhance(2.0)
    gray = np.array(pil)

    # Binarize
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Scale up small images
    hh, ww = binary.shape
    if ww < 1000:
        scale = 1000 / ww
        binary = cv2.resize(binary, None, fx=scale, fy=scale,
                            interpolation=cv2.INTER_CUBIC)

    tmp_path = image_path + "_proc.png"
    cv2.imwrite(tmp_path, binary)
    return tmp_path


def extract_lines_with_layout(image_path, y_tolerance_ratio=0.015):
    """
    Your original layout-aware OCR function — kept intact.
    Returns (lines, reconstructed_text, width, height)
    """
    proc_path = _preprocess(image_path)
    img = Image.open(proc_path)
    w, h = img.size

    data = pytesseract.image_to_data(img, output_type=Output.DICT,
                                     config="--oem 3 --psm 6")
    words = []
    n = len(data["text"])
    for i in range(n):
        text = data["text"][i].strip()
        if not text:
            continue
        try:
            conf = int(data["conf"][i])
        except Exception:
            conf = -1
        if conf < 40:
            continue
        x      = data["left"][i]
        y      = data["top"][i]
        width  = data["width"][i]
        height = data["height"][i]
        words.append({"text": text, "left": x, "top": y,
                      "right": x + width, "bottom": y + height})

    if not words:
        # Fallback: simple string extraction
        raw = pytesseract.image_to_string(img, config="--oem 3 --psm 6")
        return [], raw.strip(), w, h

    y_tolerance  = y_tolerance_ratio * h
    words_sorted = sorted(words, key=lambda wd: wd["top"])
    lines_raw    = []
    current_line = []
    current_y    = None

    for wd in words_sorted:
        if current_y is None:
            current_line = [wd]
            current_y    = wd["top"]
            continue
        if abs(wd["top"] - current_y) <= y_tolerance:
            current_line.append(wd)
            current_y = np.mean([w["top"] for w in current_line])
        else:
            lines_raw.append(current_line)
            current_line = [wd]
            current_y    = wd["top"]
    if current_line:
        lines_raw.append(current_line)

    lines = []
    for line_words in lines_raw:
        text  = " ".join(w["text"] for w in sorted(line_words, key=lambda w: w["left"]))
        x_min = min(w["left"]   for w in line_words)
        y_min = min(w["top"]    for w in line_words)
        x_max = max(w["right"]  for w in line_words)
        y_max = max(w["bottom"] for w in line_words)
        rel_top = y_min / float(h)
        zone = "header" if rel_top < 0.2 else ("footer" if rel_top > 0.8 else "body")
        lines.append({"text": text, "x_min": x_min, "y_min": y_min,
                      "x_max": x_max, "y_max": y_max, "zone": zone})

    reconstructed_text = "\n".join(line["text"] for line in lines)
    return lines, reconstructed_text, w, h