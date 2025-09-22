from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

# -------------------------------
# Environment Variables
# -------------------------------
API_KEY = os.environ.get("GROQ_API_KEY")          # Your Groq/OpenRouter API key
MODEL_NAME = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
API_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")

# -------------------------------
# Webhook Endpoint
# -------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}

    # ---------------------------
    # Extract Q1 answer text
    # ---------------------------
    answer_text = ""
    for q in data.get("responseSet", []):
        if q.get("questionCode") == "Q1":
            answer_values = q.get("answerValues", [])
            if answer_values and "value" in answer_values[0]:
                answer_text = answer_values[0]["value"].get("text", "")
            break

    if not answer_text:
        sentiment = "Neutral"
    else:
        # ---------------------------
        # Call Groq GPT-OSS API
        # ---------------------------
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "Classify sentiment as Positive, Negative, or Neutral."},
                {"role": "user", "content": answer_text}
            ],
            "temperature": 0
        }

        ai_text = ""
        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            resp = r.json()
            ai_text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print("API Exception:", e)

        # ---------------------------
        # Determine sentiment
        # ---------------------------
        sentiment = "Neutral"
        if "positive" in ai_text.lower():
            sentiment = "Positive"
        elif "negative" in ai_text.lower():
            sentiment = "Negative"

    # ---------------------------
    # Return in QuestionPro customVariables format
    # ---------------------------
    return jsonify({
        "customVariables": {
            "Output": sentiment,  # Display Name
            "output": sentiment   # Code
        }
    })


# -------------------------------
# Health Check / Test Endpoint
# -------------------------------
@app.route("/", methods=["GET"])
def index():
    return "Webhook server is running!"

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
