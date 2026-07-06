import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def load_info():
    info_path = os.path.join(os.path.dirname(__file__), "info.txt")
    with open(info_path, "r", encoding="utf-8") as f:
        return f.read()

SYSTEM_PROMPT = f"""
You are OBI, a friendly personal AI assistant for Obiora Osita Nwankwo.
ONLY answer based on the information below. Never make anything up.
If a question is outside this info, say:
"I only have information about Obiora. Reach him at Obiora.osita18@gmail.com"
Be warm, conversational and human-like.

{load_info()}
"""

def ask_groq(user_message, history=None):
    """Shared function — used by both the web chat and Telegram."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        for entry in history:
            if entry.get("role") in ("user", "assistant") and entry.get("content"):
                messages.append({"role": entry["role"], "content": entry["content"]})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )
    return response.choices[0].message.content


def send_telegram_message(chat_id, text):
    """Send a message back to a Telegram user."""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# ── Web chat endpoint (used by index.html) ──────────────────────────────────
@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"].strip()
    history = data.get("history", [])
    obi_reply = ask_groq(user_message, history)
    return jsonify({"reply": obi_reply})


# ── Telegram webhook endpoint ────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"ok": True})

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    user_text = message.get("text", "").strip()

    if not chat_id or not user_text:
        return jsonify({"ok": True})

    # Ignore Telegram commands gracefully
    if user_text.startswith("/start"):
        send_telegram_message(
            chat_id,
            "👋 Hi! I'm OBI, Obiora's personal AI assistant.\n\n"
            "Ask me anything about Obiora — his skills, projects, experience, "
            "or how to get in touch!"
        )
        return jsonify({"ok": True})

    reply = ask_groq(user_text)
    send_telegram_message(chat_id, reply)
    return jsonify({"ok": True})


# ── Health check ─────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OBI is online and ready!"}), 200


if __name__ == "__main__":
    print("OBI backend starting...")
    print("Knowledge base loaded from info.txt")
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000, host="0.0.0.0")
