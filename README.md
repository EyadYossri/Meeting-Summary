# 🎥 Meeting Summarizer AI

An AI-powered application that processes meeting videos and automatically generates structured summaries and sends them via email.

Built using Python, Streamlit, Whisper, and LLaMA (via Ollama).

---

## 🚀 Features

- 🎥 Upload meeting video (MP4 / MOV / AVI)
- 🔊 Extract audio using FFmpeg
- 🧠 Transcribe speech using Whisper
- ✍️ Generate structured AI summary using LLaMA 3.1 / Gemma (Ollama)
- 📧 Automatically send summary via email (Gmail SMTP)
- 📊 Real-time progress tracking in Streamlit UI

---

## 🧱 Project Flow

1. Upload video
2. Extract audio
3. Transcribe audio to text
4. Generate AI summary
5. Send email with summary

---

## 🛠️ Tech Stack

- Python
- Streamlit
- OpenAI Whisper
- LLaMA 3.1 (via Ollama)
- FFmpeg
- SMTP (Gmail)

---

## 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/Meeting-Summary.git
cd Meeting-Summary
pip install -r requirements.txt
