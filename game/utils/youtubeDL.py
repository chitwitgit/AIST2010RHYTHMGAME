import os
from pytube import YouTube
import subprocess
import time


def download_youtube_audio(url, output_path, output_name):
    # Create the YouTube object
    try:
        video = YouTube(url)
        stream = video.streams.filter(only_audio=True).first()
        stream.download(output_path=output_path)
        output_file_path = os.path.join(output_path, output_name)
        print("Audio downloaded successfully!")

        # Convert the audio to mp3
        subprocess.run(["ffmpeg", "-i", os.path.join(output_path, stream.default_filename), output_file_path])
        os.remove(os.path.join(output_path, stream.default_filename))
        print(f"{video.title} has been successfully downloaded as an MP3 file.")
    except KeyError:
        print("Unable to fetch video information. Please check the video URL or your network connection.")