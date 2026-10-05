"""
AI-Based Image to ASCII Art Generator with Interactive Web Interface
---------------------------------------------------------------------
Modules (as per project report, Chapter 2):
  1. Upload Module            -> handles incoming image files
  2. Image Processing Module  -> grayscale conversion + proportional resize
  3. ASCII Conversion Module  -> pixel intensity -> ASCII symbol mapping
  4. Rendering Module         -> ASCII text -> styled PNG image (PIL)
  5. Storage Module           -> saves originals + generated ASCII art
  6. Display Module           -> serves results to the dashboard
"""

import os
import uuid
from datetime import datetime

import cv2
import numpy as np
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename

# --------------------------------------------------------------------------
# App configuration
# --------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ascii-art-generator-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ASCII_FOLDER = os.path.join(BASE_DIR, "static", "ascii_art")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ASCII_FOLDER"] = ASCII_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}

# Characters ordered from "dense" (dark) to "sparse" (light).
# 11 symbols map cleanly onto pixel_value // 25 (range 0-10 for 0-255).
ASCII_SYMBOLS = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]

# Fonts to try, in order, before giving up on a monospace font.
FONT_CANDIDATES = [
    "DejaVuSansMono.ttf",                                   # common on Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",  # explicit Linux path
    "cour.ttf",                                             # Windows Courier New
    "Courier New.ttf",
    "/Library/Fonts/Courier New.ttf",                       # macOS
]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def ensure_folders() -> None:
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["ASCII_FOLDER"], exist_ok=True)


def load_monospace_font(size: int):
    """Try a list of common monospace fonts; fall back to PIL's default bitmap font."""
    for font_path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue
    # Last resort: PIL's built-in bitmap font (always available, not scalable)
    return ImageFont.load_default()


# --------------------------------------------------------------------------
# Module 2: Image Processing
# --------------------------------------------------------------------------
def preprocess_image(image: np.ndarray, new_width: int = 120) -> np.ndarray:
    """Resize a grayscale image proportionally for ASCII conversion.

    The 0.55 factor compensates for the fact that terminal/monospace
    characters are roughly twice as tall as they are wide, keeping the
    final ASCII output visually proportional to the source image.
    """
    height, width = image.shape
    aspect_ratio = height / width
    new_height = max(1, int(aspect_ratio * new_width * 0.55))
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


# --------------------------------------------------------------------------
# Module 3: ASCII Conversion
# --------------------------------------------------------------------------
def convert_to_ascii(image: np.ndarray) -> str:
    """Map a grayscale, resized image's pixel intensities to ASCII symbols."""
    resized = preprocess_image(image)
    rows = []
    for row in resized:
        # index // 25 -> clamp to valid symbol range (0-10)
        line = "".join(ASCII_SYMBOLS[min(pixel // 25, len(ASCII_SYMBOLS) - 1)] for pixel in row)
        rows.append(line)
    return "\n".join(rows)


# --------------------------------------------------------------------------
# Module 4: Rendering (ASCII text -> styled PNG)
# --------------------------------------------------------------------------
def ascii_to_image(
    ascii_text: str,
    font_size: int = 10,
    text_color: tuple = (0, 255, 120),
    bg_color: tuple = (0, 0, 0),
) -> Image.Image:
    lines = ascii_text.split("\n")
    font = load_monospace_font(font_size)

    # Measure character cell size using a representative glyph
    bbox = font.getbbox("@")
    char_width = max(bbox[2] - bbox[0], 1)
    char_height = max(bbox[3] - bbox[1], 1) + 4  # + line spacing

    width = max(len(line) for line in lines) * char_width
    height = len(lines) * char_height

    img = Image.new("RGB", (width + 20, height + 20), bg_color)
    draw = ImageDraw.Draw(img)

    y = 10
    for line in lines:
        draw.text((10, y), line, fill=text_color, font=font)
        y += char_height

    return img


# --------------------------------------------------------------------------
# Module 5 & 6: Storage + Display (route handling)
# --------------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    ascii_art = None
    image_path = None
    ascii_image_path = None
    download_filename = None

    if request.method == "POST":
        file = request.files.get("image")

        if not file or file.filename == "":
            flash("Please choose an image file before uploading.", "warning")
            return redirect(url_for("index"))

        if not allowed_file(file.filename):
            flash("Unsupported file type. Please upload a JPG, PNG, BMP, or WEBP image.", "error")
            return redirect(url_for("index"))

        ensure_folders()

        # Use a unique, sanitized filename to avoid collisions/overwrites
        original_name = secure_filename(file.filename)
        unique_prefix = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
        saved_name = f"{unique_prefix}_{original_name}"
        upload_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_name)
        file.save(upload_path)

        # Read as grayscale directly (Image Processing Module)
        image = cv2.imread(upload_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            flash("Could not read that image. It may be corrupted or in an unsupported format.", "error")
            return redirect(url_for("index"))

        # ASCII Conversion Module
        ascii_art = convert_to_ascii(image)

        # Rendering Module
        ascii_img = ascii_to_image(ascii_art)
        ascii_filename = f"ascii_{unique_prefix}.png"
        ascii_save_path = os.path.join(app.config["ASCII_FOLDER"], ascii_filename)
        ascii_img.save(ascii_save_path)

        # Use forward-slash web paths so links work cross-platform
        image_path = url_for("static", filename=f"uploads/{saved_name}")
        ascii_image_path = url_for("static", filename=f"ascii_art/{ascii_filename}")
        download_filename = ascii_filename

    return render_template(
        "index.html",
        ascii_art=ascii_art,
        image_path=image_path,
        ascii_image_path=ascii_image_path,
        download_filename=download_filename,
    )


@app.errorhandler(413)
def file_too_large(_e):
    flash("That image is too large (max 10 MB). Please try a smaller file.", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    ensure_folders()
    port = int(os.environ.get("PORT", 5000))
    # host 0.0.0.0 binds to all network interfaces for LAN and cloud access
    app.run(host="0.0.0.0", port=port, debug=False)
