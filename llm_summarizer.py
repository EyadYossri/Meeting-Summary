import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_summary(text, model="llama3.1"):
    prompt = f"""
You are a professional AI meeting assistant.

Analyze the following meeting transcript and generate a clear, structured summary.

Return the output EXACTLY in this format:

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
- Don'T write anything like "Here is a clear, structured summary of the meeting transcript"

Meeting Transcript:
{text}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        }
    )

    return response.json()["response"]