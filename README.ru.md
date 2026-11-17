# ClipX

ClipX — локальный менеджер буфера обмена для текста, ссылок, файлов, изображений и OCR-скриптов.

## Что умеет проект

- сохранять текст и URL из буфера обмена
- хранить файлы, скриншоты и документы
- закреплять и отмечать избранное
- автоматически показывать превью ссылок
- распознавать текст на изображениях через OCR
- работать в обычном и упрощённом интерфейсе
- экспортировать и импортировать резервные копии
- открывать приложение по QR-коду или локальной сети

## Скриншоты

### Скриншот 1

<!-- Вставьте свой скриншот сюда -->
<div align="center">
  <img src="https://placehold.co/1200x700/0f172a/e2e8f0?text=%D0%A1%D0%BA%D1%80%D0%B8%D0%BD%D1%88%D0%BE%D1%82+1" alt="ClipX Screenshot 1" width="1200" />
</div>

### Скриншот 2

<!-- Вставьте свой скриншот сюда -->
<div align="center">
  <img src="https://placehold.co/1200x700/111827/a5b4fc?text=%D0%A1%D0%BA%D1%80%D0%B8%D0%BD%D1%88%D0%BE%D1%82+2" alt="ClipX Screenshot 2" width="1200" />
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

По умолчанию приложение доступно по адресу:

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

Подготовлены инструкции для:

- локального Docker-развёртывания
- VPS через gunicorn
- Render
- Railway

См. [deployment/README.md](deployment/README.md).

## Страницы и демо

Фронтенд-предпросмотр проекта находится в `docs/index.html` и используется для демонстрации пользовательского интерфейса проекта на GitHub Pages.

## Лицензия

Проект распространяется под лицензией MIT. См. [LICENSE](LICENSE).

## Безопасность

См. [SECURITY.md](SECURITY.md).
