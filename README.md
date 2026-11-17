# ClipX

ClipX is a local web app for managing clipboard snippets, links, and files.

## Features

- Save text and URLs
- Keep favorite and pinned entries
- Upload files and images
- Preview links automatically
- OCR on uploaded images
- Bulk actions for selected items
- Import/export database backups
- Optional QR-based access on the local network
- Simple mode for lightweight use

## Requirements

- Python 3.11+
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```

For OCR support on Linux:

```bash
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

## Run locally

```bash
python app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:5050
```

## Environment options

```bash
CLIPX_PUBLIC_URL=http://192.168.1.25:5050 python app.py
CLIPX_HOST_IP=192.168.1.25 python app.py
```

## Notes

This project is intended for local usage and works best as a personal clipboard utility with a browser-based dashboard.
