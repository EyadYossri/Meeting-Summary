import subprocess
import os

def extract_audio(video_path, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    command = [
        "ffmpeg",
        "-i", video_path,
        "-q:a", "0",
        "-map", "a",
        output_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("FFmpeg Error:\n", result.stderr)
        raise Exception("Audio extraction failed!")

    if not os.path.exists(output_path):
        raise Exception("Audio file was not created!")

    return output_path