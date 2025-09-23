from flask import Flask, request, jsonify
import requests, os, re

app = Flask(__name__)

# -------------------------------
# Environment Variables
# -------------------------------
API_KEY = os.environ.get("GROQ_API_KEY")           # Your Groq/OpenRouter API key
MODEL_NAME = os.environ.get("GROQ_MODEL", "mixtral-8x7b")  # or best Groq model you have
API_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")

# -------------------------------
# Helper: light normalization
# -------------------------------
def normalize(text: str) -> str:
    # Collapse excessive whitespace & trim
    return re.sub(r'\s+', ' ', text).strip()

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
            ans = q.get("answerValues", [])
            if ans and "value" in ans[0]:
                answer_text = ans[0]["value"].get("text", "")
            break

    sentiment = "Neutral"  # default if no text

    if answer_text:
        answer_text = normalize(answer_text)

        # ---------------------------
        # Call Groq/OpenRouter model
        # ---------------------------
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
                        "Determine if the overall *intent* of the user message is "
                        "Positive, Negative, or Neutral. "
                        "Consider sarcasm, irony, satire, mixed languages, emojis, "
                        "and indirect wording. "
                        "Respond with just one of these words."
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
            ai_lower = ai_text.lower()
            if "positive" in ai_lower:
                sentiment = "Positive"
            elif "negative" in ai_lower:
                sentiment = "Negative"
        except Exception as e:
            print("API Exception:", e)

    # ---------------------------
    # Return in QuestionPro customVariables format
    # ---------------------------
    return jsonify({
        "customVariables": {
            "custom2": sentiment   # must match the Code you set in QuestionPro
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
