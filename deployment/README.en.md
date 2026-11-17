# Production deployment guide

ClipX is a local-first Flask application. It can be deployed on a VPS, in Docker, or on managed hosting providers such as Render or Railway.

## 1) VPS / server deployment

Use a Linux VM or server with Python 3.11+.

```bash
sudo apt update
sudo apt install python3-venv python3-pip nginx

cd /opt/clipx
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run in production mode:

```bash
gunicorn app:app --bind 0.0.0.0:5050 --workers 2 --timeout 120
```

If you use Nginx, point the upstream to `127.0.0.1:5050`.

## 2) Docker deployment

```bash
docker build -t clipx .
docker run --rm -p 5050:5050 -v $(pwd)/data:/app/data clipx
```

Or with Docker Compose:

```bash
docker compose up --build -d
```

## 3) Render deployment

Use the included `render.yaml` template.

1. Create a new Web Service on Render.
2. Connect the repository.
3. Choose the Python environment.
4. Render will use the included template values automatically.

## 4) Railway deployment

Use the included `railway.json` template.

1. Create a new project on Railway.
2. Connect the repository.
3. Railway will run the app using the provided start command.

## Runtime environment

Recommended values:

```env
CLIPX_PORT=5050
CLIPX_SECRET=replace_with_secure_secret
CLIPX_MAX_MB=1024
```

## Health check

The app exposes:

```text
GET /health
```

Example:

```bash
curl http://localhost:5050/health
```

## Notes

This project stores local data in `data/` and is best suited for private or semi-private deployments, not a public multi-user SaaS backend.
