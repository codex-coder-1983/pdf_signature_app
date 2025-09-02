from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from PIL import Image
import os
import uuid
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_ROOT = BASE_DIR / "uploads"
COMBINED_ROOT = BASE_DIR / "combined"
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB per request (adjust as needed)

for d in (UPLOAD_ROOT, COMBINED_ROOT):
    d.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def allowed_filename(filename: str) -> bool:
    return "." in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@app.route('/')
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload():
    # Create a session folder so multiple users/sessions don't collide
    session_id = uuid.uuid4().hex
    session_folder = UPLOAD_ROOT / session_id
    session_folder.mkdir()

    files = request.files.getlist('signatures')
    if not files:
        flash('No files uploaded', 'error')
        return redirect(url_for('index'))

    saved_paths = []
    for f in files:
        if f and allowed_filename(f.filename):
            filename = secure_filename(f.filename)
            path = session_folder / filename
            f.save(path)
            saved_paths.append(path)
        else:
            flash(f'File not allowed: {f.filename}', 'error')

    if not saved_paths:
        flash('No valid files to process', 'error')
        return redirect(url_for('index'))

    # Combine signatures vertically (change logic below for other layouts)
    combined_filename = f"combined_{session_id}.png"
    combined_path = COMBINED_ROOT / combined_filename
    try:
        combine_images_vertically(saved_paths, combined_path)
    except Exception as e:
        flash(f'Error combining images: {e}', 'error')
        return redirect(url_for('index'))

    return render_template('result.html', download_url=url_for('download', filename=combined_filename))


@app.route('/combined/<path:filename>')
def download(filename):
    return send_from_directory(COMBINED_ROOT, filename, as_attachment=True)


def combine_images_vertically(image_paths, out_path):
    """Open images, convert to RGBA for uniformity, and stack vertically with minimal padding."""
    imgs = [Image.open(p).convert('RGBA') for p in image_paths]

    # Normalize widths: use max width, scale others proportionally
    max_w = max(img.width for img in imgs)
    resized = []
    for img in imgs:
        if img.width != max_w:
            new_h = int(img.height * (max_w / img.width))
            img = img.resize((max_w, new_h), Image.LANCZOS)
        resized.append(img)

    total_h = sum(img.height for img in resized)
    combined = Image.new('RGBA', (max_w, total_h), (255, 255, 255, 0))

    y = 0
    for img in resized:
        combined.paste(img, (0, y), img)
        y += img.height

    combined.save(out_path)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
