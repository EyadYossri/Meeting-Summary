import subprocess
import os


def extract_audio(video_path, output_path="outputs/audio.wav"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
<<<<<<< HEAD
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-threads", "0",
        "-af", "silenceremove=1:0:-50dB",
=======
        "-acodec", "pcm_s16le",  # WAV codec
        "-ar", "16000",          # Whisper/WhisperX optimal
        "-ac", "1",              # mono audio
>>>>>>> ab7e773 (update requirements)
        output_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"FFmpeg Error:\n{result.stderr}")

    if not os.path.exists(output_path):
        raise Exception("Audio file was not created!")

    return output_path
