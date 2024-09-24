# YouTube Video Frame Extractor

This Streamlit application allows users to easily create FLUX training datasets from YouTube videos by extracting high quality frames.

![Application Interface](app_interface.png)

## Features

- Download YouTube videos using a provided URL
- Extract frames from the video at specified intervals
- Skip mostly black or white frames
- Preview and select extracted frames
- Add optional trigger words to frame filenames
- Generate a zip file of selected frames for download

## How it works

1. User enters a YouTube video URL and sets extraction parameters
2. The app downloads the video and extracts frames at specified intervals
3. Extracted frames are displayed for user selection
4. Selected frames are zipped with optional trigger words in filenames
5. User can download the resulting dataset

## Requirements

- Python 3.7+
- Streamlit
- OpenCV (cv2)
- yt-dlp
- NumPy

## Usage

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```
   streamlit run streamlit-youtune.py
   ```
4. Enter a YouTube URL, set parameters, and follow the on-screen instructions

## Note

Ensure you comply with YouTube's terms of service and respect content creators' rights when using this tool. The app is designed for educational and fair use purposes only.
