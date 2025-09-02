import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "signed"

ALLOWED_PDF = {"pdf"}
ALLOWED_IMAGES = {"png", "jpg", "jpeg"}

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # --- Upload PDF ---
        if "pdf" not in request.files:
            flash("No PDF uploaded")
            return redirect(request.url)

        pdf_file = request.files["pdf"]
        if pdf_file.filename == "" or not allowed_file(pdf_file.filename, ALLOWED_PDF):
            flash("Invalid or missing PDF")
            return redirect(request.url)

        pdf_filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_filename)
        pdf_file.save(pdf_path)

        # --- Upload Signatures ---
        if "signatures" not in request.files:
            flash("No signatures uploaded")
            return redirect(request.url)

        signature_files = request.files.getlist("signatures")
        sig_paths = []
        for sig in signature_files:
            if sig and allowed_file(sig.filename, ALLOWED_IMAGES):
                sig_name = secure_filename(sig.filename)
                sig_path = os.path.join(app.config["UPLOAD_FOLDER"], sig_name)
                sig.save(sig_path)
                sig_paths.append(sig_path)

        if not sig_paths:
            flash("No valid signature images uploaded")
            return redirect(request.url)

        # --- Process: insert signatures into PDF ---
        output_pdf = os.path.join(app.config["OUTPUT_FOLDER"], f"signed_{pdf_filename}")
        insert_signatures_into_pdf(pdf_path, sig_paths, output_pdf)

        return redirect(url_for("download_file", filename=os.path.basename(output_pdf)))

    return render_template("upload.html")


def insert_signatures_into_pdf(pdf_path, signature_paths, output_pdf):
    doc = fitz.open(pdf_path)
    page = doc[0]  # add signatures on first page for now

    # Start coordinates near bottom-left
    x, y = 50, page.rect.height - 100
    for sig_path in signature_paths:
        rect = fitz.Rect(x, y, x + 120, y + 60)  # fixed box size
        page.insert_image(rect, filename=sig_path)
        y -= 70  # move up for next signature

    doc.save(output_pdf)
    doc.close()


@app.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(app.config["OUTPUT_FOLDER"], filename), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
