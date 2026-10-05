# AI-Based Image to ASCII Art Generator

An interactive web application that transforms images into high-resolution monospace ASCII art and styled retro matrix PNG graphics.

Built with Python, Flask, OpenCV, and Pillow (PIL).

---

## ✨ Features

- **Drag-and-Drop Web Interface**: Simple and intuitive UI to upload images (`PNG`, `JPG`, `JPEG`, `BMP`, `WEBP`).
- **Aspect-Ratio Preservation**: Compensates for monospace font vertical elongation factor (`0.55`) so artwork doesn't stretch.
- **Three-Panel Comparison**: View the original image, styled rendered PNG, and raw monospace ASCII text side-by-side.
- **1-Click Copy & Download**: Instant button to copy raw text to clipboard or download the high-res styled PNG.
- **Cloud-Ready**: Includes `Procfile`, `render.yaml`, and `Dockerfile` for zero-configuration deployment to Render, Railway, or Hugging Face.

---

## 🏗️ Architecture (6-Module Pipeline)

```
[User Image]
     │
     ▼
Module 1: Upload Module (Flask, secure file handling, 10MB limit)
     │
     ▼
Module 2: Image Processing (OpenCV grayscale + aspect-corrected resize)
     │
     ▼
Module 3: ASCII Conversion (Pixel intensity to 11-level character density mapping)
     │
     ├──────────────────────────┐
     ▼                          ▼
Module 4: Rendering (PIL)  [Raw ASCII Text]
     │                          │
     ▼                          │
Module 5: Storage (UUID & timestamped local storage)
     │                          │
     └──────────┬───────────────┘
                ▼
Module 6: Display (Responsive web dashboard)
```

---

## 🚀 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shivasai-008/ascii-art-generator.git
   cd ascii-art-generator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open in browser:**
   ```
   http://127.0.0.1:5000
   ```

---

## 🌐 Deploying to Render.com (24/7 Free Hosting)

1. Log into [Render.com](https://render.com).
2. Click **New +** > **Web Service**.
3. Connect your GitHub repository `shivasai-008/ascii-art-generator`.
4. Render will auto-detect settings from `render.yaml`:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click **Deploy Web Service** to get your free live public HTTPS URL!
