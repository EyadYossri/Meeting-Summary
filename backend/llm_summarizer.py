import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

# ── API config ────────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL     = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL       = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:streamGenerateContent?alt=sse&key={key}"
)

MAX_RETRIES           = 5
RATE_LIMIT_BASE_WAIT  = 30   # seconds — doubles on each retry


# ── Prompt ────────────────────────────────────────────────────────────────────

def _final_prompt(text: str) -> str:
    return f"""أنت مساعد ذكاء اصطناعي محترف متخصص في تحليل الاجتماعات بعمق.
سأقوم بإعطائك تفريغاً نصياً لاجتماع. يحتوي النص على متحدثين بأسماء افتراضية مثل SPEAKER_0.

مهمتك الأولى (تحليل المتحدثين):
- استنتج الأسماء الحقيقية أو المسميات الوظيفية بدقة.

مهمتك الثانية (التلخيص التفصيلي):
اكتب ملخصاً "شاملاً وموسعاً" باللغة العربية بالصيغة التالية:

عنوان احترافي مفصل للابتماع

سياق الاجتماع وهدفه:
- (شرح مفصل لسبب الاجتماع والأهداف التي تمت مناقشتها)

أهم المحاور والنقاط التفصيلية:
- (قم بتوسيع كل نقطة تم ذكرها، اشرح الحجج والآراء المختلفة التي طرحت بالتفصيل)

القرارات المتخذة:
- (ذكر القرار مع شرح بسيط لسبب اتخاذه)

خطة العمل والمهام (جدول تفصيلي):
- [الاسم/المسمى] ← المهمة: (وصف دقيق للمهمة) | الموعد النهائي (إن وجد)

ملاحظات جانبية وتوصيات:
- (أي تفاصيل دقيقة أو ملاحظات فنية تم ذكرها في الاجتماع)

القواعد الجديدة:
- "تجنب الإيجاز الشديد"؛ قدم تفاصيل كافية تجعل من يقرأ الملخص يشعر كأنه حضر الاجتماع.
- حافظ على التنسيق والاحترافية.
- ابدأ بالعنوان مباشرة.
- لا تستخدم كلمة "Speaker" في الملخص النهائي، استبدلها بالأسماء الحقيقية أو الألقاب المستنتجة.

النص المطلوب تلخيصه:
{text}"""


# ── Core call ─────────────────────────────────────────────────────────────────

def generate_summary(text: str, model: str | None = None, stream_callback=None) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY غير موجود. أضفه في ملف .env الخاص بك.")

    chosen_model = model or GEMINI_MODEL
    url = GEMINI_URL.format(model=chosen_model, key=GEMINI_API_KEY)

    payload = {
        "contents": [{"parts": [{"text": _final_prompt(text)}]}],
        "generationConfig": {
            "temperature":     0.3,
            "maxOutputTokens": 8192,
        },
    }

    # POST with exponential back-off on 429
    wait = RATE_LIMIT_BASE_WAIT
# Inside your generate_summary function, update the exception handling:

    for attempt in range(1, MAX_RETRIES + 1): 
        try: 
            response = requests.post(url, json=payload, stream=True, timeout=180) 
            response.raise_for_status() 
            break 
        except requests.exceptions.HTTPError as exc: 
            code = exc.response.status_code if exc.response is not None else 0 
            
            # Catch both Rate Limits (429) and Server Overloads (503/500)
            if code in [429, 500, 502, 503, 504]: 
                if attempt == MAX_RETRIES: 
                    raise Exception(f"Failed after {MAX_RETRIES} attempts due to Server Error {code}.")
                
                print(f"[Gemini {code}] Server busy. Waiting {wait}s (Attempt {attempt}/{MAX_RETRIES})") 
                time.sleep(wait) 
                wait = min(wait * 2, 300) 
            else: 
                raise

    # Stream response
    full = ""
    for raw_line in response.iter_lines():
        if not raw_line:
            continue
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        if not line.startswith("data:"):
            continue
        data_str = line[len("data:"):].strip()
        if not data_str or data_str == "[DONE]":
            continue
        try:
            chunk = json.loads(data_str)
            token = chunk["candidates"][0]["content"]["parts"][0]["text"]
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
        if token:
            full += token
            if stream_callback:
                stream_callback(token)

    if not full:
        raise ValueError("Gemini أعاد استجابة فارغة. يرجى المحاولة مرة أخرى.")

    return full