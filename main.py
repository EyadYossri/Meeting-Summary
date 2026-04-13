import os

from audio_extractor import extract_audio
from transcriber import transcribe
from llm_summarizer import generate_summary
from email_sender import send_email


def main():
    video_path = input("Enter video path: ")
    sender_email = input("Enter sender Gmail: ")
    sender_password = input("Enter app password: ")
    receiver_email = input("Enter receiver email: ")

    audio_path = "outputs/audio.mp3"
    os.makedirs("outputs", exist_ok=True)

    print("\n📂 Extracting audio...")
    extract_audio(video_path, audio_path)

    print("\n📝 Transcribing audio...")
    text = transcribe(audio_path)

    print("\n🧠 Generating summary...")
    summary = generate_summary(text, model="llama3.1")

    email_body = f"""
Dear,

I hope you are doing well.

Please find below the summary of the recent meeting:

{summary}

Best regards,
AI Meeting Assistant
"""

    print("\n📧 Sending email...")
    send_email(
        sender_email,
        sender_password,
        receiver_email,
        "Meeting Summary",
        email_body
    )

    print("\n✅ Done! Summary sent successfully.")


if __name__ == "__main__":
    main()