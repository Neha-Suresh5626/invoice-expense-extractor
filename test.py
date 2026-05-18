from utils.ocr import extract_text
from utils.extractor import extract_invoice_data

text = extract_text(r"C:\Users\Nithya Shaji\Desktop\practice\invoice-expense-extractor\sample_invoice.jpeg")

data = extract_invoice_data(text)

print(data)