import whisperx
import torch
import os
import gc
import multiprocessing
from dotenv import load_dotenv
from whisperx.diarize import DiarizationPipeline

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"

model = whisperx.load_model("base", device, compute_type=compute_type)

def run_diarization(audio_path, token, dev, return_dict):
    diarize_model = DiarizationPipeline(use_auth_token=token, device=dev)
    segments = diarize_model(audio_path)
    return_dict['segments'] = segments

def transcribe(audio_path):
    batch_size = 16 if device == "cuda" else 4

    result = model.transcribe(audio_path, batch_size=batch_size)
    lang = result["language"]

    model_a, metadata = whisperx.load_align_model(
        language_code=lang, 
        device=device
    )
    
    result = whisperx.align(
        result["segments"],
        model_a,
        metadata,
        audio_path,
        device,
        return_char_alignments=False
    )
    
    del model_a
    gc.collect()

    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    
    p = multiprocessing.Process(
        target=run_diarization, 
        args=(audio_path, hf_token, device, return_dict)
    )
    p.start()
    p.join()
    
    diarize_segments = return_dict['segments']

    result = whisperx.assign_word_speakers(diarize_segments, result)

    transcript = ""
    for seg in result["segments"]:
        speaker = seg.get("speaker", "UNKNOWN")
        text = seg["text"].strip()
        transcript += f"{speaker}: {text}\n"

    return transcript
