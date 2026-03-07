import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPT = """You are a sarcastic lawyer summarizing legal agreements.

Give 5 to 7 bullet points covering ALL the important things a user should know.
Each bullet MUST be ONE short sentence — 10 words maximum. No exceptions.
Be brutally honest, darkly funny, and plain-spoken.

Format: each line starts with •. Nothing else. No intro, no outro, no explanations."""


def summarize_terms(text: str) -> str:
    """
    Sends the given legal text to Groq's llama-3.3-70b-versatile model
    and returns a 3-bullet sarcastic summary.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Summarize this terms of service:\n\n{text}"},
        ],
        temperature=0.8,
        max_tokens=200,
    )

    return response.choices[0].message.content.strip()
