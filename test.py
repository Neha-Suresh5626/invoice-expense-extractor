from utils.ocr import extract_text
from utils.extractor import extract_invoice_data

text = extract_text("sample_invoice.jpeg")

print(text)

data = extract_invoice_data(text)

print(data)