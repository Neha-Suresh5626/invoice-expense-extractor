import re

def extract_invoice_data(text):

    invoice = re.search(
        r'Invoice Number\s+(\d+)',
        text,
        re.IGNORECASE
    )

    total = re.search(
        r'Total\s+\$?(\d+[.,]?\d*)',
        text,
        re.IGNORECASE
    )

    tax = re.search(
        r'Tax\s+\$?(\d+[.,]?\d*)',
        text,
        re.IGNORECASE
    )

    return {

        "invoice_number":
        invoice.group(1) if invoice else "Not Found",

        "total":
        total.group(1) if total else "Not Found",

        "gst":
        tax.group(1) if tax else "Not Found"
    }