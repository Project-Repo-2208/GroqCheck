from flask import Flask, request, jsonify
import requests, os

app = Flask(__name__)

# Environment variables
API_KEY = os.environ.get("GROQ_API_KEY")          # Your Groq/OpenRouter API key
MODEL_NAME = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
API_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}
    user_text = data.get("response_text", "")
    
    if not user_text:
        return jsonify({"Output": "Neutral"})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Classify sentiment as Positive, Negative, or Neutral."},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0
    }

    print("Sending payload to API:", payload)

    ai_text = ""
    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        print("API response status:", r.status_code)
        print("API response body:", r.text)

        r.raise_for_status()
        resp = r.json()
        ai_text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
    except requests.exceptions.RequestException as e:
        print("RequestException:", e)
    except Exception as e:
        print("Other Exception:", e)

    # Determine sentiment
    sentiment = "Neutral"
    if "positive" in ai_text.lower():
        sentiment = "Positive"
    elif "negative" in ai_text.lower():
        sentiment = "Negative"

    return jsonify({"Output": sentiment})


@app.route("/", methods=["GET"])
def index():
    return "Webhook server is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
