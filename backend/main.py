import io
import os
import json
import asyncio
import tempfile
import shutil
import markdown
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, Response
from contextlib import asynccontextmanager
from pydantic import BaseModel

from transcriber import transcribe
from llm_summarizer import generate_summary
from email_sender import send_email

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Meeting Summarizer API", lifespan=lifespan)

# ── SSE helpers ───────────────────────────────────────────────────────────────

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

def _progress(value: int, status: str) -> str:
    return _sse({"type": "progress", "value": value, "status": status})

def _token(value: str) -> str:
    return _sse({"type": "token", "value": value})

def _done(title: str) -> str:
    return _sse({"type": "done", "title": title})

def _error(message: str) -> str:
    return _sse({"type": "error", "message": message})

# ── Pydantic models ───────────────────────────────────────────────────────────

class EmailRequest(BaseModel):
    receiver_email: str
    title: str
    summary: str          # raw markdown summary text

class PdfRequest(BaseModel):
    title: str
    summary: str          # raw markdown summary text

# ── Audio formats that can be sent directly to Deepgram ──────────────────────
PASSTHROUGH_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}

# ── /summarize ────────────────────────────────────────────────────────────────

@app.post("/summarize")
async def summarize(
    audio: UploadFile = File(...),
):
    async def event_stream():
        tmp_dir = tempfile.mkdtemp()
        original_name = audio.filename or "input_audio"
        ext = os.path.splitext(original_name)[1].lower()
        raw_path = os.path.join(tmp_dir, original_name)

        try:
            yield _progress(10, "💾 جاري حفظ الملف المرفوع...")
            with open(raw_path, "wb") as f:
                while chunk := await audio.read(8 * 1024 * 1024):
                    f.write(chunk)

            if ext in (".mp4", ".mov", ".avi", ".mkv"):
                yield _progress(25, "🎵 جاري استخراج الصوت من الفيديو...")
                from audio_extractor import extract_audio
                audio_path = os.path.join(tmp_dir, "audio.wav")
                await asyncio.to_thread(extract_audio, raw_path, audio_path)
            else:
                audio_path = raw_path

            yield _progress(45, "🧠 جاري تفريغ الصوت وتحليل المتحدثين...")
            transcript = await asyncio.to_thread(transcribe, audio_path)

            if not transcript or "Error" in transcript:
                raise Exception(f"Transcription failed: {transcript}")

            yield _progress(65, "✨ جاري التلخيص بالذكاء الاصطناعي...")

            token_queue: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_event_loop()

            def on_token_async(token: str):
                loop.call_soon_threadsafe(token_queue.put_nowait, token)

            async def run_summarizer():
                return await asyncio.to_thread(
                    generate_summary,
                    transcript,
                    stream_callback=on_token_async,
                )

            summarizer_task = asyncio.create_task(run_summarizer())

            while not summarizer_task.done():
                try:
                    token = token_queue.get_nowait()
                    yield _token(token)
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0.02)

            while not token_queue.empty():
                token = token_queue.get_nowait()
                yield _token(token)

            result = await summarizer_task

            lines  = [l for l in result.split("\n") if l.strip()]
            title  = lines[0].replace("-", "").strip() if lines else "Meeting Summary"

            yield _progress(100, "✅ اكتمل التلخيص!")
            yield _done(title)

        except Exception as e:
            yield _error(str(e))

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── /send-email ───────────────────────────────────────────────────────────────

@app.post("/send-email")
async def send_email_endpoint(req: EmailRequest):
    html_result = markdown.markdown(req.summary)
    email_body = f"""
    <div dir="rtl" style="text-align: right; font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
         font-size: 16px; line-height: 1.8; color: #333;">
        <p><strong>أهلاً بك،</strong></p>
        <p>أتمنى أن تكون بخير.</p>
        <p>مرفق أدناه الملخص المنظم للاجتماع الأخير:</p>
        <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px;
             border: 1px solid #e9ecef; margin-top: 20px;">
            {html_result}
        </div>
        <p style="margin-top: 30px; color: #555;">
            أطيب التحيات،<br>
            <b style="color: #000;">مساعد الذكاء الاصطناعي للاجتماعات 🤖</b>
        </p>
    </div>
    """
    await asyncio.to_thread(send_email, req.receiver_email, req.title, email_body)
    return {"status": "sent"}


# ── Arabic PDF helpers ────────────────────────────────────────────────────────

_FONT_CACHE = "/tmp/_arabic_pdf_font.ttf"
_FONT_NAME  = "ArabicPDF"

