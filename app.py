import os
from flask import Flask, jsonify

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "dev")

@app.get("/")
def home():
    return jsonify(message="Bonjour DevOps", version=VERSION)

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.get("/hello/<nom>")
def hello(nom):
    return jsonify(message=f"Bonjour {nom}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
