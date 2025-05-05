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
                    st.warning(f"Artist and album must be set for `{
