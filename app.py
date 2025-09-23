from flask import Flask, request, jsonify
import requests, os, re

app = Flask(__name__)

# -------------------------------
# Environment Variables (unchanged)
# -------------------------------
API_KEY = os.environ.get("GROQ_API_KEY")           # Your Groq/OpenRouter API key
MODEL_NAME = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
API_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

# -------------------------------
# Webhook Endpoint
# -------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}

    # Extract Q1 answer text
    answer_text = ""
    for q in data.get("responseSet", []):
        if q.get("questionCode") == "Q1":
            vals = q.get("answerValues", [])
            if vals and "value" in vals[0]:
                answer_text = vals[0]["value"].get("text", "")
            break

    sentiment = "Neutral"

    if answer_text:
        answer_text = normalize(answer_text)

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert sentiment analyst. "
                        "Classify the overall intent of the message as Positive, Negative, or Neutral. "
                        "Detect sarcasm, satire, irony, humor, and indirect wording. "
                        "Respond with only one word."
                    )
                },
                {"role": "user", "content": answer_text}
            ],
            "temperature": 0
        }

        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            ai_text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            lower = ai_text.lower()
            if "positive" in lower:
                sentiment = "Positive"
            elif "negative" in lower:
                sentiment = "Negative"
        except Exception as e:
            print("API Exception:", e)

    # Must match the Code field you set in QuestionPro (e.g., custom2)
    return jsonify({
        "customVariables": {
            "custom2": sentiment
        }
    })

@app.route("/", methods=["GET"])
def index():
    return "Webhook server is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
