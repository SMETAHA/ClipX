# ClipX

ClipX is a local-first clipboard manager for text, links, files, images, and OCR-powered snippets.

## What it does

- save text and URLs from the clipboard
- collect files, screenshots, and documents
- pin and favorite entries for quick access
- auto-preview links and metadata
- extract text from images using OCR
- work with both a full and a simplified interface
- export and import backup archives
- access the app via QR code or local network URL

## Screenshots

### Screenshot 1

<!-- Replace with your own screenshot -->
<div align="center">
  <img src="https://placehold.co/1200x700/0f172a/e2e8f0?text=Screenshot+1" alt="ClipX Screenshot 1" width="1200" />
</div>

### Screenshot 2

<!-- Replace with your own screenshot -->
<div align="center">
  <img src="https://placehold.co/1200x700/111827/a5b4fc?text=Screenshot+2" alt="ClipX Screenshot 2" width="1200" />
</div>

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For OCR on Linux:

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

Run:

```bash
python app.py
```

Default URL:

```text
http://localhost:5050
```

## Environment variables

```bash
CLIPX_PORT=5050 python app.py
CLIPX_PUBLIC_URL=http://192.168.1.25:5050 python app.py
CLIPX_HOST_IP=192.168.1.25 python app.py
```

## Deployment

The repo includes deployment templates for:

- Docker-based local deployment
- VPS with gunicorn
- Render
- Railway

See [deployment/README.md](deployment/README.md).

## Frontend demo

The current UI mockup is available in `docs/index.html` and is suitable for a GitHub Pages showcase of the project interface.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).

## Security

See [SECURITY.md](SECURITY.md).
