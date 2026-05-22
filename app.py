from flask import Flask, render_template, request
import os

from utils.ocr import extract_lines_with_layout
from utils.extractor import extract_invoice_data
from utils.exporter import export_to_excel
from utils.db import init_db, insert_invoice, get_all_invoices

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():

    if "invoice" not in request.files:
        return render_template("error.html", message="No file uploaded")

    file = request.files["invoice"]

    if file.filename == "":
        return render_template("error.html", message="No selected file")

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    try:

        lines, full_text, w, h = extract_lines_with_layout(filepath)

        data = extract_invoice_data(lines, full_text)

        insert_invoice(data)

        excel_path = os.path.join(
            app.config["OUTPUT_FOLDER"],
            "invoice_data.xlsx"
        )

        export_to_excel(data, excel_path)

        return render_template(
            "result.html",
            data=data
        )

    except Exception as e:

        return render_template(
            "error.html",
            message=str(e)
        )


@app.route("/dashboard")
def dashboard():

    invoices = get_all_invoices()

    total_expense = 0

    for inv in invoices:

        try:
            total_expense += float(inv[5])
        except:
            pass

    return render_template(
        "dashboard.html",
        invoices=invoices,
        total_expense=total_expense,
        invoice_count=len(invoices)
    )


if __name__ == "__main__":
    app.run(debug=True)