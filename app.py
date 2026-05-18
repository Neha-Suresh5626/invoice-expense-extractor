from flask import Flask, render_template, request
import os

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

        return f"{file.filename} uploaded successfully"

    return "No file selected"


if __name__ == "__main__":
    app.run(debug=True)
