from __future__ import annotations

import atexit
import html
import json
import mimetypes
import io
import os
import shutil
import socket
import sqlite3
import tempfile
import uuid
import zipfile
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "clipx.db"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("CLIPX_SECRET", "clipx-dev-secret")
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("CLIPX_MAX_MB", "1024")) * 1024 * 1024


ITEM_COLUMNS: dict[str, str] = {
    "id": "TEXT PRIMARY KEY",
    "kind": "TEXT NOT NULL",
    "title": "TEXT",
    "text_content": "TEXT",
    "file_name": "TEXT",
    "stored_name": "TEXT",
    "mime": "TEXT",
    "size": "INTEGER",
    "favorite": "INTEGER NOT NULL DEFAULT 0",
    "pinned": "INTEGER NOT NULL DEFAULT 0",
    "link_url": "TEXT",
    "link_title": "TEXT",
    "link_description": "TEXT",
    "link_image": "TEXT",
    "ocr_text": "TEXT",
    "created_at": "TEXT NOT NULL",
}

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".html", ".htm", ".css", ".scss", ".json", ".xml", ".yaml", ".yml",
    ".csv", ".log", ".ini", ".toml", ".cfg", ".conf", ".sh", ".bat", ".ps1",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".java", ".kt", ".rs", ".go", ".lua",
    ".rb", ".php", ".sql", ".r", ".R", ".gd", ".shader", ".glsl",
}
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"}
PREVIEW_TEXT_LIMIT = 2 * 1024 * 1024

MDNS_SERVICE_TYPE = "_http._tcp.local."
MDNS_DEFAULT_NAME = "clipx"
_MDNS_ZEROCONF: Any | None = None
_MDNS_SERVICE_INFO: Any | None = None
_MDNS_STATUS: dict[str, Any] = {
    "enabled": False,
    "running": False,
    "hostname": "",
    "url": "",
    "ip": "",
    "error": "",
}


class LinkPreviewParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or "").lower()
            value = attrs_dict.get("content") or ""
            if key and value:
                self.meta[key] = html.unescape(value.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return html.unescape(" ".join(self.title_parts).strip())


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def short_id() -> str:
    return uuid.uuid4().hex[:10]


def get_db(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in rows)


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT,
                text_content TEXT,
                file_name TEXT,
                stored_name TEXT,
                mime TEXT,
                size INTEGER,
                favorite INTEGER NOT NULL DEFAULT 0,
                pinned INTEGER NOT NULL DEFAULT 0,
                link_url TEXT,
                link_title TEXT,
                link_description TEXT,
                link_image TEXT,
                ocr_text TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        for name, definition in ITEM_COLUMNS.items():
            if not column_exists(conn, "items", name):
                conn.execute(f"ALTER TABLE items ADD COLUMN {name} {definition}")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_items_kind ON items(kind)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_items_flags ON items(pinned, favorite)")


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def detect_text_kind(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith(("http://", "https://")) and "\n" not in stripped:
        return "link"
    return "text"


def make_title_from_text(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else "Untitled text"
    return first_line[:80]


def extract_first_url(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith(("http://", "https://")) and "\n" not in stripped:
        return stripped
    return ""


def display_filename(name: str) -> str:
    """Name shown to the user. Keep Unicode, strip only paths/control chars."""
    raw = (name or "").replace("\\", "/")
    cleaned = raw.rsplit("/", 1)[-1].replace("\x00", "").strip()
    return cleaned or f"file_{short_id()}"


def safe_extension(name: str) -> str:
    """ASCII-only extension for the local stored filename."""
    ext = Path(name).suffix[:32]
    ext = "".join(
        ch for ch in ext
        if ch.isascii() and (ch.isalnum() or ch in ".-_")
    )
    if ext in {"", ".", ".."}:
        return ""
    return ext if ext.startswith(".") else f".{ext}"


def stored_filename(item_id: str, original_name: str) -> str:
    """Name on disk. Never trust browser filenames for filesystem paths."""
    stem = Path(original_name).stem
    safe_stem = secure_filename(stem)[:80]
    ext = safe_extension(original_name)
    if safe_stem:
        return f"{item_id}_{safe_stem}{ext}"
    return f"{item_id}{ext or '.bin'}"


def safe_filename(name: str) -> str:
    """Generic ASCII filename for temporary/internal files."""
    cleaned = secure_filename((name or "").replace("\\", "/"))
    return cleaned or f"file_{short_id()}"


def fetch_link_preview(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {}

    try:
        req = Request(
            url,
            headers={
                "User-Agent": "ClipX/1.0 (+local link preview)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=5) as resp:
            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return {"link_url": url, "link_title": parsed.netloc}
            raw = resp.read(512 * 1024)
            charset = resp.headers.get_content_charset() or "utf-8"
    except Exception:
        return {"link_url": url, "link_title": parsed.netloc}

    try:
        text = raw.decode(charset, errors="replace")
    except Exception:
        text = raw.decode("utf-8", errors="replace")

    parser = LinkPreviewParser()
    try:
        parser.feed(text)
    except Exception:
        pass

    title = parser.meta.get("og:title") or parser.meta.get("twitter:title") or parser.title or parsed.netloc
    description = (
        parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
        or parser.meta.get("description")
        or ""
    )
    image = parser.meta.get("og:image") or parser.meta.get("twitter:image") or ""

    return {
        "link_url": url,
        "link_title": title[:220],
        "link_description": description[:500],
        "link_image": image[:1000],
    }


def run_ocr_if_possible(path: Path, mime: str) -> str:
    if not mime.startswith("image/"):
        return ""

    try:
        from PIL import Image  # type: ignore
        import pytesseract  # type: ignore
    except Exception:
        return ""

    try:
        langs = os.environ.get("CLIPX_OCR_LANG", "rus+eng")
        with Image.open(path) as img:
            text = pytesseract.image_to_string(img, lang=langs)
        return text.strip()
    except Exception:
        return ""


def insert_text_item(conn: sqlite3.Connection, content: str, title: str = "") -> str | None:
    content = content.strip()
    title = title.strip()
    if not content:
        return None

    item_id = short_id()
    kind = detect_text_kind(content)
    preview = fetch_link_preview(extract_first_url(content)) if kind == "link" else {}
    if not title:
        title = preview.get("link_title") or make_title_from_text(content)

    conn.execute(
        """
        INSERT INTO items (
            id, kind, title, text_content,
            link_url, link_title, link_description, link_image,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            kind,
            title,
            content,
            preview.get("link_url") or extract_first_url(content),
            preview.get("link_title") or None,
            preview.get("link_description") or None,
            preview.get("link_image") or None,
            now_iso(),
        ),
    )
    return item_id


def insert_file_item(conn: sqlite3.Connection, file: FileStorage, title: str = "") -> str | None:
    if not file.filename:
        return None

    original_name = display_filename(file.filename)
    item_id = short_id()
    stored_name = stored_filename(item_id, original_name)
    save_path = UPLOAD_DIR / stored_name
    file.save(save_path)

    guessed_mime = mimetypes.guess_type(original_name)[0]
    mime = guessed_mime or file.mimetype or "application/octet-stream"
    kind = "image" if mime.startswith("image/") else "file"
    size = save_path.stat().st_size
    ocr_text = run_ocr_if_possible(save_path, mime) if kind == "image" else ""

    conn.execute(
        """
        INSERT INTO items (
            id, kind, title, file_name, stored_name, mime, size, ocr_text, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            kind,
            title or original_name,
            original_name,
            stored_name,
            mime,
            size,
            ocr_text,
            now_iso(),
        ),
    )
    return item_id


def file_preview_kind(row: sqlite3.Row) -> str:
    mime = (row["mime"] or "").lower()
    name = (row["file_name"] or "").lower()
    suffix = Path(name).suffix

    if row["kind"] == "image" or mime.startswith("image/"):
        return "image"
    if mime == "application/pdf" or suffix == ".pdf":
        return "pdf"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    if mime.startswith("text/") or suffix in TEXT_EXTENSIONS or mime in {
        "application/json", "application/xml", "application/javascript",
        "application/x-javascript", "application/x-sh", "application/sql",
    }:
        return "text-file"
    if suffix in ARCHIVE_EXTENSIONS:
        return "archive"
    return "unknown"


def read_text_file_preview(row: sqlite3.Row) -> dict[str, Any]:
    if not row["stored_name"]:
        return {"ok": False, "text": "", "truncated": False, "error": "Файл не найден."}

    path = UPLOAD_DIR / row["stored_name"]
    if not path.exists():
        return {"ok": False, "text": "", "truncated": False, "error": "Файл не найден на диске."}

    try:
        raw = path.read_bytes()[: PREVIEW_TEXT_LIMIT + 1]
        truncated = len(raw) > PREVIEW_TEXT_LIMIT
        raw = raw[:PREVIEW_TEXT_LIMIT]
    except Exception:
        return {"ok": False, "text": "", "truncated": False, "error": "Не смог прочитать файл."}

    for encoding in ("utf-8", "cp1251", "latin-1"):
        try:
            return {
                "ok": True,
                "text": raw.decode(encoding, errors="strict"),
                "truncated": truncated,
                "encoding": encoding,
                "error": "",
            }
        except UnicodeDecodeError:
            continue

    return {
        "ok": True,
        "text": raw.decode("utf-8", errors="replace"),
        "truncated": truncated,
        "encoding": "utf-8/replace",
        "error": "",
    }


def read_archive_preview(row: sqlite3.Row) -> dict[str, Any]:
    if not row["stored_name"]:
        return {"ok": False, "files": [], "truncated": False, "error": "Архив не найден."}
    path = UPLOAD_DIR / row["stored_name"]
    suffix = Path(row["file_name"] or "").suffix.lower()
    if suffix != ".zip":
        return {"ok": False, "files": [], "truncated": False, "error": "Список файлов показываю только для ZIP."}
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
        return {"ok": True, "files": names[:200], "truncated": len(names) > 200, "error": ""}
    except Exception:
        return {"ok": False, "files": [], "truncated": False, "error": "Не смог прочитать ZIP."}


@app.template_filter("filesize")
def filesize(value: int | None) -> str:
    if value is None:
        return ""
    size = float(value)
    units = ["B", "KB", "MB", "GB"]
    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@app.template_filter("truncate_text")
def truncate_text(value: str | None, length: int = 220) -> str:
    if not value:
        return ""
    value = value.strip()
    if len(value) <= length:
        return value
    return value[:length] + "…"


app.jinja_env.globals["file_preview_kind"] = file_preview_kind


def redirect_target(default_endpoint: str = "index", **values: Any) -> str:
    next_url = request.form.get("next", "").strip() or request.args.get("next", "").strip()
    if next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return request.referrer or url_for(default_endpoint, **values)



def env_truthy(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() not in {"0", "false", "no", "off", "нет"}


def mdns_label(value: str | None = None) -> str:
    """Safe ASCII label for <name>.local."""
    raw = (value or os.environ.get("CLIPX_MDNS_NAME") or MDNS_DEFAULT_NAME).strip().lower()
    chars: list[str] = []
    for ch in raw:
        if ch.isascii() and (ch.isalnum() or ch == "-"):
            chars.append(ch)
        elif ch in {"_", " ", "."}:
            chars.append("-")
    label = "".join(chars).strip("-")[:63]
    return label or MDNS_DEFAULT_NAME


def mdns_hostname() -> str:
    return f"{mdns_label()}.local"


def detect_lan_ip() -> str:
    """Best-effort LAN IP detection that is safe outside request context."""
    forced = os.environ.get("CLIPX_HOST_IP", "").strip()
    if forced:
        return forced

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # UDP connect does not need the address to be reachable; it only picks an outbound interface.
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except Exception:
        pass

    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    return "127.0.0.1"


def guess_lan_ip() -> str:
    """Best-effort LAN IP detection for phone/second-device connection."""
    ip = detect_lan_ip()
    if ip and not ip.startswith("127."):
        return ip
    try:
        return request.host.split(":", 1)[0]
    except RuntimeError:
        return ip


def mdns_connection_url(path: str = "", port: int | str | None = None, scheme: str = "http") -> str:
    clean_path = "/" + path.lstrip("/") if path else ""
    use_port = str(port or os.environ.get("CLIPX_PORT", "5050"))
    return f"{scheme}://{mdns_hostname()}:{use_port}{clean_path}"


def mdns_status() -> dict[str, Any]:
    return dict(_MDNS_STATUS)


def start_mdns(port: int) -> None:
    """Advertise ClipX as http://clipx.local:port via mDNS/Bonjour/Avahi.

    Optional dependency: pip install zeroconf
    Disable with: CLIPX_MDNS=0
    Rename with: CLIPX_MDNS_NAME=myclipx
    """
    global _MDNS_ZEROCONF, _MDNS_SERVICE_INFO

    label = mdns_label()
    hostname = f"{label}.local."
    ip = detect_lan_ip()
    _MDNS_STATUS.update({
        "enabled": env_truthy("CLIPX_MDNS", "1"),
        "running": False,
        "hostname": hostname.rstrip("."),
        "url": mdns_connection_url("/", port=port),
        "ip": ip,
        "error": "",
    })

    if not _MDNS_STATUS["enabled"]:
        _MDNS_STATUS["error"] = "disabled by CLIPX_MDNS=0"
        return

    if ip.startswith("127."):
        _MDNS_STATUS["error"] = "LAN IP not detected"
        print("[ClipX] mDNS disabled: LAN IP not detected")
        return

    try:
        from zeroconf import ServiceInfo, Zeroconf  # type: ignore
    except Exception as exc:
        _MDNS_STATUS["error"] = f"zeroconf not installed: {exc.__class__.__name__}"
        print("[ClipX] mDNS unavailable. Install it with: pip install zeroconf")
        return

    try:
        service_name = f"ClipX ({label}).{MDNS_SERVICE_TYPE}"
        _MDNS_SERVICE_INFO = ServiceInfo(
            MDNS_SERVICE_TYPE,
            service_name,
            addresses=[socket.inet_aton(ip)],
            port=port,
            properties={
                "path": "/",
                "name": "ClipX",
                "url": mdns_connection_url("/", port=port),
            },
            server=hostname,
        )
        _MDNS_ZEROCONF = Zeroconf()
        _MDNS_ZEROCONF.register_service(_MDNS_SERVICE_INFO)
        _MDNS_STATUS.update({"running": True, "error": ""})
        print(f"[ClipX] mDNS: {mdns_connection_url('/', port=port)} -> {ip}:{port}")
    except Exception as exc:
        _MDNS_STATUS["error"] = f"mDNS register failed: {exc.__class__.__name__}: {exc}"
        print(f"[ClipX] mDNS register failed: {exc}")


def stop_mdns() -> None:
    global _MDNS_ZEROCONF, _MDNS_SERVICE_INFO
    if _MDNS_ZEROCONF and _MDNS_SERVICE_INFO:
        try:
            _MDNS_ZEROCONF.unregister_service(_MDNS_SERVICE_INFO)
        except Exception:
            pass
        try:
            _MDNS_ZEROCONF.close()
        except Exception:
            pass
    _MDNS_ZEROCONF = None
    _MDNS_SERVICE_INFO = None
    _MDNS_STATUS["running"] = False


atexit.register(stop_mdns)


def connection_url(path: str = "") -> str:
    """URL that should work from another device in the same LAN."""
    public = os.environ.get("CLIPX_PUBLIC_URL", "").strip().rstrip("/")
    clean_path = "/" + path.lstrip("/") if path else ""
    if public:
        return public + clean_path

    host = request.host.split(":", 1)[0]
    port = request.host.split(":", 1)[1] if ":" in request.host else os.environ.get("CLIPX_PORT", "5050")

    local_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if (
        host in local_hosts
        and env_truthy("CLIPX_USE_MDNS_URL", "1")
        and _MDNS_STATUS.get("running")
    ):
        return mdns_connection_url(clean_path, port=port, scheme=request.scheme)

    if host in local_hosts:
        host = guess_lan_ip()
    return f"{request.scheme}://{host}:{port}{clean_path}"


def qrcode_available() -> bool:
    try:
        import qrcode  # noqa: F401
        import qrcode.image.svg  # noqa: F401
        return True
    except Exception:
        return False


def qr_fallback_svg(url: str, reason: str = "QR module missing") -> str:
    safe_url = html.escape(url, quote=True)
    safe_reason = html.escape(reason[:80], quote=True)
    short_url = html.escape(url[:42] + ("…" if len(url) > 42 else ""), quote=True)
    return f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"220\" height=\"220\" viewBox=\"0 0 220 220\" role=\"img\" aria-label=\"{safe_url}\">
  <rect width=\"220\" height=\"220\" rx=\"22\" fill=\"#ffffff\"/>
  <rect x=\"18\" y=\"18\" width=\"52\" height=\"52\" rx=\"6\" fill=\"#111827\"/>
  <rect x=\"150\" y=\"18\" width=\"52\" height=\"52\" rx=\"6\" fill=\"#111827\"/>
  <rect x=\"18\" y=\"150\" width=\"52\" height=\"52\" rx=\"6\" fill=\"#111827\"/>
  <rect x=\"32\" y=\"32\" width=\"24\" height=\"24\" rx=\"4\" fill=\"#ffffff\"/>
  <rect x=\"164\" y=\"32\" width=\"24\" height=\"24\" rx=\"4\" fill=\"#ffffff\"/>
  <rect x=\"32\" y=\"164\" width=\"24\" height=\"24\" rx=\"4\" fill=\"#ffffff\"/>
  <text x=\"110\" y=\"106\" text-anchor=\"middle\" font-family=\"system-ui, sans-serif\" font-size=\"28\" font-weight=\"800\" fill=\"#2563eb\">QR</text>
  <text x=\"110\" y=\"130\" text-anchor=\"middle\" font-family=\"system-ui, sans-serif\" font-size=\"10\" fill=\"#374151\">{safe_reason}</text>
  <text x=\"110\" y=\"148\" text-anchor=\"middle\" font-family=\"monospace\" font-size=\"8\" fill=\"#111827\">{short_url}</text>
  <text x=\"110\" y=\"174\" text-anchor=\"middle\" font-family=\"system-ui, sans-serif\" font-size=\"9\" fill=\"#6b7280\">pip install -r requirements.txt</text>
</svg>"""


@app.route("/connect.svg")
def connect_qr():
    raw_path = request.args.get("path", "/").strip() or "/"
    if not raw_path.startswith("/") or raw_path.startswith("//"):
        raw_path = "/"
    url = connection_url(raw_path)
    try:
        import qrcode
        import qrcode.image.svg

        image = qrcode.make(
            url,
            image_factory=qrcode.image.svg.SvgPathImage,
            box_size=10,
            border=2,
        )
        stream = io.BytesIO()
        image.save(stream)
        payload = stream.getvalue()
        if not payload.lstrip().startswith((b"<?xml", b"<svg")):
            raise RuntimeError("qrcode returned non-svg payload")
        return app.response_class(
            payload,
            mimetype="image/svg+xml",
            headers={"Cache-Control": "no-store, max-age=0"},
        )
    except Exception as exc:
        # Important: never return plain text into <img>, otherwise browser shows a broken image icon.
        return app.response_class(
            qr_fallback_svg(url, f"QR unavailable: {exc.__class__.__name__}"),
            mimetype="image/svg+xml",
            headers={"Cache-Control": "no-store, max-age=0", "X-ClipX-QR-Fallback": "1"},
        )


@app.route("/connect.json")
def connect_json():
    """Small machine-readable connection info for NFC/QR/helpers."""
    return {
        "name": "ClipX",
        "url": connection_url("/"),
        "simple_url": connection_url("/simple"),
        "nfc_url": connection_url("/nfc"),
        "lan_ip": guess_lan_ip(),
        "mdns": mdns_status(),
        "qrcode_available": qrcode_available(),
    }


@app.route("/nfc")
def nfc_entry():
    """NFC-friendly entry point: open the lightweight ClipX view."""
    return redirect(url_for("simple"))



app.jinja_env.globals["connection_url"] = connection_url
app.jinja_env.globals["qrcode_available"] = qrcode_available
app.jinja_env.globals["mdns_status"] = mdns_status

init_db()


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    kind_filter = request.args.get("kind", "").strip()
    flag_filter = request.args.get("flag", "").strip()

    sql = "SELECT * FROM items"
    params: list[Any] = []
    clauses: list[str] = []

    if query:
        clauses.append(
            """
            (
                title LIKE ? OR text_content LIKE ? OR file_name LIKE ? OR
                link_title LIKE ? OR link_description LIKE ? OR ocr_text LIKE ?
            )
            """
        )
        like = f"%{query}%"
        params.extend([like, like, like, like, like, like])

    if kind_filter:
        clauses.append("kind = ?")
        params.append(kind_filter)

    if flag_filter == "pinned":
        clauses.append("pinned = 1")
    elif flag_filter == "favorite":
        clauses.append("favorite = 1")
    elif flag_filter == "ocr":
        clauses.append("ocr_text IS NOT NULL AND ocr_text != ''")

    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    sql += " ORDER BY pinned DESC, favorite DESC, created_at DESC LIMIT 300"

    with get_db() as conn:
        items = conn.execute(sql, params).fetchall()
        total = conn.execute("SELECT COUNT(*) AS c FROM items").fetchone()["c"]

    return render_template(
        "index.html",
        items=items,
        query=query,
        kind_filter=kind_filter,
        flag_filter=flag_filter,
        total=total,
    )


@app.route("/simple")
def simple():
    query = request.args.get("q", "").strip()
    sql = "SELECT * FROM items"
    params: list[Any] = []
    if query:
        like = f"%{query}%"
        sql += " WHERE title LIKE ? OR text_content LIKE ? OR file_name LIKE ? OR link_title LIKE ? OR link_description LIKE ? OR ocr_text LIKE ?"
        params.extend([like, like, like, like, like, like])
    sql += " ORDER BY pinned DESC, favorite DESC, created_at DESC LIMIT 300"

    with get_db() as conn:
        items = conn.execute(sql, params).fetchall()
        total = conn.execute("SELECT COUNT(*) AS c FROM items").fetchone()["c"]

    return render_template("simple.html", items=items, query=query, total=total)


@app.route("/add-text", methods=["POST"])
def add_text():
    content = request.form.get("content", "").strip()
    title = request.form.get("title", "").strip()
    next_url = redirect_target("index")

    if not content:
        flash("Пустой текст не сохраняю.")
        return redirect(next_url)

    with get_db() as conn:
        insert_text_item(conn, content, title=title)

    return redirect(next_url)


@app.route("/quick-add", methods=["POST"])
def quick_add():
    content = request.form.get("content", "").strip()
    title = request.form.get("title", "").strip()
    files = request.files.getlist("file")
    next_url = redirect_target("simple")

    created_text = 0
    created_files = 0

    with get_db() as conn:
        if content:
            if insert_text_item(conn, content, title=title):
                created_text += 1
        for file in files:
            if file and file.filename and insert_file_item(conn, file, title=title if len(files) == 1 and not content else ""):
                created_files += 1

    if not created_text and not created_files:
        flash("Нечего сохранять: вставь текст или кинь файл.")
    else:
        parts = []
        if created_text:
            parts.append(f"текст: {created_text}")
        if created_files:
            parts.append(f"файлы: {created_files}")
        flash("Сохранено — " + ", ".join(parts) + ".")

    return redirect(next_url)


@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("file")
    next_url = redirect_target("index")

    if not files or all(not f.filename for f in files):
        flash("Файл не выбран.")
        return redirect(next_url)

    title = request.form.get("title", "").strip()
    created = 0
    with get_db() as conn:
        for file in files:
            if insert_file_item(conn, file, title=title if len(files) == 1 else ""):
                created += 1

    return redirect(next_url)


@app.route("/i/<item_id>")
def item(item_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    if not row:
        abort(404)

    preview = {"kind": "none", "text": "", "truncated": False, "encoding": "", "error": ""}
    if row["kind"] not in ("text", "link"):
        preview_kind = file_preview_kind(row)
        preview["kind"] = preview_kind
        if preview_kind == "text-file":
            text_preview = read_text_file_preview(row)
            preview.update(text_preview)
        elif preview_kind == "archive":
            archive_preview = read_archive_preview(row)
            preview.update(archive_preview)

    return render_template("item.html", item=row, preview=preview)


@app.route("/raw/<item_id>")
def raw_item(item_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    if not row:
        abort(404)

    if row["kind"] in ("text", "link"):
        return app.response_class(
            row["text_content"] or "",
            mimetype="text/plain; charset=utf-8",
        )

    if not row["stored_name"]:
        abort(404)

    return send_from_directory(
        UPLOAD_DIR,
        row["stored_name"],
        mimetype=row["mime"] or None,
        as_attachment=False,
        download_name=row["file_name"],
        conditional=True,
    )


@app.route("/download/<item_id>")
def download(item_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    if not row:
        abort(404)

    if row["kind"] in ("text", "link"):
        text = row["text_content"] or ""
        tmp_path = DATA_DIR / f"{row['id']}.txt"
        tmp_path.write_text(text, encoding="utf-8")
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=f"{row['title'] or row['id']}.txt",
            mimetype="text/plain",
        )

    if not row["stored_name"]:
        abort(404)

    return send_from_directory(
        UPLOAD_DIR,
        row["stored_name"],
        as_attachment=True,
        download_name=row["file_name"],
    )


@app.route("/favorite/<item_id>", methods=["POST"])
def favorite(item_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT favorite FROM items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            abort(404)
        new_value = 0 if row["favorite"] else 1
        conn.execute("UPDATE items SET favorite = ? WHERE id = ?", (new_value, item_id))

    return redirect(redirect_target("index"))


@app.route("/pin/<item_id>", methods=["POST"])
def pin(item_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT pinned FROM items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            abort(404)
        new_value = 0 if row["pinned"] else 1
        conn.execute("UPDATE items SET pinned = ? WHERE id = ?", (new_value, item_id))

    return redirect(redirect_target("index"))


def delete_item(conn: sqlite3.Connection, item_id: str) -> None:
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        return

    if row["stored_name"]:
        path = UPLOAD_DIR / row["stored_name"]
        if path.exists():
            path.unlink()

    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))


@app.route("/delete/<item_id>", methods=["POST"])
def delete(item_id: str):
    with get_db() as conn:
        delete_item(conn, item_id)
    return redirect(redirect_target("index"))


@app.route("/bulk", methods=["POST"])
@app.route("/bulk/", methods=["POST"])
@app.route("/bulk-action", methods=["POST"])
def bulk():
    action = request.form.get("action", "").strip()
    ids = request.form.getlist("item_ids")

    if not ids:
        flash("Ничего не выбрано.")
        return redirect(redirect_target("index"))

    if action == "export":
        return export_items(ids)

    with get_db() as conn:
        placeholders = ",".join("?" for _ in ids)
        if action == "delete":
            for item_id in ids:
                delete_item(conn, item_id)
        elif action == "favorite":
            conn.execute(f"UPDATE items SET favorite = 1 WHERE id IN ({placeholders})", ids)
        elif action == "unfavorite":
            conn.execute(f"UPDATE items SET favorite = 0 WHERE id IN ({placeholders})", ids)
        elif action == "pin":
            conn.execute(f"UPDATE items SET pinned = 1 WHERE id IN ({placeholders})", ids)
        elif action == "unpin":
            conn.execute(f"UPDATE items SET pinned = 0 WHERE id IN ({placeholders})", ids)
        else:
            flash("Неизвестное массовое действие.")

    return redirect(redirect_target("index"))


def export_items(ids: list[str] | None = None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = EXPORT_DIR / f"clipx_backup_{timestamp}.zip"

    with get_db() as conn:
        if ids:
            placeholders = ",".join("?" for _ in ids)
            rows = conn.execute(f"SELECT * FROM items WHERE id IN ({placeholders})", ids).fetchall()
        else:
            rows = conn.execute("SELECT * FROM items ORDER BY created_at DESC").fetchall()

    items = [row_to_dict(row) for row in rows]
    manifest = {
        "app": "ClipX",
        "version": 3,
        "exported_at": now_iso(),
        "items": items,
    }

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for item_data in items:
            stored_name = item_data.get("stored_name")
            if stored_name:
                src = UPLOAD_DIR / stored_name
                if src.exists():
                    zf.write(src, f"uploads/{stored_name}")

    return send_file(out_path, as_attachment=True, download_name=out_path.name)


@app.route("/export")
def export_all():
    return export_items()


def safe_extract_zip(zf: zipfile.ZipFile, target_dir: Path) -> None:
    target_root = target_dir.resolve()
    for member in zf.infolist():
        member_path = (target_root / member.filename).resolve()
        if target_root != member_path and target_root not in member_path.parents:
            raise ValueError("Unsafe path inside ZIP")
        zf.extract(member, target_root)


def normalize_import_item(item_data: dict[str, Any]) -> dict[str, Any]:
    return {key: item_data.get(key) for key in ITEM_COLUMNS.keys()}


@app.route("/import", methods=["POST"])
def import_backup():
    file = request.files.get("backup")
    if not file or not file.filename:
        flash("Бэкап не выбран.")
        return redirect(redirect_target("index"))

    imported = 0
    skipped = 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        backup_path = tmp_dir / safe_filename(file.filename)
        file.save(backup_path)

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                safe_extract_zip(zf, tmp_dir / "backup")
        except Exception:
            flash("Не смог прочитать ZIP-бэкап.")
            return redirect(redirect_target("index"))

        manifest_path = tmp_dir / "backup" / "manifest.json"
        if not manifest_path.exists():
            flash("В бэкапе нет manifest.json.")
            return redirect(redirect_target("index"))

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        items = manifest.get("items", [])

        with get_db() as conn:
            existing = {row["id"] for row in conn.execute("SELECT id FROM items").fetchall()}
            for raw_item_data in items:
                item_data = normalize_import_item(raw_item_data)
                item_id = item_data.get("id") or short_id()
                if item_id in existing:
                    skipped += 1
                    continue
                item_data["id"] = item_id
                item_data["created_at"] = item_data.get("created_at") or now_iso()
                item_data["favorite"] = int(item_data.get("favorite") or 0)
                item_data["pinned"] = int(item_data.get("pinned") or 0)

                stored_name = item_data.get("stored_name")
                if stored_name:
                    src = tmp_dir / "backup" / "uploads" / stored_name
                    dst = UPLOAD_DIR / stored_name
                    if src.exists() and not dst.exists():
                        shutil.copy2(src, dst)

                columns = list(ITEM_COLUMNS.keys())
                placeholders = ",".join("?" for _ in columns)
                conn.execute(
                    f"INSERT INTO items ({','.join(columns)}) VALUES ({placeholders})",
                    [item_data.get(col) for col in columns],
                )
                existing.add(item_id)
                imported += 1

    flash(f"Импортировано: {imported}. Пропущено дублей: {skipped}.")
    return redirect(redirect_target("index"))


@app.route("/reocr/<item_id>", methods=["POST"])
def reocr(item_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
        if not row:
            abort(404)
        if file_preview_kind(row) != "image" or not row["stored_name"]:
            flash("OCR есть смысл запускать только для картинок.")
            return redirect(redirect_target("index"))

        path = UPLOAD_DIR / row["stored_name"]
        text = run_ocr_if_possible(path, row["mime"] or "image/*")
        conn.execute("UPDATE items SET ocr_text = ? WHERE id = ?", (text, item_id))
        flash("OCR обновлён." if text else "OCR ничего не нашёл или tesseract не установлен.")

    return redirect(redirect_target("item", item_id=item_id))


@app.route("/health")
def health():
    return {
        "status": "ok",
        "name": "ClipX",
        "qrcode_available": qrcode_available(),
        "connection_url": connection_url("/"),
        "simple_url": connection_url("/simple"),
        "nfc_url": connection_url("/nfc"),
        "mdns": mdns_status(),
    }


if __name__ == "__main__":
    port = int(os.environ.get("CLIPX_PORT", "5050"))
    start_mdns(port)
    app.run(host="0.0.0.0", port=port, debug=False)
