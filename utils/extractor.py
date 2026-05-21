# extractor.py
import re
import spacy

# load spaCy English model (do this once at import)
nlp = spacy.load("en_core_web_sm")


def _classify_line_features(line_text: str):
    """
    Simple keyword-based classification of a line.
    """
    txt = line_text.lower()

    features = {
        "is_billing_block": False,
        "is_bank_block": False,
        "is_table_row": False,
    }

    billing_kw = ["bill to", "billed to", "ship to", "invoice to", "customer", "client"]
    if any(k in txt for k in billing_kw):
        features["is_billing_block"] = True

    bank_kw = ["bank", "ifsc", "iban", "account", "acc no", "swift", "upi", "branch"]
    if any(k in txt for k in bank_kw):
        features["is_bank_block"] = True

    table_kw = ["qty", "quantity", "description", "hsn", "rate", "amount", "unit", "price"]
    if any(k in txt for k in table_kw):
        features["is_table_row"] = True

    # numeric-heavy line -> likely part of items / totals
    tokens = txt.split()
    if tokens:
        num_ratio = sum(t.replace(".", "", 1).isdigit() for t in tokens) / len(tokens)
        if num_ratio > 0.5:
            features["is_table_row"] = True

    return features


def _score_vendor_candidate(ent_text: str, zone: str, features: dict):
    """
    Score a candidate vendor name using layout + keyword heuristics.
    Higher is better.
    """
    score = 0

    # zone
    if zone == "header":
        score += 5
    elif zone == "body":
        score += 2
    elif zone == "footer":
        score -= 2

    # negative features
    if features.get("is_billing_block"):
        score -= 5
    if features.get("is_bank_block"):
        score -= 4
    if features.get("is_table_row"):
        score -= 4

    # length of the entity (number of words)
    words = ent_text.split()
    if 2 <= len(words) <= 6:
        score += 2
    elif len(words) == 1:
        score -= 1  # too short, often noise

    # positive vendor hints
    vendor_keywords = [
        "ltd",
        "limited",
        "pvt",
        "private",
        "pvt.",
        "corp",
        "corporation",
        "company",
        "co.",
        "solutions",
        "technologies",
        "studios",
        "studio",
        "salon",
        "store",
        "traders",
        "enterprises",
        "services",
    ]
    txt_lower = ent_text.lower()
    if any(k in txt_lower for k in vendor_keywords):
        score += 3

    # negative hints
    customer_words = ["customer", "client", "ship to", "bill to", "invoice to"]
    if any(w in txt_lower for w in customer_words):
        score -= 3

    bank_words = ["bank", "financial services"]
    if any(w in txt_lower for w in bank_words):
        score -= 3

    return score


