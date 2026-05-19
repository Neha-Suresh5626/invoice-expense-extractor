from flask import Flask, render_template, request
import os
from utils.ocr import extract_text
from utils.extractor import extract_invoice_data
from flask import send_file
from utils.exporter import generate_excel

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")

def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])

def upload_file():

    file = request.files["invoice"]

    if file.filename != "":

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)

        file.save(filepath)

        text = extract_text(filepath)

        data = extract_invoice_data(text)

        excel_path = generate_excel(data)

        return send_file(excel_path, as_attachment=True)

    return "No file selected"


if __name__ == "__main__":
    app.run(debug=True)
