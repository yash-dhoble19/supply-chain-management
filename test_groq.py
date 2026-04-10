import urllib.request
import json
import ssl

api_key = "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"
url = "https://api.groq.com/openai/v1/chat/completions"

data = json.dumps({
    "model": "llama-3.1-8b-instant",
    "messages": [{"role": "user", "content": "Say hello in one word"}],
    "max_tokens": 10
}).encode("utf-8")

ctx = ssl.create_default_context()

req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"Bearer {api_key}")
req.add_header("Content-Type", "application/json")
req.add_header("User-Agent", "Mozilla/5.0")

try:
    with urllib.request.urlopen(req, context=ctx) as resp:
        result = json.loads(resp.read().decode())
        print("SUCCESS!")
        print("Response:", result["choices"][0]["message"]["content"])
        print("Model:", result.get("model"))
        print("Usage:", result.get("usage"))
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR {e.code}: {e.reason}")
    body = e.read().decode()
    print("Body:", body)
except Exception as e:
    print(f"ERROR: {e}")
