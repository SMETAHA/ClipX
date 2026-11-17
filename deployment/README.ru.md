# Руководство по деплою

Проект ClipX — локальный Flask-сервис, который можно разворачивать как на сервере, так и в контейнере.

## 1) Развёртывание на VPS

Подойдёт Ubuntu/Debian. Для запуска потребуются Python 3.11+ и gunicorn.

```bash
sudo apt update
sudo apt install python3-venv python3-pip nginx

cd /opt/clipx
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Для запуска в прод режиме:

```bash
gunicorn app:app --bind 0.0.0.0:5050 --workers 2 --timeout 120
```

Для Nginx можно настроить reverse proxy на `127.0.0.1:5050`.

## 2) Docker

```bash
docker build -t clipx .
docker run --rm -p 5050:5050 -v $(pwd)/data:/app/data clipx
```

Или через Compose:

```bash
docker compose up --build -d
```

## 3) Render

Используйте шаблон `render.yaml`.

1. Создайте новый Web Service в Render.
2. Подключите GitHub-репозиторий.
3. Выберите Python.
4. Render автоматически возьмёт параметры из шаблона.

## 4) Railway

Используйте шаблон `railway.json`.

1. Создайте проект в Railway.
2. Подключите репозиторий.
3. Railway запустит сервис по указанной команде.

## Переменные окружения

Рекомендуемые настройки:

```env
CLIPX_PORT=5050
CLIPX_SECRET=replace_with_secure_secret
CLIPX_MAX_MB=1024
```

## Проверка здоровья

Приложение отдаёт endpoint:

```text
GET /health
```

Проверка:

```bash
curl http://localhost:5050/health
```

## Важно

Проект хранит локальные данные в `data/` и лучше подходит для приватного или полу-приватного развёртывания, чем для публичного SaaS-сервиса.
