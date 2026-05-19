from utils.exporter import generate_excel

sample_data = {

    "invoice_number": "000000",

    "gst": "520.00",

    "total": "4520.00"
}

path = generate_excel(sample_data)

print(path)