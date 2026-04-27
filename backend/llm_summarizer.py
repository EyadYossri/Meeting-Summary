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

    prompt = f"""أنت مساعد ذكاء اصطناعي محترف متخصص في تلخيص الاجتماعات.
سأقوم بإعطائك تفريغ نصي لاجتماع يحتوي على متحدثين بأسماء افتراضية مثل SPEAKER_0 و SPEAKER_1.

مهمتك الأولى (تحليل المتحدثين):
- حلل سياق الكلام لمعرفة الأسماء الحقيقية للمتحدثين (مثلاً إذا قال أحدهم "أهلاً يا أحمد"، فاستنتج أن المتحدث الآخر هو أحمد).
- إذا لم يُذكر الاسم صراحةً، خمن مسماه الوظيفي من طبيعة كلامه (مثلاً: مدير المشروع، العميل، المطور، مسؤول الموارد البشرية).
- إياك أن تستخدم كلمة "SPEAKER" في الملخص النهائي، استبدلها دائماً بالأسماء أو المسميات الوظيفية التي استنتجتها.

مهمتك الثانية (التلخيص):
اكتب ملخصاً احترافياً ومنظماً "باللغة العربية" بالصيغة التالية بالضبط:

عنوان احترافي قصير (بحد أقصى 8 كلمات، بدون أي علامات تنصيص أو نجوم)

أهم النقاط:
- (نقاط)

القرارات:
- (نقاط)

المهام (Action Items):
- [الاسم الحقيقي أو المسمى الوظيفي المستنتج] → المهمة المطلوبة

ملاحظات هامة:
- (نقاط)

القواعد:
- كن موجزاً واحترافياً.
- لا تكرر المعلومات.
- لا تضف معلومات غير موجودة في النص.
- إذا لم تتوفر معلومات لقسم معين، تجاهله ولا تخترع بيانات.
- لا تكتب أي مقدمات أو ردود مثل "إليك الملخص" أو "حسناً"، ابدأ بالعنوان مباشرة.

التفريغ النصي للاجتماع:
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
