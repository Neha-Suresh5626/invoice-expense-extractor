import re


def extract_invoice_data(lines_with_layout, full_text):

    data = {
        "vendor_name": "Not Available",
        "invoice_number": "Not Available",
        "date": "Not Available",
        "tax": "Not Available",
        "total": "Not Available",
    }

    header_lines = [
        line
        for line in lines_with_layout
        if line["zone"] == "header"
    ]

    vendor_candidates = []

    ignore_words = [
        "invoice",
        "bill",
        "tax",
        "amount",
        "qty",
        "description",
        "phone",
        "email",
        "bank",
        "payment"
    ]

    for line in header_lines:

        text = line["text"].strip()

        lower = text.lower()

        if len(text) < 2:
            continue

        if any(word in lower for word in ignore_words):
            continue

        if sum(c.isdigit() for c in text) > 2:
            continue

        if not re.search(r"[A-Za-z]", text):
            continue

        height = line["y_max"] - line["y_min"]

        vendor_candidates.append({
            "text": text,
            "height": height,
            "y": line["y_min"]
        })

    vendor_candidates = sorted(
        vendor_candidates,
        key=lambda x: (-x["height"], x["y"])
    )

    if len(vendor_candidates) >= 2:

        first = vendor_candidates[0]
        second = vendor_candidates[1]

        if abs(first["y"] - second["y"]) < 80:

            vendor_name = (
                first["text"]
                + " "
                + second["text"]
            )

        else:
            vendor_name = first["text"]

    elif len(vendor_candidates) == 1:

        vendor_name = vendor_candidates[0]["text"]

    else:

        vendor_name = "Not Available"

    data["vendor_name"] = vendor_name

    cleaned_text = full_text

    invoice_patterns = [
        r"(?:invoice no|invoice number|invoice #)[\s\:]*([A-Z0-9\-]+)",
        r"INV[\-\s]?(\d+)"
    ]

    for pattern in invoice_patterns:

        match = re.search(
            pattern,
            cleaned_text,
            re.IGNORECASE
        )

        if match:
            data["invoice_number"] = match.group(1)
            break

    date_patterns = [
        r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}",
        r"\d{1,2}\s+[A-Za-z]+\s+\d{4}",
        r"[A-Za-z]+\s+\d{1,2},\s+\d{4}"
    ]

    for pattern in date_patterns:

        match = re.search(pattern, cleaned_text)

        if match:
            data["date"] = match.group(0)
            break

    tax_patterns = [
        r"(?:tax|gst|vat)[\s\:\.\(]*([\d\,\.%]+)"
    ]

    for pattern in tax_patterns:

        match = re.search(
            pattern,
            cleaned_text,
            re.IGNORECASE
        )

        if match:
            data["tax"] = match.group(1)
            break

    total_patterns = [
        r"(?:grand total|total|amount due)[\s\:\.]*[$£€₹]?\s*([\d\,\.]+)"
    ]

    for pattern in total_patterns:

        match = re.search(
            pattern,
            cleaned_text,
            re.IGNORECASE
        )

        if match:
            data["total"] = match.group(1)
            break

    return data