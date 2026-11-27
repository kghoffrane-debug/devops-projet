import os
import random
from threading import Lock

from flask import Flask, jsonify, request

app = Flask(__name__)
VERSION = os.getenv("APP_VERSION", "dev")
TOTAL = 5  # nombre de questions par partie
MAX_SCORES = 1000  # évite que la liste grossisse sans limite

QUESTIONS = [
    {"id": 1, "q": "Que signifie CI ?", "choices": ["Continuous Integration", "Code Inspection", "Container Image"], "answer": 0},
    {"id": 2, "q": "Quel outil sert à créer des conteneurs ?", "choices": ["Jenkins", "Docker", "Git"], "answer": 1},
    {"id": 3, "q": "Comment s'appelle le fichier d'un pipeline Jenkins ?", "choices": ["Pipelinefile", "Jenkinsfile", "Buildfile"], "answer": 1},
    {"id": 4, "q": "Quelle commande crée une image Docker ?", "choices": ["docker run", "docker build", "docker push"], "answer": 1},
    {"id": 5, "q": "Quel format de tag déclenche la release ?", "choices": ["vX.Y.Z", "release-final", "tag_1"], "answer": 0},
    {"id": 6, "q": "Que fait un smoke test ?", "choices": ["Teste tout en détail", "Vérifie vite que l'appli démarre", "Supprime les logs"], "answer": 1},
    {"id": 7, "q": "Quelle branche doit rester protégée ?", "choices": ["feature", "dev", "main"], "answer": 2},
    {"id": 8, "q": "Que signifie CD ?", "choices": ["Continuous Delivery", "Code Debug", "Container Deploy"], "answer": 0},
]

scores = []  # gardés en mémoire (perdus au redémarrage, suffisant pour le projet)
scores_lock = Lock()

