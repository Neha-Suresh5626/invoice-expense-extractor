import pytesseract
from pytesseract import Output
from PIL import Image
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_lines_with_layout(image_path, y_tolerance_ratio=0.015):

    img = Image.open(image_path)

    w, h = img.size

    data = pytesseract.image_to_data(
        img,
        output_type=Output.DICT
    )

    words = []

    n = len(data["text"])

    for i in range(n):

        text = data["text"][i].strip()

        if not text:
            continue

        try:
            conf = int(data["conf"][i])
        except:
            conf = -1

        if conf < 40:
            continue

        x = data["left"][i]
        y = data["top"][i]
        width = data["width"][i]
        height = data["height"][i]

        words.append({
            "text": text,
            "left": x,
            "top": y,
            "right": x + width,
            "bottom": y + height
        })

    if not words:
        return [], "", w, h

    y_tolerance = y_tolerance_ratio * h

    words_sorted = sorted(
        words,
        key=lambda w: w["top"]
    )

    lines_raw = []

    current_line = []
    current_y = None

    for wd in words_sorted:

        if current_y is None:
            current_line = [wd]
            current_y = wd["top"]
            continue

        if abs(wd["top"] - current_y) <= y_tolerance:

            current_line.append(wd)

            current_y = np.mean(
                [w["top"] for w in current_line]
            )

        else:

            lines_raw.append(current_line)

            current_line = [wd]
            current_y = wd["top"]

    if current_line:
        lines_raw.append(current_line)

    lines = []

    for line_words in lines_raw:

        text = " ".join(
            w["text"]
            for w in sorted(
                line_words,
                key=lambda w: w["left"]
            )
        )

        x_min = min(w["left"] for w in line_words)
        y_min = min(w["top"] for w in line_words)
        x_max = max(w["right"] for w in line_words)
        y_max = max(w["bottom"] for w in line_words)

        rel_top = y_min / float(h)

        if rel_top < 0.2:
            zone = "header"
        elif rel_top > 0.8:
            zone = "footer"
        else:
            zone = "body"

        lines.append({
            "text": text,
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
            "zone": zone
        })

    reconstructed_text = "\n".join(
        line["text"]
        for line in lines
    )

    return lines, reconstructed_text, w, h