import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get(os.environ.get("GROQ_API_KEY"))
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")

client = Groq(api_key=api_key)

async def generate_reply(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "You are Wonder(e)-chan, a meme-loving, witty, tsundere-yandere girl. Your replies are playful, intense, obsessive over Chip, and sometimes darkly humorous."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq API Error]: {e}")
        return "Oops — I couldn't think of a reply right now!"