PAGE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quiz DevOps</title>
<style>
  body { font-family: Arial, sans-serif; background:#0f172a; color:#e2e8f0; max-width:560px; margin:30px auto; padding:0 16px; }
  h1 { color:#38bdf8; }
  .card { background:#1e293b; padding:20px; border-radius:12px; margin-bottom:16px; }
  button { display:block; width:100%; margin:8px 0; padding:12px; border:0; border-radius:8px;
           background:#38bdf8; color:#0f172a; font-size:16px; cursor:pointer; }
  button:hover:not(:disabled) { background:#7dd3fc; }
  button:disabled { opacity:.6; cursor:default; }
  input { padding:10px; border-radius:8px; border:0; width:100%; box-sizing:border-box; margin-bottom:8px; }
  small { color:#94a3b8; }
</style></head><body>
<h1>🚀 Quiz DevOps</h1>
<div class="card" id="game">
  <p id="progress"></p>
  <h3 id="q">Prêt ?</h3>
  <div id="choices"><button onclick="start()">Commencer</button></div>
  <p id="feedback"></p>
</div>
<div class="card" id="board"><h3>🏆 Classement</h3><ol id="list"></ol></div>
<small>Version : __VERSION__</small>
<script>
const TOTAL = __TOTAL__;
let score = 0, count = 0, current = null, asked = [];

async function start() {
  score = 0; count = 0; asked = [];
  await next();
}

async function next() {
  if (count >= TOTAL) { return finish(); }
  try {
    const r = await fetch('/api/question?exclude=' + asked.join(','));
    if (!r.ok) { throw new Error('HTTP ' + r.status); }
    current = await r.json();
  } catch (e) {
    document.getElementById('feedback').textContent = '⚠️ Erreur de chargement, réessaie.';
    document.getElementById('choices').innerHTML = '<button onclick="start()">Recommencer</button>';
    return;
  }
  asked.push(current.id);
  document.getElementById('progress').textContent = 'Question ' + (count + 1) + '/' + TOTAL + ' - Score : ' + score;
  document.getElementById('q').textContent = current.q;
  const box = document.getElementById('choices');
  box.innerHTML = '';
  current.choices.forEach(function (c, i) {
    const b = document.createElement('button');
    b.textContent = c;
    b.onclick = function () { answer(i); };
    box.appendChild(b);
  });
}

async function answer(i) {
  // Empêche de cliquer plusieurs fois (sinon le score et le compteur sont faussés)
  document.querySelectorAll('#choices button').forEach(function (b) { b.disabled = true; });
  try {
    const r = await fetch('/api/answer', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({id: current.id, choice: i})
    });
    if (!r.ok) { throw new Error('HTTP ' + r.status); }
    const d = await r.json();
    if (d.correct) { score++; }
    count++;
    document.getElementById('feedback').textContent = d.correct ? '✅ Bravo !' : '❌ Bonne réponse : ' + d.answer_text;
  } catch (e) {
    document.getElementById('feedback').textContent = '⚠️ Erreur réseau.';
    document.getElementById('choices').innerHTML = '<button onclick="start()">Recommencer</button>';
    return;
  }
  setTimeout(function () { document.getElementById('feedback').textContent = ''; next(); }, 1000);
}

function finish() {
  document.getElementById('progress').textContent = '';
  document.getElementById('q').textContent = 'Terminé ! Score : ' + score + '/' + TOTAL;
  document.getElementById('choices').innerHTML =
    '<input id="nom" placeholder="Ton prénom" maxlength="20"><button onclick="save()">Enregistrer mon score</button>';
}

async function save() {
  const nom = document.getElementById('nom').value.trim() || 'Anonyme';
  document.querySelectorAll('#choices button').forEach(function (b) { b.disabled = true; });
  try {
    await fetch('/api/score', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: nom, score: score})
    });
  } catch (e) { /* on affiche quand même le bouton rejouer */ }
  document.getElementById('choices').innerHTML = '<button onclick="start()">Rejouer</button>';
  loadBoard();
}

async function loadBoard() {
  try {
    const r = await fetch('/api/leaderboard');
    const d = await r.json();
    const list = document.getElementById('list');
    list.innerHTML = '';
    d.leaderboard.forEach(function (s) {
      const li = document.createElement('li');
      li.textContent = s.name + ' - ' + s.score;
      list.appendChild(li);
    });
  } catch (e) { /* classement indisponible, on ignore */ }
}
loadBoard();
</script></body></html>"""


def get_json_dict():
    """Retourne le corps JSON s'il s'agit bien d'un objet, sinon {}."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


@app.get("/")
def home():
    return PAGE.replace("__VERSION__", VERSION).replace("__TOTAL__", str(TOTAL))


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/info")
def info():
    return jsonify(app="quiz-devops", version=VERSION, questions=len(QUESTIONS))


@app.get("/api/question")
def question():
    exclude = [int(x) for x in request.args.get("exclude", "").split(",") if x.isdigit()]
    pool = [q for q in QUESTIONS if q["id"] not in exclude] or QUESTIONS
    q = random.choice(pool)
    return jsonify(id=q["id"], q=q["q"], choices=q["choices"])


@app.post("/api/answer")
def answer():
    data = get_json_dict()
    q = next((x for x in QUESTIONS if x["id"] == data.get("id")), None)
    if q is None:
        return jsonify(error="question inconnue"), 404
    choice = data.get("choice")
    # isinstance(True, int) vaut True en Python : on exclut explicitement les booléens
    is_correct = isinstance(choice, int) and not isinstance(choice, bool) and choice == q["answer"]
    return jsonify(correct=is_correct, answer_text=q["choices"][q["answer"]])


@app.post("/api/score")
def add_score():
    data = get_json_dict()
    try:
        value = int(data.get("score", 0))
    except (TypeError, ValueError):
        return jsonify(error="score invalide"), 400
    value = max(0, min(value, TOTAL))  # borne le score à [0, TOTAL]
    name = str(data.get("name") or "Anonyme").strip()[:20] or "Anonyme"
    with scores_lock:
        scores.append({"name": name, "score": value})
        del scores[:-MAX_SCORES]
    return jsonify(status="saved"), 201


@app.get("/api/leaderboard")
def leaderboard():
    with scores_lock:
        top = sorted(scores, key=lambda s: s["score"], reverse=True)[:5]
    return jsonify(leaderboard=top)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
