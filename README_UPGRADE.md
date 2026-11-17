# ClipX full preserved + QR + no reload

Эта сборка сделана как **полная версия**, а не урезанная ветка.

Сохранено из `clipx_upgrade_full.zip`:

- Drag & Drop файлов
- горячие клавиши: Ctrl+K, /, Ctrl+U, Ctrl+Enter
- автоматические preview ссылок
- закреплённые записи Pin
- избранное Star
- массовые операции
- экспорт / импорт базы
- OCR картинок
- тупой режим `/simple`

Добавлено сверху:

- почти все действия без полной перезагрузки страницы
- QR-код подключения на главной
- QR-код подключения в тупом режиме
- показ LAN-ссылки при наведении на QR
- Copy URL рядом с QR
- drop/paste текста и ссылок как quick-add
- выбор папок и файлов в обычном и тупом режиме

## Установка

```bash
pip install -r requirements.txt
```

Для OCR:

```bash
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
```

## Запуск

```bash
python app.py
```

Если QR показывает не тот адрес:

```bash
CLIPX_PUBLIC_URL=http://192.168.1.25:5050 python app.py
```

или:

```bash
CLIPX_HOST_IP=192.168.1.25 python app.py
```

## Фикс QR / bulk-panel

В этой версии `/connect.svg` больше не отдаёт plain text в `<img>`, поэтому вместо битой картинки будет либо настоящий QR, либо SVG-заглушка с URL и подсказкой установки зависимости.

Проверить состояние можно так:

```bash
curl http://localhost:5050/health
```

Если в ответе `"qrcode_available": false`, поставь зависимости ещё раз:

```bash
pip install -r requirements.txt
```

Массовая кнопка теперь показывает счётчик выбранных элементов и активируется только после выбора карточек.
