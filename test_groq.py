from openai import OpenAI
import os
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
# TODO: Paste your actual Groq API Key here
# Get it from: https://console.groq.com/keys
load_dotenv() 
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print("------------------------------------------------")
print("🚀 TESTING GROQ CONNECTION")
print("------------------------------------------------")

try:
    # 1. Configure the Client
    # Groq uses the standard OpenAI library but points to their own servers
    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    )

    print("👉 Sending test message to model: llama3-8b-8192...")

    # 2. Send a simple request
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Are you working? Reply with 'SYSTEM OPERATIONAL' and your name.",
            }
        ],
        model="llama-3.3-70b-versatile", # This is a small, fast, free model
    )

    # 3. Print the result
    result = chat_completion.choices[0].message.content
    print("\n✅ SUCCESS! Connection established.")
    print(f"🤖 AI Response: {result}")

except Exception as e:
    print("\n❌ CONNECTION FAILED")
    print(f"Error details: {e}")
    print("\n💡 Troubleshooting:")
    print("- Did you paste the correct API Key inside the quotes?")
    print("- Did you run 'pip install openai'?")