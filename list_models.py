import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("Listing 1.5 models:")
for m in genai.list_models():
    if '1.5' in m.name:
        print(m.name)
