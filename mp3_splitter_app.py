import streamlit as st
import os
import subprocess
import tempfile
from zipfile import ZipFile
from math import floor

st.title("🎵 MP3 Splitter: 3 Files, 30 Tracks")

st.markdown("Upload up to 3 MP3 files and split each into 10 tagged tracks.")

uploaded_files = st.file_uploader("Choose up to 3 MP3 files", type="mp3", accept_multiple_files=True)
artist = st.text_input("Artist Name")
album = st.text_input("Album Title")

if st.button("Split and Download ZIP") and uploaded_files and artist and album:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        def get_duration(path):
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                 "default=noprint_wrappers=1:nokey=1", path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return float(result.stdout.strip())

        track_counter = 1
        for uploaded_file in uploaded_files:
            # Save to temp location
            temp_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            try:
                duration = get_duration(temp_path)
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")
                continue

            segment_duration = floor(duration / 10)
            base_name = os.path.splitext(uploaded_file.name)[0]

            for i in range(1, 11):
                start_time = (i - 1) * segment_duration
                track_number = f"{track_counter:02d}"
                track_title = f"{track_number} - {base_name}"
                output_filename = f"{track_title}.mp3"
                output_path = os.path.join(output_dir, output_filename)

                ffmpeg_cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss", str(start_time),
                    "-t", str(segment_duration),
                    "-i", temp_path,
                    "-id3v2_version", "3",
                    "-metadata", f"artist={artist}",
                    "-metadata", f"album={album}",
                    "-metadata", f"track={track_counter}/30",
                    "-metadata", f"title={track_title}",
                    "-c", "copy",
                    output_path
                ]
                subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                track_counter += 1

        # Zip everything
        zip_path = os.path.join(temp_dir, "split_tracks.zip")
        with ZipFile(zip_path, "w") as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, output_dir)
                    zipf.write(full_path, arcname)

        with open(zip_path, "rb") as f:
            st.download_button("Download ZIP", f, file_name="split_tracks.zip")

