import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

DEFAULT_MODEL = "llama-3.1-8b-instant"

CHUNK_SIZE = 4000


def summarize_chunk(chunk_text, model=DEFAULT_MODEL):
    """
    Map Step: هذه الدالة تقوم بتلخيص كل جزء بشكل سريع بدون تنسيق نهائي
    للحفاظ على المعلومات من الضياع.
    """
    prompt = f"""أنت مساعد ذكاء اصطناعي. سأعطيك جزءاً من تفريغ لاجتماع طويل.
قم بتلخيص هذا الجزء بدقة، واستخرج أهم النقاط والقرارات والمهام المذكورة فيه. ركز على التفاصيل ولا تضيع أي معلومة مهمة.

النص:
{chunk_text}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def generate_summary(text, model=DEFAULT_MODEL, stream_callback=None):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Add it to your .env file.")

    use_stream = stream_callback is not None
    
    if len(text) > CHUNK_SIZE:
        if use_stream:
            stream_callback("⏳ الميتينج طويل جداً.. جاري تقسيمه وتحليله بالذكاء الاصطناعي (Map-Reduce)...\n\n")
        
        chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        chunk_summaries = []
        
        for chunk in chunks:
            summary = summarize_chunk(chunk, model)
            chunk_summaries.append(summary)
        
        final_text_to_summarize = "\n\n--- ملخصات أجزاء الاجتماع ---\n\n".join(chunk_summaries)
    else:
        final_text_to_summarize = text

    prompt = f"""أنت مساعد ذكاء اصطناعي محترف متخصص في تلخيص الاجتماعات.
سأقوم بإعطائك إما (تفريغ نصي) أو (مجموعة ملخصات لاجتماع طويل). يحتوي النص على متحدثين بأسماء افتراضية مثل SPEAKER_0.

مهمتك الأولى (تحليل المتحدثين):
- حلل سياق الكلام لمعرفة الأسماء الحقيقية للمتحدثين (إذا تم ذكرها).
- إذا لم يُذكر الاسم صراحةً، خمن مسماه الوظيفي.
- إياك أن تستخدم كلمة "SPEAKER" في الملخص النهائي.

مهمتك الثانية (التلخيص):
اكتب ملخصاً احترافياً ومنظماً "باللغة العربية" بالصيغة التالية بالضبط:

عنوان احترافي قصير (بحد أقصى 8 كلمات، بدون أي علامات تنصيص)

أهم النقاط:
- (نقاط)

القرارات:
- (نقاط)

المهام:
- [الاسم الحقيقي أو المسمى الوظيفي المستنتج] → المهمة المطلوبة

ملاحظات هامة:
- (نقاط)

القواعد:
- كن موجزاً واحترافياً.
- لا تكرر المعلومات، ولا تضف معلومات غير موجودة.
- ابدأ بالعنوان مباشرة ولا تكتب أي مقدمات.

النص المطلوب تلخيصه:
{final_text_to_summarize}"""

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
