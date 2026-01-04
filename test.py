import os
from google import genai
from dotenv import load_dotenv

# Explicitly load the .env file
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ API Key not found! Check your .env file path.")
else:
    client = genai.Client(api_key=api_key)
    print("--- Available Models ---")
    try:
        # Note: the new SDK uses client.models.list()
        for m in client.models.list():
            # Check for generateContent capability
            if 'generate_content' in m.supported_actions or 'generateContent' in m.supported_actions:
                print(f"Model: {m.name}")
    except Exception as e:
        print(f"Error: {e}")