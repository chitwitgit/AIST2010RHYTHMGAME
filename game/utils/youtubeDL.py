import os
from pytube import YouTube
import time
import ffmpeg


def download_youtube_audio(url, output_path, output_name):
    # Create the YouTube object
    try:
        video = YouTube(url)
        stream = video.streams.filter(only_audio=True).first()
        stream.download(output_path=output_path)
        output_file_path = os.path.join(output_path, output_name)
        print("Audio downloaded successfully!")

        # Convert the audio to mp3
        ffmpeg.input(os.path.join(output_path, stream.default_filename)).output(output_file_path).run()
        os.remove(os.path.join(output_path, stream.default_filename))
        while not os.path.exists(output_file_path):
            time.sleep(1)
        print(f"{video.title} has been successfully downloaded as an MP3 file.")
    except KeyError:
        print("Unable to fetch video information. Please check the video URL or your network connection.")
