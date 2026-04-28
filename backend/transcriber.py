import os
import requests
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_URL     = "https://api.deepgram.com/v1/listen"

MIME_MAP = {
    ".wav":  "audio/wav",
    ".mp3":  "audio/mpeg",
    ".m4a":  "audio/mp4",
    ".ogg":  "audio/ogg",
    ".flac": "audio/flac",
    ".webm": "audio/webm",
    ".mp4":  "audio/mp4",
}

MIN_TRANSCRIPT_WORDS = 5


def transcribe(audio_path: str) -> str:
    try:
        if not DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY is not set in your .env file.")

        ext      = os.path.splitext(audio_path)[1].lower()
        mimetype = MIME_MAP.get(ext, "audio/wav")

        with open(audio_path, "rb") as f:
            audio_data = f.read()

        if not audio_data:
            raise ValueError("Audio file is empty.")

        # ── Direct REST call — works regardless of SDK version ────────────────
        response = requests.post(
            DEEPGRAM_URL,
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type":  mimetype,
            },
            params={
                "model":        "nova-3",
                "language":     "ar",
                "smart_format": "true",
                "diarize":      "true",
                "punctuate":    "true",
            },
            data=audio_data,
            timeout=300,
        )
        response.raise_for_status()
        result = response.json()
        # ─────────────────────────────────────────────────────────────────────

        try:
            words = result["results"]["channels"][0]["alternatives"][0]["words"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected Deepgram response structure: {e}\n{result}")

        if not words:
            raise ValueError(
                "Deepgram returned an empty transcript. "
                "The audio may be silent, too short, or in an unsupported format."
            )

        # Group consecutive words by speaker into full sentences
        transcript_lines = []
        current_speaker  = None
        current_words    = []

        for word in words:
            speaker       = word.get("speaker")
            speaker_label = f"SPEAKER_{speaker}" if speaker is not None else "UNKNOWN"
            text          = word.get("punctuated_word", word.get("word", ""))

            if speaker_label != current_speaker:
                if current_words:
                    transcript_lines.append(f"{current_speaker}: {' '.join(current_words)}")
                current_speaker = speaker_label
                current_words   = [text]
            else:
                current_words.append(text)

        if current_words:
            transcript_lines.append(f"{current_speaker}: {' '.join(current_words)}")

        transcript  = "\n".join(transcript_lines)
        total_words = sum(len(line.split()) for line in transcript_lines)

        if total_words < MIN_TRANSCRIPT_WORDS:
            raise ValueError(
                f"Transcript is too short ({total_words} words). "
                "Please check that the audio contains clear speech."
            )

        return transcript

    except Exception as e:
        return f"Error transcribing audio: {e}"