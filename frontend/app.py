import streamlit as st
import requests
import json
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in [
    ("summary_text", None),
    ("summary_title", None),
    ("show_email_form", False),
    ("email_sent", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🎙️ Meeting Summarizer AI")

# ── Audio source tabs ─────────────────────────────────────────────────────────
tab_upload, tab_record = st.tabs(["📁 Upload Audio", "🎤 Record Audio"])

audio_bytes = None
audio_name  = None
audio_mime  = None

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a meeting audio file",
        type=["mp3", "wav", "m4a", "ogg", "flac", "webm", "mp4", "mov", "avi"],
    )
    if uploaded_file:
        audio_bytes = uploaded_file.read()
        audio_name  = uploaded_file.name
        audio_mime  = uploaded_file.type or "audio/wav"
        st.audio(audio_bytes, format=audio_mime)

with tab_record:
    st.caption("Click the microphone to start/stop recording.")
    recorded = st.audio_input("Record meeting audio")
    if recorded:
        audio_bytes = recorded.read()
        audio_name  = "recording.wav"
        audio_mime  = "audio/wav"
        st.audio(audio_bytes, format="audio/wav")

# ── Start summarization ───────────────────────────────────────────────────────
if st.button("▶️ Start Summarization", type="primary"):
    if not audio_bytes:
        st.error("Please upload or record an audio file first.")
    else:
        # Reset previous results
        st.session_state.summary_text  = None
        st.session_state.summary_title = None
        st.session_state.show_email_form = False
        st.session_state.email_sent    = False

        progress     = st.progress(0)
        status       = st.empty()
        summary_box  = st.empty()
        summary_text = ""
        summary_title = "Meeting Summary"

        try:
            with requests.post(
                f"{BACKEND_URL}/summarize",
                files={"audio": (audio_name, audio_bytes, audio_mime)},
                stream=True,
                timeout=600,
            ) as response:
                response.raise_for_status()

                for raw_line in response.iter_lines():
                    if not raw_line:
                        continue

                    line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                    if not line.startswith("data:"):
                        continue

                    data_str = line[len("data:"):].strip()
                    if not data_str:          # empty "data:" keep-alive line
                        continue

                    try:
                        event = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue             # skip malformed lines silently

                    if event["type"] == "progress":
                        progress.progress(event["value"])
                        status.text(event["status"])

                    elif event["type"] == "token":
                        summary_text += event["value"]
                        summary_box.markdown(
                            f"<div dir='rtl' style='text-align:right'>\n\n{summary_text}\n\n</div>",
                            unsafe_allow_html=True,
                        )

                    elif event["type"] == "done":
                        summary_title = event.get("title", "Meeting Summary")
                        st.session_state.summary_text  = summary_text
                        st.session_state.summary_title = summary_title
                        summary_box.empty()
                        status.empty()
                        progress.empty()

                    elif event["type"] == "error":
                        st.error(f"Error: {event['message']}")
                        break

        except requests.exceptions.ConnectionError:
            st.error(
                f"Cannot connect to the backend at `{BACKEND_URL}`.\n\n"
                "Make sure the FastAPI service is running and `BACKEND_URL` is set correctly."
            )
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ── Show results + actions (persisted across reruns) ──────────────────────────
if st.session_state.summary_text:
    st.success("✅ تم الانتهاء من التلخيص بنجاح!")

    st.markdown(
        "<h3 style='text-align:right;direction:rtl'>📋 الملخص النهائي</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div dir='rtl' style='text-align:right'>\n\n{st.session_state.summary_text}\n\n</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("#### ماذا تريد أن تفعل بالملخص؟")

    col_pdf, col_email = st.columns(2)

    # ── Save as PDF ────────────────────────────────────────────────────────────
    with col_pdf:
        if st.button("📄 حفظ كـ PDF", use_container_width=True):
            with st.spinner("جاري إنشاء ملف PDF..."):
                try:
                    pdf_response = requests.post(
                        f"{BACKEND_URL}/generate-pdf",
                        json={
                            "title":   st.session_state.summary_title,
                            "summary": st.session_state.summary_text,
                        },
                        timeout=60,
                    )
                    if pdf_response.status_code == 200:
                        st.download_button(
                            label="⬇️ تحميل PDF",
                            data=pdf_response.content,
                            file_name=f"{st.session_state.summary_title[:50]}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    else:
                        try:
                            err = pdf_response.json().get("error", "Unknown error")
                        except Exception:
                            err = pdf_response.text or f"HTTP {pdf_response.status_code}"
                        st.error(f"فشل إنشاء PDF: {err}")
                except Exception as e:
                    st.error(f"خطأ: {e}")

    # ── Send via Email ─────────────────────────────────────────────────────────
    with col_email:
        if st.button("📧 إرسال بالبريد الإلكتروني", use_container_width=True):
            st.session_state.show_email_form = True
            st.session_state.email_sent = False

    # ── Email form (shown after clicking the email button) ────────────────────
    if st.session_state.show_email_form and not st.session_state.email_sent:
        with st.container(border=True):
            st.markdown("##### ✉️ أدخل البريد الإلكتروني للمستلم")
            receiver_email = st.text_input(
                "البريد الإلكتروني",
                placeholder="example@email.com",
                label_visibility="collapsed",
            )

            send_col, cancel_col = st.columns([3, 1])
            with send_col:
                if st.button("📤 إرسال", type="primary", use_container_width=True):
                    if not receiver_email or "@" not in receiver_email:
                        st.error("يرجى إدخال بريد إلكتروني صحيح.")
                    else:
                        with st.spinner("جاري إرسال البريد الإلكتروني..."):
                            try:
                                email_resp = requests.post(
                                    f"{BACKEND_URL}/send-email",
                                    json={
                                        "receiver_email": receiver_email,
                                        "title":          st.session_state.summary_title,
                                        "summary":        st.session_state.summary_text,
                                    },
                                    timeout=30,
                                )
                                email_resp.raise_for_status()
                                st.session_state.email_sent      = True
                                st.session_state.show_email_form = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"فشل إرسال البريد الإلكتروني: {e}")

            with cancel_col:
                if st.button("إلغاء", use_container_width=True):
                    st.session_state.show_email_form = False
                    st.rerun()

    if st.session_state.email_sent:
        st.success("✅ تم إرسال الملخص بنجاح إلى بريدك الإلكتروني!")