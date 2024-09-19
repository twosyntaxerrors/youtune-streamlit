import os
import cv2
import shutil
import streamlit as st
import numpy as np
from yt_dlp import YoutubeDL
import zipfile

# Function to download the highest quality video from YouTube using yt-dlp
def download_youtube_video(url, output_path):
    ydl_opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        # Download the highest quality video-only format that doesn't require merging
        'format': 'bestvideo[ext=mp4][height<=2160][fps<=60]',
        'noplaylist': True,
        'nocheckcertificate': True,  # Ignore certificate errors
    }
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', None)
            filename = ydl.prepare_filename(info_dict)
            return filename, video_title
    except Exception as e:
        st.error(f"Error downloading video: {e}")
        return None, None

# Function to determine if an image is mostly black or white
def is_black_or_white_frame(frame, threshold=0.95):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    num_pixels = gray_frame.size
    num_black_pixels = np.sum(gray_frame < 30)  # Pixels close to black
    num_white_pixels = np.sum(gray_frame > 225)  # Pixels close to white
    if num_black_pixels / num_pixels > threshold or num_white_pixels / num_pixels > threshold:
        return True
    return False

# Function to extract frames every N frames, skipping black/white frames
def extract_frames(video_path, frame_folder, frame_interval=50):
    if not os.path.exists(frame_folder):
        os.makedirs(frame_folder)

    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    extracted_count = 0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        total_frames = 1  # Avoid division by zero
    progress = st.progress(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            if not is_black_or_white_frame(frame):
                frame_filename = os.path.join(frame_folder, f"frame_{extracted_count:05d}.jpg")
                cv2.imwrite(frame_filename, frame)
                extracted_count += 1
            else:
                st.write(f"Skipping mostly black/white frame at position {frame_count}")
        frame_count += 1
        progress.progress(min(frame_count / total_frames, 1.0))

    cap.release()
    st.success(f"Extracted {extracted_count} frames from the video.")

# Function to display frames and allow user to select frames to include
def display_and_select_frames(frame_folder):
    st.write("### Preview Extracted Frames")
    image_files = sorted(os.listdir(frame_folder))
    selected_frames = []

    # Determine the number of columns based on the number of images
    num_cols = 3  # Adjust as needed
    cols = st.columns(num_cols)

    for idx, img_file in enumerate(image_files):
        col = cols[idx % num_cols]
        img_path = os.path.join(frame_folder, img_file)
        with col:
            # Display the image using the image path
            st.image(img_path, use_column_width=True)
            # Unique key for each checkbox
            include_frame = st.checkbox(f"Include {img_file}", value=True, key=f"checkbox_{img_file}")
            if include_frame:
                selected_frames.append(img_file)
    return selected_frames

# Function to zip the selected frames with trigger word in filenames
def zip_selected_frames(folder_path, output_zip, selected_frames, trigger_word):
    with zipfile.ZipFile(f"{output_zip}.zip", 'w') as zipf:
        for img_file in selected_frames:
            img_path = os.path.join(folder_path, img_file)
            # Generate new filename with trigger word
            name, ext = os.path.splitext(img_file)
            if trigger_word:
                new_name = f"{name}_{trigger_word}{ext}"
            else:
                new_name = img_file
            zipf.write(img_path, arcname=new_name)
    st.success(f"Zipped selected frames: {output_zip}.zip")

# Streamlit app function
def main():
    st.title("YouTube Video Frame Extractor")
    st.markdown("Easily create FLUX training datasets from a YouTube link.")

    # Initialize session state variables
    if 'app_stage' not in st.session_state:
        st.session_state.app_stage = 'input'  # stages: input, extraction, selection
    if 'selected_frames' not in st.session_state:
        st.session_state.selected_frames = []
    if 'youtube_url' not in st.session_state:
        st.session_state.youtube_url = ''
    if 'frame_interval' not in st.session_state:
        st.session_state.frame_interval = 50
    if 'output_path' not in st.session_state:
        st.session_state.output_path = "videos"
    if 'frames_path' not in st.session_state:
        st.session_state.frames_path = "extracted_frames"
    if 'dataset_name' not in st.session_state:
        st.session_state.dataset_name = "frames_dataset"
    if 'trigger_word' not in st.session_state:
        st.session_state.trigger_word = ""

    if st.session_state.app_stage == 'input':
        youtube_url = st.text_input("Paste the YouTube URL:")
        frame_interval = st.number_input("Frame Extraction Interval", min_value=1, value=50, step=1)
        dataset_name = st.text_input("Dataset Name", value="frames_dataset")
        trigger_word = st.text_input("Trigger Word / Unique Identifier (optional)")
        extract_button = st.button("Extract Frames")

        if extract_button and youtube_url:
            st.session_state.youtube_url = youtube_url
            st.session_state.frame_interval = frame_interval
            st.session_state.dataset_name = dataset_name
            st.session_state.trigger_word = trigger_word
            st.session_state.app_stage = 'extraction'

    if st.session_state.app_stage == 'extraction':
        # Step 1: Download YouTube video
        with st.spinner('Downloading video...'):
            video_path, video_title = download_youtube_video(st.session_state.youtube_url, st.session_state.output_path)

        if video_path:
            st.success(f"Downloaded video: {video_title}")

            # Store video_path for later deletion
            st.session_state.video_path = video_path

            # Step 2: Extract frames from the video
            with st.spinner('Extracting frames...'):
                extract_frames(video_path, st.session_state.frames_path, st.session_state.frame_interval)

            # Step 3: Delete the downloaded video file
            try:
                os.remove(video_path)
                st.info(f"Deleted downloaded video file: {video_path}")
            except Exception as e:
                st.warning(f"Could not delete video file: {e}")

            st.session_state.app_stage = 'selection'

    if st.session_state.app_stage == 'selection':
        st.write("## Select Frames to Include in the Dataset")
        selected_frames = display_and_select_frames(st.session_state.frames_path)
        st.session_state.selected_frames = selected_frames

        proceed = st.button("Proceed to Download")

        if proceed:
            if not st.session_state.selected_frames:
                st.error("No frames selected. Please select at least one frame.")
            else:
                # Step 4: Zip the selected frames
                with st.spinner('Zipping selected frames...'):
                    zip_selected_frames(
                        st.session_state.frames_path,
                        st.session_state.dataset_name,
                        st.session_state.selected_frames,
                        st.session_state.trigger_word
                    )

                # Step 5: Provide a download button for the zip file
                with open(f"{st.session_state.dataset_name}.zip", "rb") as f:
                    st.download_button(
                        label="Download Zip",
                        data=f,
                        file_name=f"{st.session_state.dataset_name}.zip",
                        mime="application/zip"
                    )

                # Optionally, reset the app state
                st.session_state.app_stage = 'input'

                # Optionally, clean up frames directory
                try:
                    shutil.rmtree(st.session_state.frames_path)
                    st.info(f"Deleted frames directory: {st.session_state.frames_path}")
                except Exception as e:
                    st.warning(f"Could not delete frames directory: {e}")

                # Optionally, clean up other directories
                if os.path.exists(st.session_state.output_path):
                    try:
                        shutil.rmtree(st.session_state.output_path)
                    except Exception as e:
                        st.warning(f"Could not delete videos directory: {e}")

    # Clean up any residual directories when the app restarts
    if st.session_state.app_stage == 'input':
        if os.path.exists(st.session_state.frames_path):
            try:
                shutil.rmtree(st.session_state.frames_path)
            except Exception as e:
                st.warning(f"Could not delete frames directory: {e}")
        if os.path.exists(st.session_state.output_path):
            try:
                shutil.rmtree(st.session_state.output_path)
            except Exception as e:
                st.warning(f"Could not delete videos directory: {e}")

if __name__ == "__main__":
    main()
