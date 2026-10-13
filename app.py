"""Barcode Studio - Flask + SQLite backend."""
import os, sqlite3, secrets, hmac
from datetime import datetime, timezone
from flask import Flask, g, jsonify, request, send_from_directory, Response

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("BARCODE_DB", os.path.join(BASE, "data", "barcodes.db"))
APP_USER = os.environ.get("APP_USER", "admin")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")   # empty = no login required
FORMATS = {"CODE128", "CODE39", "EAN13", "EAN8", "UPC", "ITF"}

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
app = Flask(__name__, static_folder=os.path.join(BASE, "static"), static_url_path="/static")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    conn = g.pop("db", None)
    if conn:
        conn.close()


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS barcodes(
            id TEXT PRIMARY KEY, value TEXT NOT NULL, format TEXT NOT NULL,
            label TEXT NOT NULL DEFAULT '', created TEXT NOT NULL)""")


@app.before_request
def require_auth():
    if not APP_PASSWORD or request.path == "/health":
        return
    a = request.authorization
    if a and hmac.compare_digest(a.username or "", APP_USER) and hmac.compare_digest(a.password or "", APP_PASSWORD):
        return
    return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="Barcode Studio"'})


@app.after_request
def headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"
    # camera must be allowed for this origin
    resp.headers["Permissions-Policy"] = "camera=(self)"
    return resp


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/barcodes")
def list_barcodes():
    rows = db().execute("SELECT * FROM barcodes ORDER BY created DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/barcodes")
def add_barcode():
    d = request.get_json(silent=True) or {}
    value = str(d.get("value", "")).strip()
    fmt = str(d.get("format", "CODE128"))
    label = str(d.get("label", "")).strip()[:100]
    if not value or len(value) > 200:
        return jsonify(error="value required (max 200 chars)"), 400
    if fmt not in FORMATS:
        return jsonify(error="unsupported format"), 400
    row = dict(id=secrets.token_hex(6), value=value, format=fmt, label=label,
               created=datetime.now(timezone.utc).isoformat())
    db().execute("INSERT INTO barcodes VALUES(:id,:value,:format,:label,:created)", row)
    db().commit()
    return jsonify(row), 201


@app.delete("/api/barcodes/<bid>")
def delete_barcode(bid):
    db().execute("DELETE FROM barcodes WHERE id=?", (bid,))
    db().commit()
    return jsonify(ok=True)


@app.delete("/api/barcodes")
def delete_all():
    db().execute("DELETE FROM barcodes")
    db().commit()
    return jsonify(ok=True)


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 8000)))