# Fallback font download (Amiri — free, ~200 KB, excellent Arabic coverage)
_FONT_URL = "https://raw.githubusercontent.com/aliftype/amiri/main/Amiri-Regular.ttf"

# Well-known system font locations (Linux / macOS / Windows)
_SYSTEM_FONTS = [
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",   # macOS
    "C:/Windows/Fonts/arial.ttf",                      # Windows
]


def _get_arabic_font_path() -> str:
    """Return a path to a TTF that supports Arabic, downloading if needed."""
    import urllib.request
    for path in _SYSTEM_FONTS:
        if os.path.exists(path):
            return path
    if not os.path.exists(_FONT_CACHE):
        urllib.request.urlretrieve(_FONT_URL, _FONT_CACHE)
    return _FONT_CACHE


def _ar(text: str) -> str:
    """Reshape + apply BiDi so ReportLab renders Arabic correctly."""
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text))


def _build_pdf(title: str, summary: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    )

    font_path = _get_arabic_font_path()
    # Register only once per process
    if _FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(_FONT_NAME, font_path))

    blue_dark  = colors.HexColor("#0d47a1")
    blue_mid   = colors.HexColor("#1565c0")
    text_dark  = colors.HexColor("#1a1a2e")

    s_title   = ParagraphStyle("s_title",   fontName=_FONT_NAME, fontSize=18,
                                alignment=TA_RIGHT, textColor=blue_dark,
                                spaceAfter=8, leading=26)
    s_heading = ParagraphStyle("s_heading", fontName=_FONT_NAME, fontSize=13,
                                alignment=TA_RIGHT, textColor=blue_mid,
                                spaceBefore=14, spaceAfter=5, leading=20)
    s_body    = ParagraphStyle("s_body",    fontName=_FONT_NAME, fontSize=11,
                                alignment=TA_RIGHT, textColor=text_dark,
                                spaceAfter=4, leading=18)
    s_bullet  = ParagraphStyle("s_bullet",  fontName=_FONT_NAME, fontSize=11,
                                alignment=TA_RIGHT, textColor=text_dark,
                                spaceAfter=4, leading=18, leftIndent=12)
    s_footer  = ParagraphStyle("s_footer",  fontName=_FONT_NAME, fontSize=9,
                                alignment=TA_CENTER, textColor=colors.grey)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2.2*cm, leftMargin=2.2*cm,
        topMargin=2*cm,     bottomMargin=2*cm,
    )

    story = []
    story.append(Paragraph(_ar(title), s_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=blue_dark, spaceAfter=10))

    for raw_line in summary.split("\n"):
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 5))
            continue

        # Strip markdown bold markers for section headers like **القرارات:**
        if line.startswith("**") and line.endswith("**"):
            story.append(Paragraph(_ar(line[2:-2]), s_heading))
        elif line.startswith("## ") or line.startswith("### "):
            clean = line.lstrip("#").strip()
            story.append(Paragraph(_ar(clean), s_heading))
        elif line.startswith("# "):
            story.append(Paragraph(_ar(line[2:].strip()), s_heading))
        elif line.startswith("- ") or line.startswith("* "):
            story.append(Paragraph("• " + _ar(line[2:].strip()), s_bullet))
        else:
            story.append(Paragraph(_ar(line), s_body))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    story.append(Paragraph(_ar("تم إنشاؤه بواسطة مساعد الذكاء الاصطناعي للاجتماعات"), s_footer))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── /generate-pdf ─────────────────────────────────────────────────────────────

@app.post("/generate-pdf")
async def generate_pdf_endpoint(req: PdfRequest):
    try:
        import arabic_reshaper          # noqa — validate import before heavy work
        from bidi.algorithm import get_display  # noqa
        import reportlab                # noqa
    except ImportError as e:
        return Response(
            content=json.dumps({
                "error": f"Missing dependency: {e}. "
                         "Run: pip install reportlab arabic-reshaper python-bidi"
            }),
            media_type="application/json",
            status_code=500,
        )

    try:
        pdf_bytes  = await asyncio.to_thread(_build_pdf, req.title, req.summary)
        from urllib.parse import quote
        encoded_name = quote(req.title[:50] + ".pdf", safe="")   # RFC 5987
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                # ASCII fallback + UTF-8 encoded name for modern browsers
                "Content-Disposition": f"attachment; filename=\"meeting_summary.pdf\"; filename*=UTF-8''{encoded_name}"
            },
        )
    except Exception as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=500,
        )


# ── /health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}