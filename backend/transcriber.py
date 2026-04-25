import os
from dotenv import load_dotenv
from deepgram import DeepgramClient

load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY")

def transcribe(audio_path):
    try:
        deepgram = DeepgramClient(API_KEY)

        with open(audio_path, "rb") as file:
            buffer_data = file.read()

        response = deepgram.listen.v1.media.transcribe_file(
            request=buffer_data,
            model="nova-3",
            smart_format=True, 
            diarize=True      
        )

        transcript = ""
        words = response.results.channels[0].alternatives[0].words
        
        for word in words:
            speaker = getattr(word, "speaker", None)
            speaker_label = f"SPEAKER_{speaker}" if speaker is not None else "UNKNOWN"
            
            text = getattr(word, "punctuated_word", getattr(word, "word", ""))
            transcript += f"{speaker_label}: {text}\n"

        return transcript

    except Exception as e:
        return f"Error transcribing audio: {e}"
