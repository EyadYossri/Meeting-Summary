import os
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

load_dotenv()

API_KEY = os.getenv("DEEPGRAM_API_KEY")

def transcribe(audio_path):
    try:
        deepgram = DeepgramClient(API_KEY)

        with open(audio_path, "rb") as file:
            buffer_data = file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            diarize=True,   
        )

        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

        transcript = ""
        words = response.results.channels[0].alternatives[0].words
        
        for word in words:
            speaker = f"SPEAKER_{word.speaker}" if word.speaker is not None else "UNKNOWN"
            
            text = word.punctuated_word or word.word
            transcript += f"{speaker}: {text}\n"

        return transcript

    except Exception as e:
        return f"Error transcribing audio: {e}"
