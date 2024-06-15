from pathlib import Path
from PIL import Image
from celery import Celery
from moviepy.editor import VideoFileClip

app = Celery("converter", broker="redis://localhost:6379/0")


@app.task
def convert_movie_to_mp4(filename):
    if not filename:
        return None
    try:
        converted_name = f"converted_{Path(filename).stem}.mp4"
        clip = VideoFileClip(filename)
        clip.write_videofile(
            converted_name,
            codec="libx264",
            ffmpeg_params=[
                "-profile:v",
                "main",
                "-level",
                "3.1",
                "-movflags",
                "faststart",
                "-crf",
                "18",
            ],
            audio_codec="aac",  # Ensure audio codec is set if the input video has audio
            temp_audiofile="temp-audio.m4a",  # Temporary audio file to avoid issues
            remove_temp=True,  # Remove the temporary file after use
            threads=4,  # Number of threads to use for encoding
            preset="medium",  # Preset for encoding speed vs. quality balance
            logger=None,
        )
        return converted_name
    except Exception as e:
        print(e)
        return None


@app.task
def convert2JPG(filename):
    try:
        converted_name = f"converted_{Path(filename).stem}.jpg"
        with Image.open(filename) as im:
            im.save(converted_name, "JPEG")
            return converted_name
    except Exception:
        return None
