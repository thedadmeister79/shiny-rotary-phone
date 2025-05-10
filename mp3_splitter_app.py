import streamlit as st
import os
import subprocess
import tempfile
from zipfile import ZipFile
from math import floor

st.title("🎵 MP3 Splitter: Custom Track Count per File")

st.markdown("Upload MP3 files, set artist/album names individually, and choose how many tracks each file should be split into.")

uploaded_files = st.file_uploader("Upload MP3 files", type="mp3", accept_multiple_files=True)

if uploaded_files:
    file_configs = []
    for idx, uploaded_file in enumerate(uploaded_files):
        st.subheader(f"🎧 File {idx + 1}: `{uploaded_file.name}`")
        artist = st.text_input(f"Artist for `{uploaded_file.name}`", key=f"artist_{idx}")
        album = st.text_input(f"Album for `{uploaded_file.name}`", key=f"album_{idx}")
        track_count = st.number_input(f"Number of tracks to split `{uploaded_file.name}` into", min_value=1, max_value=50, value=10, step=1, key=f"tracks_{idx}")
        file_configs.append({
            "file": uploaded_file,
            "artist": artist,
            "album": album,
            "track_count": track_count
        })

    if st.button("🎬 Split and Download ZIP"):
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
            for config in file_configs:
                uploaded_file = config["file"]
                artist = config["artist"]
                album = config["album"]
                track_count = config["track_count"]

                if not artist or not album:
                    st.warning(f"Artist and album must be set for `{uploaded_file.name}`")
                    continue

                # Save uploaded file to temp path
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                try:
                    duration = get_duration(temp_path)
                except Exception as e:
                    st.error(f"Could not process {uploaded_file.name}: {e}")
                    continue

                segment_duration = floor(duration / track_count)
                base_name = os.path.splitext(uploaded_file.name)[0]

                for i in range(1, track_count + 1):
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
                        "-metadata", f"track={track_counter}",
                        "-metadata", f"title={track_title}",
                        "-c", "copy",
                        output_path
                    ]
                    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    track_counter += 1

            # Zip and download
            zip_path = os.path.join(temp_dir, "split_tracks.zip")
            with ZipFile(zip_path, "w") as zipf:
                for root, _, files in os.walk(output_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        arcname = os.path.relpath(full_path, output_dir)
                        zipf.write(full_path, arcname)

            with open(zip_path, "rb") as f:
                st.success("✅ Done! Download your ZIP below.")
                st.download_button("📥 Download ZIP", f, file_name="split_tracks.zip")
