# ClipX

<div align="right">
  <a href="README.md">English</a> ·
  <a href="README.ru.md"><strong>Русский</strong></a>
</div>

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/Demo-GitHub%20Pages-blue.svg)](https://smetaha.github.io/ClipX/)

ClipX — локальный менеджер буфера обмена для текста, ссылок, файлов, изображений и OCR.

Проект помогает быстро собирать в одном месте всё, что обычно оказывается в буфере обмена, в папке с файлами или в заметках: текст, ссылки, код, изображения, скриншоты и документы.

## Почему ClipX

- локальный и приватный: данные хранятся на машине пользователя
- быстрый ввод: вставка текста, drag & drop, загрузка файлов и папок
- поиск и фильтрация по типу и статусу
- закрепление и избранное для важных записей
- OCR для распознавания текста на изображениях
- QR / LAN доступ к локальному интерфейсу
- импорт/экспорт для бэкапа и переноса данных

## Что умеет проект

- сохранять текст, ссылки и фрагменты кода
- хранить файлы, изображения и PDF
- помечать избранное и закреплять важные записи
- автоматически строить превью ссылок
- распознавать текст на картинках через OCR
- работать в стандартном и упрощённом режиме
- искать и фильтровать записи по типу и статусу
- экспортировать и импортировать резервные копии
- использовать локальный QR и LAN-доступ

## Скриншоты

> Здесь оставлены места под скриншоты — просто вставьте свои изображения в этот блок.

### Основной интерфейс

<div align="center">
  <img src="https://placehold.co/1400x800/0f172a/e2e8f0?text=ClipX+Основной+интерфейс" alt="ClipX main interface" width="1200" />
</div>

### Простая форма / быстрый ввод

<div align="center">
  <img src="https://placehold.co/1400x800/111827/a5b4fc?text=ClipX+Простой+режим" alt="ClipX simple mode" width="1200" />
</div>

### Поиск, фильтры и операции с выделением

<div align="center">
  <img src="https://placehold.co/1400x800/172033/f8fafc?text=Поиск+Фильтры+Групповые+действия" alt="ClipX filters and bulk actions" width="1200" />
</div>

## Технологии

- Python 3.11+
- Flask
- SQLite
- Pillow
- Tesseract OCR
- генерация QR-кодов

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

Открыть приложение в браузере:

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
├── .gitignore
└── .dockerignore
```

## Документация и ссылки

- [README.md](README.md)
- [README.en.md](README.en.md)
- [SECURITY.md](SECURITY.md)
- [SECURITY.ru.md](SECURITY.ru.md)
- [deployment/README.md](deployment/README.md)
- [deployment/README.ru.md](deployment/README.ru.md)
- [deployment/README.en.md](deployment/README.en.md)

## Развёртывание

В репозитории уже подготовлены шаблоны для:

- локального запуска через Docker
- развёртывания на VPS
- Render
- Railway

Подробнее: [deployment/README.ru.md](deployment/README.ru.md)

## GitHub Pages / демо

Интерфейс demo доступен здесь:

- [GitHub Pages](https://smetaha.github.io/ClipX/)

Файл `docs/index.html` используется как статический preview интерфейса и построен на основе реального UI проекта из `templates/` и `static/` без лишних выдуманных функций.

## Лицензия

Проект распространяется по лицензии MIT. См. [LICENSE](LICENSE).

## Безопасность

Пожалуйста, читайте [SECURITY.ru.md](SECURITY.ru.md) перед сообщением о возможной уязвимости.
