"""
app.py — Main Flask Application
Routes: auth, upload, result, dashboard, history, error
"""

import os
import uuid
import hashlib

from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file
)

from werkzeug.utils import secure_filename

from utils.db import (
    init_db,
    create_user,
    get_user,
    insert_invoice,
    get_all_invoices,
    get_invoice,
    get_summary,
    get_by_category,
    get_by_vendor,
    get_by_month,
    get_gst_summary
)

from utils.pdf_processor import pdf_to_image

from utils.ocr import (
    extract_lines_with_layout as typed_ocr
)

from utils.handwritten_ocr import (
    extract_lines_with_layout as hw_ocr
)

from utils.extractor import extract_invoice_data

from utils.exporter import export_to_excel


# ---------------------------------------------------
# APP CONFIG
# ---------------------------------------------------

app = Flask(__name__)

app.secret_key = "invoiceiq_secret_2024"

app.config["UPLOAD_FOLDER"] = "uploads"

app.config["OUTPUT_FOLDER"] = "outputs"

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


ALLOWED = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "tiff",
    "bmp"
}


# ---------------------------------------------------
# INITIALIZE DATABASE
# ---------------------------------------------------

init_db()


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def hash_pw(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


def allowed(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED
    )


def login_required(f):

    @wraps(f)

    def decorated(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------

@app.route("/register", methods=["GET", "POST"])

def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if not username or not password:

            return render_template(
                "auth.html",
                mode="register",
                error="All fields required."
            )

        if len(password) < 6:

            return render_template(
                "auth.html",
                mode="register",
                error="Password must be at least 6 characters."
            )

        ok = create_user(
            username,
            hash_pw(password)
        )

        if not ok:

            return render_template(
                "auth.html",
                mode="register",
                error="Username already taken."
            )

        return redirect(
            url_for(
                "login",
                msg="Account created successfully!"
            )
        )

    return render_template(
        "auth.html",
        mode="register"
    )


# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------

@app.route("/login", methods=["GET", "POST"])

def login():

    msg = request.args.get("msg", "")

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        user = get_user(username)

        if not user or user["password"] != hash_pw(password):

            return render_template(
                "auth.html",
                mode="login",
                error="Invalid credentials."
            )

        session["user_id"] = user["id"]

        session["username"] = user["username"]

        return redirect(
            url_for("index")
        )

    return render_template(
        "auth.html",
        mode="login",
        msg=msg
    )


# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------

@app.route("/logout")

def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ---------------------------------------------------
# HOME / UPLOAD
# ---------------------------------------------------

@app.route("/", methods=["GET", "POST"])

@login_required

def index():

    if request.method == "POST":

        file = request.files.get("file")

        invoice_type = request.form.get(
            "invoice_type",
            "typed"
        )

        # -----------------------------------
        # VALIDATIONS
        # -----------------------------------

        if not file or file.filename == "":

            return render_template(
                "error.html",
                error="No file selected."
            )

        if not allowed(file.filename):

            return render_template(
                "error.html",
                error="Invalid file type."
            )

        # -----------------------------------
        # SAVE FILE
        # -----------------------------------

        ext = file.filename.rsplit(".", 1)[1].lower()

        uid_name = (
            uuid.uuid4().hex
            + "."
            + ext
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            uid_name
        )

        file.save(filepath)

        try:

            # -----------------------------------
            # PDF → IMAGE
            # -----------------------------------

            image_path = (
                pdf_to_image(filepath)
                if ext == "pdf"
                else filepath
            )

            # -----------------------------------
            # OCR ENGINE
            # -----------------------------------

            if invoice_type == "handwritten":

                lines, raw_text, w, h = hw_ocr(
                    image_path
                )

            elif invoice_type == "mixed":

                lines, raw_text, w, h = typed_ocr(
                    image_path
                )

                if len(raw_text.strip()) < 20:

                    lines, raw_text, w, h = hw_ocr(
                        image_path
                    )

            else:

                lines, raw_text, w, h = typed_ocr(
                    image_path
                )

            # -----------------------------------
            # EXTRACT DATA
            # -----------------------------------

            data = extract_invoice_data(
                lines,
                raw_text
            )

            data["invoice_type"] = invoice_type

            data["filename"] = file.filename

            # -----------------------------------
            # SAVE TO DATABASE
            # -----------------------------------

            insert_invoice(
                data,
                session["user_id"]
            )

            # -----------------------------------
            # USER-SPECIFIC EXCEL EXPORT
            # -----------------------------------

            excel_path = export_to_excel(
                data,
                app.config["OUTPUT_FOLDER"],
                session["username"]
            )

            data["excel_file"] = os.path.basename(
                excel_path
            )

            # -----------------------------------
            # SHOW RESULT
            # -----------------------------------

            return render_template(
                "result.html",
                data=data
            )

        except Exception as e:

            return render_template(
                "error.html",
                error=str(e)
            )

    return render_template(
        "index.html",
        username=session.get("username", "")
    )


# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------

@app.route("/dashboard")

@login_required

def dashboard():

    uid = session["user_id"]

    summary = get_summary(uid)

    by_cat = get_by_category(uid)

    by_vendor = get_by_vendor(uid)

    by_month = get_by_month(uid)

    gst_data = get_gst_summary(uid)

    return render_template(
        "dashboard.html",
        username=session.get("username", ""),
        summary=summary,
        by_cat=by_cat,
        by_vendor=by_vendor,
        by_month=by_month,
        gst_data=gst_data
    )


# ---------------------------------------------------
# HISTORY
# ---------------------------------------------------

@app.route("/history")

@login_required

def history():

    invoices = get_all_invoices(
        session["user_id"]
    )

    return render_template(
        "history.html",
        username=session.get("username", ""),
        invoices=invoices
    )


# ---------------------------------------------------
# DOWNLOAD EXCEL
# ---------------------------------------------------

@app.route("/download/<filename>")

@login_required

def download(filename):

    path = os.path.join(
        app.config["OUTPUT_FOLDER"],
        filename
    )

    if not os.path.exists(path):

        return render_template(
            "error.html",
            error="File not found."
        )

    return send_file(
        path,
        as_attachment=True
    )


# ---------------------------------------------------
# ERRORS
# ---------------------------------------------------

@app.errorhandler(413)

def too_large(e):

    return render_template(
        "error.html",
        error="File too large (max 16 MB)."
    ), 413


@app.errorhandler(404)

def not_found(e):

    return render_template(
        "error.html",
        error="Page not found."
    ), 404


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if __name__ == "__main__":

    os.makedirs(
        "uploads",
        exist_ok=True
    )

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    app.run(
        debug=True,
        port=5000
    )