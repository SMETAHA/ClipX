# ClipX

ClipX is a local-first clipboard manager for text, URLs, files, images, and OCR-powered snippets.

It helps you capture useful information quickly and keep it organized without depending on a cloud backend.

## Overview

- Save text and URLs from the clipboard
- Collect files, screenshots, and documents
- Pin favorite items and keep them visible
- Auto-preview web links and metadata
- OCR screenshots and images
- Use a simple and a full interface
- Export/import backup archives
- Share via QR or LAN URL on the local network

## Quick links

- [README in English](README.en.md)
- [README в русском](README.ru.md)
- [Security policy](SECURITY.md)
- [Production deployment guide](deployment/README.md)
- [GitHub Pages demo](https://smetaha.github.io/ClipX/)

## Screenshots

### Screenshot 1

<!-- Replace with your own screenshot -->
<div align="center">
  <img src="https://placehold.co/1200x700/0f172a/e2e8f0?text=Screenshot+1" alt="ClipX screenshot 1" width="1200" />
</div>

### Screenshot 2

<!-- Replace with your own screenshot -->
<div align="center">
  <img src="https://placehold.co/1200x700/111827/a5b4fc?text=Screenshot+2" alt="ClipX screenshot 2" width="1200" />
</div>

## Stack

- Python 3.11+
- Flask
- SQLite
- Pillow + Tesseract OCR
- QR code generation

## Local setup

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

## Production deployment

This repo includes deployment templates for:

- local Docker deployment
- VPS using gunicorn
- Render
- Railway

See [deployment/README.md](deployment/README.md) for setup instructions.

## GitHub Pages

The `docs/` folder contains a lightweight front-end preview based on the current project UI, useful for a visual landing page or demo.

## Project structure

```text
ClipX/
├── app.py
├── requirements.txt
├── README.md
├── README.ru.md
├── README.en.md
├── SECURITY.md
├── LICENSE
├── Procfile
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── railway.json
├── docs/
│   └── index.html
├── deployment/
│   └── README.md
├── static/
├── templates/
├── data/
├── .github/workflows/pages.yml
└── .gitignore
```

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).

## Security

Please review [SECURITY.md](SECURITY.md) before reporting vulnerabilities.
