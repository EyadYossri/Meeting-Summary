import os
import json
import asyncio
import tempfile
import shutil
import markdown
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from audio_extractor import extract_audio
from transcriber import transcribe
from llm_summarizer import generate_summary
from email_sender import send_email

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Meeting Summarizer API", lifespan=lifespan)

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"

def _progress(value: int, status: str) -> str:
    return _sse({"type": "progress", "value": value, "status": status})

def _token(value: str) -> str:
    return _sse({"type": "token", "value": value})

def _done(title: str, summary: str) -> str:
    return _sse({"type": "done", "title": title, "summary": summary})

def _error(message: str) -> str:
    return _sse({"type": "error", "message": message})

@app.post("/summarize")
async def summarize(
    video: UploadFile = File(...),
    receiver_email: str = Form(...),
):

    async def event_stream():
        tmp_dir = tempfile.mkdtemp()
        video_filename = video.filename if video.filename else "input_video"
        video_path = os.path.join(tmp_dir, video_filename)
        audio_path = os.path.join(tmp_dir, "audio.wav")

        try:
            yield _progress(10, "💾 جاري حفظ الفيديو المرفوع...")
            with open(video_path, "wb") as f:
                while chunk := await video.read(8 * 1024 * 1024):
                    f.write(chunk)

            yield _progress(25, "🎵 جاري استخراج الصوت...")
            await asyncio.to_thread(extract_audio, video_path, audio_path)

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

            yield _progress(90, "📧 جاري إرسال الملخص للإيميل...")

            lines = [l for l in result.split("\n") if l.strip()]
            title = lines[0].replace("-", "").strip() if lines else "Meeting Summary"

            html_result = markdown.markdown(result)

            email_body = f"""
            <div dir="rtl" style="text-align: right; font-family: 'Segoe UI', Tahoma, Arial, sans-serif; font-size: 16px; line-height: 1.8; color: #333;">
                <p><strong>أهلاً بك،</strong></p>
                <p>أتمنى أن تكون بخير.</p>
                <p>مرفق أدناه الملخص المنظم للاجتماع الأخير:</p>
                
                <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px; border: 1px solid #e9ecef; margin-top: 20px;">
                    {html_result}
                </div>
                
                <p style="margin-top: 30px; color: #555;">أطيب التحيات،<br><b style="color: #000;">مساعد الذكاء الاصطناعي للاجتماعات 🤖</b></p>
            </div>
            """

            await asyncio.to_thread(
                send_email,
                receiver_email,
                title,
                email_body,
            )

            yield _progress(100, "Done!")
            yield _done(title, result)

        except Exception as e:
            yield _error(str(e))

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/health")
def health():
    return {"status": "ok"}
