"""Lista os modelos disponíveis nos dois provedores (útil quando um ID é aposentado)."""
import os

from dotenv import load_dotenv

load_dotenv()

if os.getenv("ANTHROPIC_API_KEY"):
    import anthropic
    print("Claude models:")
    for m in anthropic.Anthropic().models.list():
        print(" ", m.id)

if os.getenv("GEMINI_API_KEY"):
    from google import genai
    print("Gemini models:")
    for m in genai.Client(api_key=os.getenv("GEMINI_API_KEY")).models.list():
        print(" ", m.name)
