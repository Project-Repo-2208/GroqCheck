from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}
    user_text = data.get("response_text", "")
    if not user_text:
        return jsonify({"Output": "Neutral"})

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "Classify sentiment as Positive, Negative, or Neutral."},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0
    }

    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        resp = r.json()
        ai_text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print("Groq API error:", e)
        ai_text = ""

    sentiment = "Neutral"
    if "positive" in ai_text.lower():
        sentiment = "Positive"
    elif "negative" in ai_text.lower():
        sentiment = "Negative"

    return jsonify({"Output": sentiment})

@app.route("/", methods=["GET"])
def index():
    return "Server is running!"
