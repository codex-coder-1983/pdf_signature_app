import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "signed"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Globals for demo (better: use session or DB for multi-user support)
pdf_path, sig_path = None, None


@app.route("/", methods=["GET", "POST"])
def upload_and_preview():
    """Upload PDF + signature, return PDF for preview."""
    global pdf_path, sig_path

    if request.method == "POST":
        if "pdf" not in request.files or "signature" not in request.files:
            return "Missing PDF or signature file", 400

        pdf_file = request.files["pdf"]
        sig_file = request.files["signature"]

        if pdf_file.filename == "" or sig_file.filename == "":
            return "No selected files", 400

        pdf_filename = secure_filename(pdf_file.filename)
        sig_filename = secure_filename(sig_file.filename)

        pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_filename)
        sig_path = os.path.join(app.config["UPLOAD_FOLDER"], sig_filename)

        pdf_file.save(pdf_path)
        sig_file.save(sig_path)

        return send_file(pdf_path, as_attachment=False)

    return render_template("upload.html")


@app.route("/place_signature", methods=["POST"])
def place_signature():
    """Insert signature into PDF at given coordinates."""
    global pdf_path, sig_path
    coords = request.json

    if not pdf_path or not sig_path:
        return "No uploaded PDF/signature found", 400

    output_pdf = os.path.join(app.config["OUTPUT_FOLDER"], "signed.pdf")
    insert_signature_with_coords(pdf_path, sig_path, output_pdf, coords)

    return send_file(output_pdf, as_attachment=True)


def insert_signature_with_coords(pdf_path, sig_path, output_pdf, coords):
    """Insert signature image into PDF using coordinates from frontend."""
    doc = fitz.open(pdf_path)
    page = doc[coords["page"]]

    # PDF coordinates: bottom-left origin
    page_height = page.rect.height
    x, y = coords["x"], coords["y"]
    width, height = coords["width"], coords["height"]

    rect = fitz.Rect(x, page_height - y - height, x + width, page_height - y)

    page.insert_image(rect, filename=sig_path, keep_proportion=False, overlay=True)

    doc.save(output_pdf)
    doc.close()


if __name__ == "__main__":
    app.run(debug=True)
