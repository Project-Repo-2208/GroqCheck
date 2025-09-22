from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")  # put your key in environment
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    user_text = data.get("response_text", "")  # adjust key to your survey field

    # Call Groq API
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    payload = {
        "model": "mixtral-8x7b-32768",   # or any Groq-supported model
        "messages": [
            {"role": "system", "content": "Classify sentiment as Positive, Negative, or Neutral."},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0
    }
    r = requests.post(GROQ_URL, json=payload, headers=headers)
    ai_text = r.json()["choices"][0]["message"]["content"].strip()

    # Normalize to one of the three options
    sentiment = "Neutral"
    if "positive" in ai_text.lower():
        sentiment = "Positive"
    elif "negative" in ai_text.lower():
        sentiment = "Negative"

    return jsonify({"Output": sentiment})
