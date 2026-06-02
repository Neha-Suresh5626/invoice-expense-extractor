# InvoiceIQ — Invoice Processing & Expense Analytics

Internship MVP matching the full flowchart architecture.

## Features

- **Login / User Authentication** — register, login, per-user data
- **Select Invoice Type** — Typed / Handwritten / Mixed
- **OCR** — Tesseract (typed) + EasyOCR (handwritten)
- **AI Extraction** — Google Gemini 2.5 Flash
- **AI-Powered Field Extraction** — Gemini AI + OCR
    - Vendor
    - Invoice Number
    - Date
    - Due Date
    - Total
    - GST
    - Tax
    - Currency
- **Expense Categorisation** — Electronics, Food, Stationery, Travel, Utilities, Software, Medical, Marketing, Maintenance
- **Analytics Dashboard**
  - Monthly spend trend (line chart)
  - Category pie chart
  - Vendor bar chart + donut chart
  - GST analysis (horizontal bar + table)
- **Excel Export** — formatted, appends every invoice
- **Invoice History** — filterable table


## Architecture

Invoice
   ↓
OCR (Tesseract / EasyOCR)
   ↓
Raw Text Extraction
   ↓
Gemini AI Field Extraction
   ↓
SQLite Database
   ↓
Dashboard & Analytics


## Tech Stack

| Layer            | Tool                           |
| ---------------- | ------------------------------ |
| Backend          | Python, Flask                  |
| OCR Typed        | Tesseract + pytesseract        |
| OCR Handwritten  | EasyOCR                        |
| PDF              | pdf2image + Poppler            |
| Image Processing | OpenCV, Pillow                 |
| Database         | SQLite                         |
| Export           | pandas + openpyxl              |
| Charts           | Chart.js (frontend)            |
| UI               | IBM Plex Mono/Sans, dark theme |
| AI Extraction    | Google Gemini 2.5 Flash        |

## Setup

### 1. System Dependencies

**Linux/Ubuntu:**

```bash
sudo apt install tesseract-ocr poppler-utils -y
```

**macOS:**

```bash
brew install tesseract poppler
```

**Windows:**

- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Poppler: https://github.com/oschwartz10612/poppler-windows/releases
- Add both to system PATH
- Uncomment the tesseract_cmd line in `utils/ocr.py`

### 2. Python Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=YOUR_API_KEY
```

### 3. Run

```bash
python app.py
# Open: http://localhost:5000
```

### 4. Quick test (no browser)

```bash
python test.py
```

## Project Structure

```
invoice-expense-extractor/
├── app.py               ← Flask routes (auth, upload, dashboard, history)
├── test.py              ← smoke tests
├── database.db          ← SQLite (auto-created)
├── requirements.txt
├── README.md
├── .gitignore
├── uploads/             ← uploaded invoices (runtime)
├── outputs/             ← Excel exports (runtime)
├── .env                ← Gemini API key (not tracked)
├── static/
│   ├── style.css        ← IBM Plex dark theme
│   └── charts.js        ← Chart.js config (5 chart types)
├── templates/
│   ├── auth.html        ← login + register
│   ├── index.html       ← upload + invoice type selector
│   ├── result.html      ← extracted fields + download
│   ├── dashboard.html   ← analytics (monthly/vendor/GST/category)
│   ├── history.html     ← all invoices table
│   └── error.html
└── utils/
    ├── ocr.py           ← Tesseract, layout-aware (your original code)
    ├── handwritten_ocr.py ← EasyOCR
    ├── extractor.py     ← regex extraction + categorisation
    ├── exporter.py      ← Excel generation
    ├── ai_extractor.py  ← Gemini-powered invoice extraction
    ├── db.py            ← SQLite (users + invoices + analytics queries)
    └── pdf_processor.py ← PDF → PNG
```

## Windows Tesseract Fix

Uncomment in `utils/ocr.py`:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```
