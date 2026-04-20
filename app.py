import streamlit as st
import os

from audio_extractor import extract_audio
from transcriber import transcribe
from llm_summarizer import generate_summary
from email_sender import send_email

st.title("🎥 Meeting Summarizer AI")

uploaded_file = st.file_uploader("Upload Meeting Video", type=["mp4", "mov", "avi"])

sender_email = st.text_input("Enter sender Gmail:")
sender_password = st.text_input("Enter app password:", type="password")
receiver_email = st.text_input("Enter receiver email:")

if st.button("Start Summarization"):

    if uploaded_file is None:
        st.error("Please upload a video file")
    else:
        progress = st.progress(0)
        status = st.empty()

        status.text("Saving video...")
        os.makedirs("uploads", exist_ok=True)

        video_path = os.path.join("uploads", uploaded_file.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_file.read())

        progress.progress(20)

        status.text("Extracting audio...")
        audio_path = "outputs/audio.wav"
        os.makedirs("outputs", exist_ok=True)

        extract_audio(video_path, audio_path)

        progress.progress(40)

        status.text("Transcribing audio...")
        text = transcribe(audio_path)

        progress.progress(70)

        status.text("Generating summary...")
        summary = generate_summary(text, model="llama3.1")

        progress.progress(85)

        status.text("Sending email...")

        email_body = f"""
Dear,

I hope you are doing well.

Please find below the summary of the recent meeting:
{summary}

Best regards,
AI Meeting Assistant
"""

        send_email(
            sender_email,
            sender_password,
            receiver_email,
            "Meeting Summary",
            email_body
        )

        progress.progress(100)
        status.text("Done!")

        st.success("Process completed successfully!")
