from flask import Flask, render_template_string, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TG Username Checker</title>
    <style>
        body { font-family: monospace; background: #111; color: #eee; display: flex; justify-content: center; padding-top: 100px; margin: 0; }
        .box { width: 90%; max-width: 500px; }
        input { width: 100%; padding: 12px; background: #222; border: 1px solid #444; color: #eee; font-size: 16px; box-sizing: border-box; border-radius: 6px; }
        button { margin-top: 10px; padding: 12px 24px; background: #2a6; border: none; color: #fff; cursor: pointer; font-size: 16px; border-radius: 6px; width: 100%; font-weight: bold; }
        button:hover { background: #3b7; }
        .result { margin-top: 20px; padding: 16px; border-left: 4px solid #444; background: #1a1a1a; border-radius: 4px; word-wrap: break-word; }
        .free { border-color: #2a6; }
        .taken { border-color: #c33; }
        .error { border-color: #f90; }
        .hint { color: #888; font-size: 12px; margin-top: 12px; text-align: center; }
    </style>
</head>
<body>
<div class="box">
    <h2>TG Username Checker</h2>
    <input id="u" placeholder="username (без @)" autofocus autocapitalize="none" autocomplete="off">
    <button onclick="check()">Проверить</button>
    <div id="out"></div>
    <div class="hint">Источник: fragment.com</div>
</div>
<script>
async function check() {
    const u = document.getElementById('u').value.trim().replace('@','');
    if (!u) return;
    document.getElementById('out').innerHTML = '<div class="result">проверяю...</div>';
    try {
        const r = await fetch('/check?u=' + encodeURIComponent(u));
        const d = await r.json();
        if (d.available === null) {
            document.getElementById('out').innerHTML = `<div class="result error"><b>@${u}</b> — ОШИБКА<br><small>${d.detail}</small></div>`;
            return;
        }
        const cls = d.available ? 'free' : 'taken';
        const txt = d.available ? 'СВОБОДЕН' : 'ЗАНЯТ';
        const extra = d.detail ? '<br><small>' + d.detail + '</small>' : '';
        document.getElementById('out').innerHTML = `<div class="result ${cls}"><b>@${u}</b> — ${txt}${extra}</div>`;
    } catch (e) {
        document.getElementById('out').innerHTML = `<div class="result error">Сеть недоступна</div>`;
    }
}
document.getElementById('u').addEventListener('keydown', e => { if (e.key === 'Enter') check(); });
</script>
</body>
</html>
"""

def check_fragment(username: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(f"https://fragment.com/username/{username}", headers=headers, timeout=10)
        text = r.text.lower()

        if "unavailable" in text:
            return {"available": False, "detail": "занят (fragment: unavailable)"}
        if "available" in text or "for sale" in text or "auction" in text:
            return {"available": True, "detail": "доступен на fragment"}
            
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.lower() if soup.title else ""
        if "not found" in title or "404" in title:
            return {"available": True, "detail": "не найден на fragment"}
        return {"available": False, "detail": f"неопределённо"}
    except Exception as e:
        return {"available": None, "detail": f"ошибка: {str(e)[:80]}"}

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/check")
def check():
    u = request.args.get("u", "").strip().lower()
    if not re.match(r"^[a-z][a-z0-9_]{3,30}[a-z0-9]$", u):
        return jsonify({"available": None, "detail": "невалидный формат"})
    result = check_fragment(u)
    return jsonify({"username": u, **result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
