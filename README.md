# 🎥 Meeting Summarizer AI

An AI-powered application that processes meeting videos, automatically generates structured summaries with speaker diarization, and sends them via email.

Built using Python, Streamlit, WhisperX, and LLaMA (via Ollama).

---

## Features

- Upload meeting video (MP4 / MOV / AVI)
- Extract audio to WAV format using FFmpeg
- Transcribe speech and identify speakers (diarization) using WhisperX
- Generate structured AI summary using LLaMA 3.1 / Gemma (Ollama)
- Automatically send summary via email (Gmail SMTP)
- Real-time progress tracking in Streamlit UI

---

## Project Flow

1. Upload video
2. Extract audio
3. Transcribe audio and perform speaker diarization
4. Generate AI summary
5. Send email with summary

---

## Tech Stack

- Python
- Streamlit
- WhisperX (Transcription & Diarization)
- LLaMA 3.1 (via Ollama)
- FFmpeg
- SMTP (Gmail)

---

## Installation

```bash
git clone https://github.com/EyadYossri/Meeting-Summary.git
cd Meeting-Summary
pip install -r requirements.txt
```

---

## Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Set up Environment Variables:
.env example
```bash
HF_TOKEN=your_hugging_face_token_here

