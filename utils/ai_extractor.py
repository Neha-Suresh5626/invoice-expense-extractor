import google.generativeai as genai
import json

import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


def extract_invoice_ai(text):

    prompt = f"""
You are an invoice information extractor.

Extract:

- vendor_name
- invoice_number
- date
- subtotal
- gst
- tax
- total

Rules:
1. Return ONLY valid JSON.
2. Extract both gst and tax separately if available.
3. If only one tax value exists, put the same value in both gst and tax.
4. Ignore billed-to customer names.
5. Ignore item descriptions.
6. Vendor name must be the company issuing the invoice.

Invoice Text:
{text}
"""

    response = model.generate_content(prompt)

    result = response.text

    result = result.replace("```json", "")
    result = result.replace("```", "")
    result = result.strip()

    return json.loads(result)