import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"].strip()
    history = data.get("history", [])
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

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

    obi_reply = response.choices[0].message.content
    return jsonify({"reply": obi_reply})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OBI is online and ready!"}), 200

if __name__ == "__main__":
    print("OBI backend starting...")
    print("Knowledge base loaded from info.txt")
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000, host="0.0.0.0")
