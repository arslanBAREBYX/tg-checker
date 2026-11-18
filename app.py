from flask import Flask, render_template_string, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import random
import itertools

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TG Auto Checker</title>
    <style>
        body { font-family: monospace; background: #111; color: #eee; display: flex; justify-content: center; padding-top: 50px; margin: 0; }
        .box { width: 95%; max-width: 600px; }
        input { width: 100%; padding: 12px; background: #222; border: 1px solid #444; color: #eee; font-size: 16px; box-sizing: border-box; border-radius: 6px; }
        button { margin-top: 10px; padding: 12px 24px; background: #2a6; border: none; color: #fff; cursor: pointer; font-size: 16px; border-radius: 6px; width: 100%; font-weight: bold; }
        button:hover { background: #3b7; }
        .result { margin-top: 20px; padding: 16px; border-left: 4px solid #444; background: #1a1a1a; border-radius: 4px; word-wrap: break-word; }
        .free { border-color: #2a6; }
        .error { border-color: #f90; }
        .hint { color: #888; font-size: 12px; margin-top: 12px; text-align: center; }
        .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(255,255,255,.3); border-radius: 50%; border-top-color: #fff; animation: spin 1s ease-in-out infinite; margin-bottom: 10px; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
<div class="box">
    <h2>Поиск свободных красивых юзернеймов</h2>
    <input id="base" placeholder="базовое слово (например, Wolf или оставь пустым)" autocapitalize="none" autocomplete="off">
    <button onclick="search()">Искать</button>
    <div id="out"></div>
</div>
<script>
async function search() {
    const base = document.getElementById('base').value.trim();
    const out = document.getElementById('out');
    out.innerHTML = '<div class="result"><div class="spinner"></div> Ищу свободные варианты, это займет время...</div>';
    
    try {
        const r = await fetch('/search?base=' + encodeURIComponent(base));
        const d = await r.json();
        
        if (d.error) {
            out.innerHTML = `<div class="result error">Ошибка: ${d.error}</div>`;
            return;
        }
        
        let html = '<div class="result free"><b>Найдено свободных:</b><br><br>';
        if (d.free.length === 0) {
            html += 'Не найдено. Попробуй еще раз.';
        } else {
            html += d.free.join('<br>');
        }
        html += '</div>';
        out.innerHTML = html;
    } catch (e) {
        out.innerHTML = `<div class="result error">Сеть недоступна</div>`;
    }
}
document.getElementById('base').addEventListener('keydown', e => { if (e.key === 'Enter') search(); });
</script>
</body>
</html>
"""

WORDS = ["Dark", "Neon", "Silent", "Ghost", "Storm", "Wolf", "Shadow", "Fire", "Ice", "Void", 
         "Cyber", "Night", "Lone", "Wild", "Frost", "Blood", "Sky", "Alpha", "Rogue", "Steel"]
SUFFIXES = ["", "_bot", "X", "1", "2", "7", "99", "_1"]

def check_fragment(username: str) -> bool:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(f"https://fragment.com/username/{username}", headers=headers, timeout=5)
        text = r.text.lower()
        if "unavailable" in text:
            return False
        if "available" in text or "for sale" in text or "auction" in text:
            return True
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.lower() if soup.title else ""
        if "not found" in title or "404" in title:
            return True
        return False
    except:
        return False

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/search")
def search():
    base = request.args.get("base", "").strip().lower()
    free_found = []
    
    # Если база указана, используем её, иначе берем случайные слова
    if base:
        check_list = [base + w.lower() for w in WORDS] + [w.lower() + base for w in WORDS]
    else:
        check_list = [w.lower() for w in WORDS] + [w.lower() + s for w in WORDS for s in SUFFIXES[1:]]
    
    random.shuffle(check_list)
    
    for u in check_list:
        if len(u) < 5 or len(u) > 32:
            continue
        if not re.match(r"^[a-z][a-z0-9_]{3,30}[a-z0-9]$", u):
            continue
            
        if check_fragment(u):
            free_found.append(f"@{u}")
            if len(free_found) >= 5: # останавливаемся, когда нашли 5 свободных
                break
                
    return jsonify({"free": free_found})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