def extract_invoice_data(lines_with_layout, full_text):
    """
    Extract invoice fields from:
      - lines_with_layout: list of line dicts from OCR (see ocr.py)
      - full_text: full OCR text (for regex-based fields)

    Returns dict with keys:
      vendor_name, invoice_number, date, tax, total
    """

    data = {
        "vendor_name": "Not Available",
        "invoice_number": "Not Available",
        "date": "Not Available",
        "tax": "Not Available",
        "total": "Not Available",
    }

    # ------------------------------------------------------------------
    # 1) VENDOR NAME DETECTION (layout + spaCy)
    # ------------------------------------------------------------------

    candidates = []

    for line in lines_with_layout:
        text = line["text"].strip()
        if not text:
            continue

        # basic garbage filters similar to your old logic
        if len(text) < 3:
            continue
        if sum(c.isdigit() for c in text) > 2:
            continue
        if not re.search(r"[A-Za-z]", text):
            continue
        if len(text.split()) > 8:
            # long paragraphs are unlikely vendor names
            continue

        features = _classify_line_features(text)

        # hard skip lines that are clearly bank or table related
        if features["is_bank_block"] or features["is_table_row"]:
            continue

        # restrict search area:
        # - always consider header
        # - consider body only if it's in upper part (e.g. above mid-page)
        zone = line["zone"]
        y_min = line["y_min"]
        # we don't have page height here, so rely mostly on zone:
        if zone == "body":
            # optional: you can pass page_h into this function and use
            # y_min < 0.5 * page_h to restrict further
            pass

        # NER to find organization-like entities within the line
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "GPE", "FAC"]:
                score = _score_vendor_candidate(ent.text, zone, features)
                candidates.append((ent.text.strip(), score))

        # if no entity found, you may treat whole line as candidate with small base score
        if not any(ent.label_ in ["ORG", "GPE", "FAC"] for ent in doc.ents):
            score = _score_vendor_candidate(text, zone, features) - 1  # slightly penalize
            candidates.append((text, score))

    if candidates:
        best_name, best_score = max(candidates, key=lambda x: x[1])
        # threshold so we don't pick total garbage
        if best_score >= 2:
            data["vendor_name"] = best_name
        else:
            # fallback: first non-empty header line
            header_lines = [l["text"] for l in lines_with_layout if l["zone"] == "header" and l["text"].strip()]
            if header_lines:
                data["vendor_name"] = header_lines[0].strip()
    else:
        # no candidates at all: fallback to first header line
        header_lines = [l["text"] for l in lines_with_layout if l["zone"] == "header" and l["text"].strip()]
        if header_lines:
            data["vendor_name"] = header_lines[0].strip()

    # ------------------------------------------------------------------
    # 2) INVOICE NUMBER (mostly your original logic)
    # ------------------------------------------------------------------

    cleaned_text = "\n".join(
        [line["text"].strip() for line in lines_with_layout if line["text"].strip()]
    )

    invoice_patterns = [
        r"(?:invoice no|invoice number|invoice #)[\s\:]*([A-Z0-9\-]+)",
        r"INV[\-\s]?(\d+)",
        r"No\.\s*(\d+)",
    ]

    for pattern in invoice_patterns:
        match = re.search(pattern, cleaned_text, re.IGNORECASE)
        if match:
            data["invoice_number"] = match.group(1)
            break

    # fallback simple invoice number
    if data["invoice_number"] == "Not Available":
        simple_inv = re.search(r"\b\d{4,8}\b", cleaned_text)
        if simple_inv:
            data["invoice_number"] = simple_inv.group()

    # ------------------------------------------------------------------
    # 3) DATE EXTRACTION
    # ------------------------------------------------------------------

    date_patterns = [
        r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",
        r"\d{1,2}\s+[A-Za-z]+\s+\d{4}",
        r"[A-Za-z]+\s+\d{1,2},\s+\d{4}",
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}",
    ]

    for pattern in date_patterns:
        match = re.search(pattern, cleaned_text)
        if match:
            data["date"] = match.group(0)
            break

    # ------------------------------------------------------------------
    # 4) TAX / GST EXTRACTION
    # ------------------------------------------------------------------

    tax_patterns = [
        r"(?:tax|gst|vat)[\s\:\.\(]*([\d\,\.%]+)",
        r"TAX\s*\(?(\d+)%?\)?",
    ]

    for pattern in tax_patterns:
        match = re.search(pattern, cleaned_text, re.IGNORECASE)
        if match:
            value = match.group(1)
            if "%" not in value and value.isdigit():
                value += "%"
            data["tax"] = value
            break

    # ------------------------------------------------------------------
    # 5) TOTAL AMOUNT EXTRACTION
    # ------------------------------------------------------------------

    total_patterns = [
        r"(?:grand total|total|amount due|balance due)[\s\:\.]*[$£€₹]?\s*([\d\,\.]+)"
    ]

    for pattern in total_patterns:
        match = re.search(pattern, cleaned_text, re.IGNORECASE)
        if match:
            data["total"] = match.group(1)
            break

    # fallback: largest currency-like value
    if data["total"] == "Not Available":
        money_values = re.findall(r"[$£€₹]\s?([\d,]+\.?\d*)", cleaned_text)
        numeric_values = []
        for value in money_values:
            try:
                numeric_values.append(float(value.replace(",", "")))
            except Exception:
                pass
        if numeric_values:
            data["total"] = max(numeric_values)

    return data