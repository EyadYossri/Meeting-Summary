import whisperx
import torch
import os
from dotenv import load_dotenv
from whisperx.diarize import DiarizationPipeline

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

device = "cuda" if torch.cuda.is_available() else "cpu"

compute_type = "float16" if device == "cuda" else "int8"

model = whisperx.load_model("base", device, compute_type=compute_type)

_align_model_cache = {}

_diarize_model = DiarizationPipeline(token=hf_token, device=device)


def transcribe(audio_path):
    batch_size = 16 if device == "cuda" else 4

    result = model.transcribe(audio_path, batch_size=batch_size)

    lang = result["language"]

    if lang not in _align_model_cache:
        model_a, metadata = whisperx.load_align_model(
            language_code=lang,
            device=device
        )
        _align_model_cache[lang] = (model_a, metadata)
    else:
        model_a, metadata = _align_model_cache[lang]

    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio_path,
        device,
        return_char_alignments=False
    )

    diarize_segments = _diarize_model(audio_path)

    result = whisperx.assign_word_speakers(diarize_segments, result)

    transcript = ""
    for seg in result["segments"]:
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg["text"].strip()
        transcript += f"{speaker}: {text}\n"

    return transcript