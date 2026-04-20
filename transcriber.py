import whisperx
import torch
import os
from dotenv import load_dotenv
from whisperx.diarize import DiarizationPipeline

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

device = "cuda" if torch.cuda.is_available() else "cpu"

model = whisperx.load_model("base", device)

def transcribe(audio_path):
    result = model.transcribe(audio_path)

    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"],
        device=device
    )

    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio_path,
        device
    )

    diarize_model = DiarizationPipeline(
        token=hf_token
    )

    diarize_segments = diarize_model(audio_path)

    result = whisperx.assign_word_speakers(diarize_segments, result)

    transcript = ""

    for seg in result["segments"]:
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg["text"]

        transcript += f"{speaker}: {text}\n"

    return transcript
