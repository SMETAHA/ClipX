# ClipX

ClipX is a local-first clipboard manager for text, links, files, images, and OCR-powered snippets.

## What the project does

- save text and URLs
- store files, screenshots, and PDFs
- pin important entries and mark favorites
- preview links automatically
- extract text from images via OCR
- work in both full and simplified mode
- export and import database backups
- connect over QR code and LAN
- search and filter saved items quickly

## Screenshots

### Main interface

<div align="center">
  <img src="https://placehold.co/1200x700/0f172a/e2e8f0?text=ClipX+main+interface" alt="ClipX main interface" width="1200" />
</div>

### Simple mode

<div align="center">
  <img src="https://placehold.co/1200x700/111827/a5b4fc?text=ClipX+simple+mode" alt="ClipX simple mode" width="1200" />
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

Open in the browser:

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

The repo includes templates for:

- local Docker deployment
- VPS / server deployment
- Render
- Railway

See [deployment/README.en.md](deployment/README.en.md).

## GitHub Pages

The `docs/index.html` preview is built from the real HTML/CSS sources in `templates/` and `static/`, without adding unrelated functionality.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).

## Security

See [SECURITY.md](SECURITY.md).
