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


def insert_signature_with_coords(input_pdf, sig_path, output_pdf, coords):
    doc = fitz.open(input_pdf)
    page = doc[coords["page"]]

    # Apply scale correction
    x = coords["x"] / coords["scale"]
    y = coords["y"] / coords["scale"]
    w = coords["width"] / coords["scale"]
    h = coords["height"] / coords["scale"]

    page_height = page.rect.height

    # Flip Y because PDF origin is bottom-left
    y_pdf = page_height - (y + h)

    rect = fitz.Rect(x, y_pdf, x + w, y_pdf + h)

    print("DEBUG - Corrected PDF rect:", rect, flush=True)

    page.insert_image(rect, filename=sig_path)
    doc.save(output_pdf)
    doc.close()
    return rect




if __name__ == "__main__":
    app.run(debug=True)
