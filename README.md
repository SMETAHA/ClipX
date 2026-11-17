# ClipX

ClipX is a local-first web app for collecting, organizing, and reusing text, links, and files from a personal clipboard workflow.

It is designed for quick capture, simple browsing, and local networking use on a home or office machine — without depending on a cloud backend.

## Highlights

- Save snippets of text and URLs
- Store and reopen files and images
- Mark items as pinned or favorite
- Preview web links automatically
- Run OCR on uploaded images
- Use bulk actions for selection-heavy workflows
- Import and export database backups
- Access the app over the local network via QR code
- Switch to a lightweight `/simple` interface

## Tech stack

- Python 3.11+
- Flask
- SQLite for local storage
- Pillow + Tesseract for OCR support
- QR code generation for easy access

## Quick start

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Install OCR dependencies on Linux

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

### 3) Run the app

```bash
python app.py
```

The app starts on port 5050 by default:

```text
http://localhost:5050
```

## Environment variables

```bash
CLIPX_PORT=5050 python app.py
CLIPX_PUBLIC_URL=http://192.168.1.25:5050 python app.py
CLIPX_HOST_IP=192.168.1.25 python app.py
```

## Docker

A production-style container setup is included for local deployment:

```bash
docker build -t clipx .
docker run --rm -p 5050:5050 -v $(pwd)/data:/app/data clipx
```

You can also use Docker Compose:

```bash
docker compose up --build
```

## GitHub Pages demo

This repository includes a lightweight static landing page under `docs/` for GitHub Pages.

The demo URL is:

```text
https://<your-user>.github.io/ClipX/
```

## Project structure

```text
ClipX/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── Dockerfile
├── docker-compose.yml
├── docs/
│   └── index.html
├── static/
├── templates/
├── data/
└── .github/workflows/pages.yml
```

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.

## Notes

ClipX is intended as a personal, local workflow tool. It is best suited for environments where you want a private clipboard manager with a browser UI and a local network-friendly setup.
