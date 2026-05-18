import re

def extract_invoice_data(text):

    total = re.search(r'Total.*?(\d+)', text)

    gst = re.search(r'GST.*?(\d+)', text)

    invoice = re.search(r'Invoice.*?(\w+)', text)

    return {

        "total": total.group(1) if total else "Not Found",

        "gst": gst.group(1) if gst else "Not Found",

        "invoice_number": invoice.group(1) if invoice else "Not Found"
    }