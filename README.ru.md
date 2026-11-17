# ClipX

ClipX — локальный менеджер буфера обмена для текста, ссылок, файлов, изображений и OCR.

## Что умеет проект

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

### Простой режим

<div align="center">
  <img src="https://placehold.co/1200x700/111827/a5b4fc?text=ClipX+simple+mode" alt="ClipX simple mode" width="1200" />
</div>

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Для OCR на Linux:

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

Запуск:

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

## Развёртывание

В репозитории есть шаблоны для:

- локального запуска через Docker
- VPS / server deployment
- Render
- Railway

Смотрите [deployment/README.ru.md](deployment/README.ru.md).

## GitHub Pages

В `docs/index.html` лежит preview интерфейса проекта, собранный по реальному HTML/CSS из `templates/` и `static/`, без лишних выдуманных функций.

## Лицензия

Проект распространяется по лицензии MIT. См. [LICENSE](LICENSE).

## Безопасность

См. [SECURITY.ru.md](SECURITY.ru.md).
