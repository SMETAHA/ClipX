# ClipX

ClipX — локальный менеджер буфера обмена для текста, ссылок, файлов, изображений и OCR.

Это проект для быстрой упаковки полезной информации: заметки, ссылки, файлы, скриншоты, код и всё, что обычно держат в буфере обмена или в папке «временно пригодится».

## Что умеет

- сохранять текст и ссылки
- хранить файлы, картинки и PDF
- закреплять важные записи и помечать избранное
- автоматически показывать превью ссылок
- распознавать текст на изображениях через OCR
- работать в обычном и упрощённом режиме
- экспортировать и импортировать бэкап базы
- подключаться по QR-коду и LAN
- быстро искать и фильтровать записи

## Скриншоты

### Основной интерфейс

<div align="center">
  <img src="https://placehold.co/1200x700/0f172a/e2e8f0?text=ClipX+main+interface" alt="ClipX main interface" width="1200" />
</div>

### Простая форма / быстрый ввод

<div align="center">
  <img src="https://placehold.co/1200x700/111827/a5b4fc?text=ClipX+simple+mode" alt="ClipX simple mode" width="1200" />
</div>

## Стек

- Python 3.11+
- Flask
- SQLite
- Pillow + Tesseract OCR
- QR code generation

## Быстрый старт

### 1) Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) OCR для Linux

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

### 3) Запуск

```bash
python app.py
```

Открыть в браузере:

```text
http://localhost:5050
```

## Переменные окружения

```bash
CLIPX_PORT=5050 python app.py
CLIPX_PUBLIC_URL=http://192.168.1.25:5050 python app.py
CLIPX_HOST_IP=192.168.1.25 python app.py
```

## Структура проекта

```text
ClipX/
├── app.py
├── requirements.txt
├── README.md
├── README.ru.md
├── README.en.md
├── SECURITY.md
├── SECURITY.ru.md
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
│   ├── README.md
│   ├── README.ru.md
│   └── README.en.md
├── static/
├── templates/
├── data/
├── .github/workflows/pages.yml
└── .gitignore
```

## Документация

- [README в русском](README.ru.md)
- [README in English](README.en.md)
- [Security policy](SECURITY.md)
- [Политика безопасности (RU)](SECURITY.ru.md)
- [Deployment guide](deployment/README.md)
- [Руководство по деплою](deployment/README.ru.md)

## Развёртывание

В репозитории есть шаблоны для:

- локального запуска через Docker
- VPS / server deployment
- Render
- Railway

Смотрите: [deployment/README.md](deployment/README.md)

## GitHub Pages

В `docs/index.html` лежит preview интерфейса проекта, собранный по реальному HTML/CSS из `templates/` и `static/`, без лишних выдуманных функций.

## Лицензия

Проект распространяется по лицензии MIT. См. [LICENSE](LICENSE).

## Безопасность

Пожалуйста, читайте [SECURITY.md](SECURITY.md) перед сообщением о уязвимости.
