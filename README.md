# 🎥 Meeting Summarizer AI

An AI-powered application that processes meeting videos, automatically generates structured summaries with speaker diarization, and sends them via email.

Built using Python, FastAPI, and Streamlit, utilizing cloud APIs (Deepgram, Groq, Resend) for a lightweight, fast, and scalable architecture with ultra-low memory consumption.

---

## Features

- **Video Support:** Upload meeting recordings in MP4, MOV, or AVI formats.
- **Audio Extraction:** Fast and reliable audio separation using `FFmpeg`.
- **Speaker Diarization:** Highly accurate speech-to-text and speaker identification powered by **Deepgram API** (Nova-2 model).
- **Intelligent Summarization:** Instantly generate structured summaries (key topics, decisions, action items) using **Groq API**.
- **Cloud Email Delivery:** Seamless and reliable email delivery using **Resend API**, completely bypassing traditional SMTP cloud firewalls.
- **Real-Time UI:** Track processing progress step-by-step with a dynamic **Streamlit** interface utilizing Server-Sent Events (SSE).

---

## Project Flow

1. **Upload:** User uploads a video and provides a destination email.
2. **Extract:** Backend (FastAPI) securely extracts the audio track.
3. **Transcribe:** Audio is sent to Deepgram to generate a diarized transcript.
4. **Summarize:** The raw transcript is processed by Groq LLM into a readable, professional summary.
5. **Deliver:** The final summary is formatted and emailed to the user via Resend.

---

## Tech Stack

- **Language:** Python
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **AI Integration:** Deepgram (Speech-to-Text), Groq (LLM)
- **Email Service:** Resend API
- **System Tools:** FFmpeg

---

## Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/EyadYossri/Meeting-Summary.git
cd Meeting-Summary
```

---

## Install dependencies:
```bash
pip install -r requirements.txt
```
(Note: ffmpeg must be installed on your system and added to your system PATH)

---

## Set up Environment Variables:
.env example
```bash
# Deepgram (For Audio Transcription & Diarization)
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# Groq (For LLM Summarization)
GROQ_API_KEY=your_groq_api_key_here

# Resend (For Email Delivery)
RESEND_API_KEY=your_resend_api_key_here

# Backend URL (For Streamlit to connect to FastAPI)
BACKEND_URL=http://localhost:8000
```

# Running the Application
## 1. Start the FastAPI Backend:
```bash
uvicorn main:app --reload
```

## 2. Start the Streamlit Frontend:
```bash
streamlit run app.py
```
