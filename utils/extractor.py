"""
utils/extractor.py — Field extraction + expense categorisation
Based on your original code, extended with more patterns and categories.
"""
import re
from utils.ai_extractor import extract_invoice_ai
# ── Expense categories ─────────────────────────────────────────────────────

CATEGORIES = {
    "Electronics":      ["laptop", "computer", "phone", "mobile", "tablet", "monitor",
                         "keyboard", "mouse", "printer", "camera", "charger", "cable",
                         "electronics", "hardware", "device"],
    "Food & Dining":    ["restaurant", "cafe", "coffee", "food", "meal", "dining",
                         "catering", "canteen", "hotel", "swiggy", "zomato", "lunch",
                         "dinner", "breakfast", "bakery", "grocery"],
    "Stationery":       ["stationery", "paper", "pen", "pencil", "folder", "binder",
                         "notebook", "ink", "toner", "office supplies", "stapler"],
    "Travel":           ["flight", "ticket", "hotel", "accommodation", "taxi", "cab",
                         "uber", "ola", "petrol", "fuel", "diesel", "travel", "train",
                         "bus", "toll", "parking"],
    "Utilities":        ["electricity", "water", "internet", "broadband", "wifi",
                         "telephone", "phone bill", "mobile bill", "gas", "utility"],
    "Software":         ["software", "subscription", "license", "cloud", "hosting",
                         "saas", "domain", "aws", "azure", "google workspace"],
    "Medical":          ["hospital", "clinic", "pharmacy", "medicine", "medical",
                         "health", "doctor", "diagnostic", "lab", "dental"],
    "Marketing":        ["advertising", "marketing", "media", "print", "brochure",
                         "banner", "campaign", "promotion", "social media"],
    "Maintenance":      ["repair", "maintenance", "service", "plumber", "electrician",
                         "cleaning", "pest control", "amc"],
}


def _to_float(s):
    if not s:
        return 0.0
    s = re.sub(r"[^\d.]", "", str(s))
    try:
        return float(s)
    except ValueError:
        return 0.0


def categorise(text):
    lower = text.lower()
    for cat, keywords in CATEGORIES.items():
        if any(kw in lower for kw in keywords):
            return cat
    return "General"


