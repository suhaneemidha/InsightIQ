from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("GROQ_API_KEY")

print("Exists:", key is not None)
print("Prefix:", key[:8] if key else "None")
print("Length:", len(key) if key else 0)