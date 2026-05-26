"""
utils/pdf_processor.py — PDF → image for OCR
"""
import os
import pdf2image


def pdf_to_image(pdf_path: str) -> str:
    pages = pdf2image.convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    if not pages:
        raise ValueError("Could not convert PDF. Is Poppler installed?")
    out_path = pdf_path.rsplit(".", 1)[0] + "_p1.png"
    pages[0].save(out_path, "PNG")
    return out_path