def extract_invoice_data(lines_with_layout, full_text):
    """
    Main extraction function — returns a dict with all fields.
    Keeps your original logic and adds GST, subtotal, due_date, currency, category.
    """
    data = {
        "vendor_name":    "Not Available",
        "invoice_number": "Not Available",
        "date":           "Not Available",
        "due_date":       "Not Available",
        "tax":            "0",
        "gst":            "0",
        "total":          "0",
        "subtotal":       "0",
        "currency":       "INR",
        "category":       "General",
        "raw_text":       full_text,
    }

    # ── Vendor name ─────────────────────────────────
    header_lines = [l for l in lines_with_layout if l.get("zone") == "header"]
    ignore_words = ["invoice", "bill", "tax", "amount", "qty",
                    "description", "phone", "email", "bank", "payment"]
    vendor_candidates = []
    for line in header_lines:
        text  = line["text"].strip()
        lower = text.lower()
        if len(text) < 2:
            continue
        if any(w in lower for w in ignore_words):
            continue
        if sum(c.isdigit() for c in text) > 2:
            continue
        if not re.search(r"[A-Za-z]", text):
            continue
        height = line["y_max"] - line["y_min"]
        vendor_candidates.append({"text": text, "height": height, "y": line["y_min"]})

    vendor_candidates.sort(key=lambda x: (-x["height"], x["y"]))
    if len(vendor_candidates) >= 2:
        f, s = vendor_candidates[0], vendor_candidates[1]
        data["vendor_name"] = (f["text"] + " " + s["text"]
                               if abs(f["y"] - s["y"]) < 80
                               else f["text"])
    elif len(vendor_candidates) == 1:
        data["vendor_name"] = vendor_candidates[0]["text"]

    # ── Invoice number ─────────────────────────────────────────────────────
    for pat in [
        r"(?:invoice no|invoice number|invoice #|inv no)[\s\:\.\-]*([A-Z0-9\-\/]+)",
        r"INV[\-\s]?(\d+)",
        r"#\s*([A-Z0-9\-]{3,15})",
    ]:
        m = re.search(pat, full_text, re.IGNORECASE)
        if m:
            data["invoice_number"] = m.group(1).strip()
            break

    # ── Dates ──────────────────────────────────────────────────────────────
    date_pats = [
        r"\d{1,2}[.\/\-]\d{1,2}[.\/\-]\d{2,4}",
        r"\d{1,2}\s+[A-Za-z]+\s+\d{4}",
        r"[A-Za-z]+\s+\d{1,2},?\s+\d{4}",
    ]
    found_dates = []
    for pat in date_pats:
        found_dates += re.findall(pat, full_text)

    if found_dates:
        data["date"] = found_dates[0]
        # due date context
        due_m = re.search(
            r"(?:due date|payment due|pay by)[^\d]*(\d{1,2}[.\/\-]\d{1,2}[.\/\-]\d{2,4})",
            full_text, re.IGNORECASE
        )
        if due_m:
            data["due_date"] = due_m.group(1)
        elif len(found_dates) > 1:
            data["due_date"] = found_dates[1]

    # ── Currency ───────────────────────────────────────────────────────────
    if re.search(r"\bINR\b|Rs\.?|₹|rupee", full_text, re.I):
        data["currency"] = "INR"
    elif re.search(r"\bUSD\b|\$|dollar", full_text, re.I):
        data["currency"] = "USD"
    elif re.search(r"\bEUR\b|€", full_text, re.I):
        data["currency"] = "EUR"
    elif re.search(r"\bGBP\b|£", full_text, re.I):
        data["currency"] = "GBP"

    # ── Amounts ────────────────────────────────────────────────────────────
    def find_amount(patterns):
        for pat in patterns:
            m = re.search(pat, full_text, re.IGNORECASE)
            if m:
                val = _to_float(m.group(1))
                if val > 0:
                    return str(val)
        return "0"

    data["total"] = find_amount([
        r"(?:grand total|total amount|amount due|net payable|total due)[\s\:\.\-]*[$£€₹]?\s*([\d\,\.]+)",
        r"total[\s\:\.\-]*[$£€₹]?\s*([\d\,\.]+)",
        r"[$£€₹]\s*([\d\,\.]+)\s*$",
    ])

    data["subtotal"] = find_amount([
        r"(?:subtotal|sub total|net amount|before tax)[\s\:\.\-]*[$£€₹]?\s*([\d\,\.]+)",
    ])

    data["tax"] = find_amount([
        r"(?:tax|vat|service tax)[\s\:\.\(\-]*(%?[\d\,\.]+)",
    ])

    data["gst"] = find_amount([
        r"(?:gst|igst|cgst|sgst)[\s\:\.\(\-]*[$£€₹]?\s*([\d\,\.]+)",
        r"goods\s*and\s*services\s*tax[\s\:]*[$£€₹]?\s*([\d\,\.]+)",
    ])
    # Fallback: calculate GST from percentage
    if data["gst"] == "0":
        gst_pct = re.search(r"gst\s*@?\s*(\d+)\s*%", full_text, re.I)
        total_f = _to_float(data["total"])
        if gst_pct and total_f > 0:
            rate = float(gst_pct.group(1)) / 100
            data["gst"] = str(round(total_f * rate / (1 + rate), 2))

    # ── Category ───────────────────────────────────────────────────────────
    data["category"] = categorise(full_text)
    # ── Gemini AI Enhancement ──────────────────────────────────────────────
    try:

        ai_data = extract_invoice_ai(full_text)

        for field in [
          "vendor_name",
          "invoice_number",
          "date",
          "subtotal",
          "gst",
          "tax",
          "total"
    ]:
          value = ai_data.get(field)

          if value and str(value).strip():

            data[field] = str(value)

    except Exception as e:

        print("Gemini Error:", e)

    return data
