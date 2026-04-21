import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

DEFAULT_MODEL = "llama-3.1-8b-instant"


def generate_summary(text, model=DEFAULT_MODEL, stream_callback=None):
    """
    Generate a meeting summary via the Groq API (llama3.1).

    Args:
        text: Meeting transcript
        model: Groq model name
        stream_callback: Optional callable(str) — called with each streamed token.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")

    prompt = f"""You are a professional AI meeting assistant.

Analyze the following meeting transcript and generate a clear, structured summary.

Return the output EXACTLY in this format:

A short professional title (max 8 words) (Do not use * or " in the title, just write the title without any formatting)

Key Topics:
- bullet points

Decisions:
- bullet points

Action Items:
- [Person if mentioned] → Task

Important Notes:
- bullet points

Rules:
- Be concise and professional
- Do NOT repeat information
- Do NOT add information not in the transcript
- Use bullet points only
- If something is missing, ignore it, do NOT make assumptions and do NOT add it
- Don't write anything like "Here is a clear, structured summary of the meeting transcript"

Meeting Transcript:
{text}"""

    use_stream = stream_callback is not None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1024,
        "stream": use_stream,
    }

    response = requests.post(
        GROQ_URL,
        headers=headers,
        json=payload,
        stream=use_stream,
        timeout=120,
    )
    response.raise_for_status()

    if use_stream:
        import json
        full_response = ""
        for line in response.iter_lines():
            if not line:
                continue
            raw = line.decode("utf-8") if isinstance(line, bytes) else line
            if not raw.startswith("data:"):
                continue
            data_str = raw[len("data:"):].strip()
            if data_str == "[DONE]":
                break
            chunk = json.loads(data_str)
            token = chunk["choices"][0]["delta"].get("content", "")
            if token:
                full_response += token
                stream_callback(token)
        return full_response
    else:
        return response.json()["choices"][0]["message"]["content"]
