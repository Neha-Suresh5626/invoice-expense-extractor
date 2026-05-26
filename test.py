"""
test.py — Quick smoke-test without a browser
Run:  python test.py
"""
from utils.db import init_db, create_user, get_user
from utils.extractor import extract_invoice_data, categorise

init_db()

# Test user creation
ok = create_user("testuser", "abc123hash")
print("User created:", ok)
user = get_user("testuser")
print("User fetched:", user["username"] if user else "NOT FOUND")

# Test extraction on sample text
sample = """
ABC Electronics Pvt Ltd
Invoice No: INV-2024-001
Date: 15/03/2024
Due Date: 30/03/2024

Laptop Dell XPS 15      ₹85,000
GST @ 18%               ₹15,300
Total Amount Due       ₹1,00,300
"""
data = extract_invoice_data([], sample)
print("\nExtracted:")
for k, v in data.items():
    if k != "raw_text":
        print(f"  {k}: {v}")

print("\nAll tests passed ✓")