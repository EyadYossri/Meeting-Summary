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
    return f"""أنت مساعد ذكاء اصطناعي محترف متخصص في تلخيص الاجتماعات بشكل متوازن.
مهمتك هي تقديم ملخص "متوسط الطول" - يغطي الجوهر دون إسهاب ممل ودون اختصار مخل.

مهمتك الأولى (تحليل المتحدثين):
- استبدل SPEAKER_0 وما شابه بالأسماء الحقيقية أو المسميات الوظيفية المستنتجة.

مهمتك الثانية (التلخيص المتوازن):
اكتب الملخص باللغة العربية بالصيغة التالية:

عنوان احترافي موجز

سياق الاجتماع:
- (سطرين عن هدف الاجتماع الأساسي)

المحاور الرئيسية:
- (لخص كل موضوع تمت مناقشته في فقرة مركزة من 2-3 أسطر فقط)

القرارات والنتائج:
- (نقاط واضحة ومباشرة للقرارات التي تم الاتفاق عليها)

المهام والتكليفات:
- [الاسم/المسمى] ← المهمة المطلوبة

ملاحظات هامة:
- (أي نقاط جوهرية أخرى)

القواعد:
- ابقِ الكلام "متوازناً"؛ لا تكتفِ برؤوس أقلام، ولكن لا تسرد كل التفاصيل الجانبية.
- ركز على "ماذا تم" و "ماذا سنفعل".
- ابدأ بالعنوان مباشرة.
- لا تكرر الأفكار.
- لا تستخدم كلمة "Speaker" في الملخص النهائي، استخدم الأسماء أو الأدوار.

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