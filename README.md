# VersaDownloader & Converter

VersaDownloader & Converter is a user-friendly desktop application designed to help you download videos (primarily from YouTube) and convert them to various formats. It also serves as a general-purpose file converter for common audio, video, image, and document types.

## Features

*   **YouTube Video Downloading:**
    *   Download individual YouTube videos.
    *   Download entire YouTube playlists.
    *   Select preferred video/audio quality and format (e.g., MP4, MKV, WebM, MP3, M4A).
    *   Advanced error handling with automatic retries and fallback strategies for downloads.
*   **File Conversion:**
    *   **Video:** Convert local video files to various formats (e.g., AVI, MOV, MKV, MP4). Extract audio to MP3, AAC, WAV, etc.
    *   **Audio:** Convert local audio files between formats (e.g., WAV to MP3, MP3 to AAC).
    *   **Image:** Convert images between JPG, PNG, and WEBP formats.
    *   **Document:** Convert DOCX and TXT files to PDF.
*   **User Interface & Experience:**
    *   Clear, tabbed interface for "Video Downloader" and "File Converter".
    *   Real-time status table showing progress, speed, ETA, and status for all operations.
    *   Concurrent downloads and conversions to maximize efficiency.
    *   Customizable settings:
        *   Default download and conversion output directories.
        *   Adjustable number of concurrent downloads and conversions.
        *   Option to auto-clear completed tasks from the list.
        *   Switchable Light and Dark themes.
    *   System notifications for batch completion of downloads or conversions.
*   **Logging:** Detailed logs for application behavior, downloads, and conversions, stored in the `logs/` directory for troubleshooting.

## Requirements (for Running from Source)

To run VersaDownloader & Converter from source, you'll need:

1.  **Python 3.7+**
2.  **FFmpeg:**
    *   Required for all video and audio downloading (post-processing) and conversion tasks.
    *   You must install FFmpeg separately and ensure that the `ffmpeg` (and `ffprobe`) executables are in your system's PATH.
    *   Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).
3.  **Pandoc:**
    *   Required for DOCX to PDF and TXT to PDF document conversions.
    *   You must install Pandoc separately and ensure its executable is in your system's PATH.
    *   Download Pandoc from [pandoc.org](https://pandoc.org/installing.html).
4.  **Python Dependencies:**
    *   Install all required Python packages using pip:
        ```bash
        pip install -r requirements.txt
        ```

## How to Run (from Source)

1.  Ensure all requirements listed above are met (Python, FFmpeg, Pandoc, pip packages).
2.  Navigate to the project's root directory in your terminal.
3.  Run the application using:
    ```bash
    python src/main.py
    ```

## Basic Usage Guide

### Video Downloader Tab
1.  **Enter URL:** Paste a YouTube video or playlist URL into the "YouTube URL" field.
2.  **Select Quality & Format:** Choose your desired download quality (e.g., 1080p, Best, Audio Only) and container format (e.g., MP4, MKV for video; MP3, M4A for audio).
3.  **Choose Output Directory:** Click "Browse..." to select the folder where your downloads will be saved.
4.  **Add to Queue:** Click "Add to Queue". For playlists, individual videos will be added to the queue.
5.  **Start Downloads:** Click "Start Downloads" to begin processing the queue.

### File Converter Tab
1.  **Add Files:** Click "Add Files..." and select one or more video, audio, image, or document files you want to convert.
2.  **Select Target Format:** Choose the desired output format from the "Target Format" dropdown (e.g., AVI, MP3, PNG, PDF).
3.  **Choose Output Directory:** Click "Browse..." to select the folder for your converted files.
4.  **Start Conversion:** Click "Start All Conversions" to begin processing.

### Settings
Access application settings via the **File > Settings** menu. Here you can configure default directories, concurrency limits, auto-clear behavior, and the application theme.

## Logging
The application maintains logs that can be helpful for troubleshooting:
*   `logs/application.log`: General application events, UI interactions, and errors.
*   `logs/youtube_download.log`: Detailed logs for YouTube download operations, including retries and errors.
*   `logs/conversion.log`: Detailed logs for file conversion operations.

## Building a Standalone Executable
For instructions on how to package VersaDownloader & Converter into a standalone executable for easier distribution, please see `BUILD_INSTRUCTIONS.md`.

## Known Issues & Limitations
*   **HEIC/HEIF Image Conversion:** While `.heic`/`.heif` files might be selectable, conversion from these formats often depends on system libraries like `libheif` being installed, which is not handled by this application. Basic support via `pillow-heif` is included, but its success can vary.
*   **PDF to DOCX/Editable Format:** Conversion *from* PDF to editable formats like DOCX is not supported due to its complexity.
*   **Real-time Conversion Progress:** Detailed percentage progress for video/audio conversions is not currently available; progress is shown as "Converting..." until completion.
*   **External Dependencies:** As mentioned, FFmpeg and Pandoc are essential for core functionalities and must be installed by the user if running from source or if they are not bundled with a packaged version.
```
