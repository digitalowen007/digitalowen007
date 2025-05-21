import yt_dlp
import argparse
import os
from ..utils.logger import setup_logger # Assuming logger.py is in src/utils

# Setup logger for this module
download_logger = setup_logger('yt_downloader', 'youtube_download.log', console_out=True) # console_out for dev

def get_video_info(url, ydl_opts=None):
    """
    Fetches video title, ID, and available formats using yt-dlp.

    Args:
        url: YouTube video URL.
        ydl_opts: Optional yt-dlp options dictionary.

    Returns:
        Dictionary with 'id', 'title', and a list of 'formats', or None if info fetch fails.
    """
    # Use a new YDL opts dict for this function to avoid modifying the global one if passed
    current_ydl_opts = {'quiet': True, 'nocheckcertificate': True} # nocheckcertificate can help with some network issues
    if ydl_opts:
        current_ydl_opts.update(ydl_opts)
    
    try:
        with yt_dlp.YoutubeDL(current_ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            if 'formats' in info:
                for f in info.get('formats', []):
                    formats.append({
                        'resolution': f.get('resolution'), 'ext': f.get('ext'),
                        'format_id': f.get('format_id'), 'fps': f.get('fps'),
                        'vcodec': f.get('vcodec'), 'acodec': f.get('acodec'),
                    })
            return {
                'id': info.get('id'), 'title': info.get('title'),
                'formats': formats, 'original_url': url,
            }
    except yt_dlp.utils.DownloadError as e:
        download_logger.error(f"yt-dlp DownloadError when fetching info for {url}: {e}")
        return None
    except Exception as e:
        download_logger.error(f"Generic error fetching video info for {url}: {e}")
        return None

def download_video(url, output_path, quality_label='best', preferred_format='mp4', 
                   progress_hooks=None, ydl_opts_override=None, max_retries=2, task_id_for_hook=None):
    """
    Downloads a single video from YouTube.

    Args:
        url: YouTube video URL.
        output_path: Directory to save the video.
        quality_label: Desired quality (e.g., '720p', 'best', 'audio_only_mp3', 'audio_only_m4a').
        preferred_format: Preferred video container format (e.g., 'mp4', 'mkv').
                          For audio_only, this is the audio format like 'mp3'.
        progress_hooks: List of functions to call for progress updates.
        ydl_opts_override: Dictionary to override default yt-dlp options.

    Returns:
        Tuple (success_boolean, final_filepath_or_error_message_string)
    """
    video_info = get_video_info(url)
    if not video_info:
        return False, f"Failed to fetch video info for {url}"

    title = video_info.get('title', 'untitled_video')
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    os.makedirs(output_path, exist_ok=True)

    # Initial ydl_opts setup based on arguments
    def _get_initial_ydl_opts(current_quality_label, current_preferred_format, current_output_path_template):
        if current_quality_label.startswith('audio_only'):
            audio_format = current_preferred_format if current_preferred_format in ['mp3', 'm4a', 'ogg'] else 'mp3'
            format_selector = f'bestaudio[ext={audio_format}]/bestaudio'
            postprocessors = [{'key': 'FFmpegExtractAudio', 'preferredcodec': audio_format, 'preferredquality': '192'}]
            merge_format = None
        else:
            height_filter = ""
            if current_quality_label != 'best' and current_quality_label.endswith('p'):
                try:
                    height = int(current_quality_label[:-1])
                    height_filter = f'[height<={height}]'
                except ValueError:
                    download_logger.warning(f"Invalid quality label '{current_quality_label}'. Using 'best'.")
            
            # More robust format selection: try preferred, then webm, then best overall
            format_selector = (
                f'bestvideo{height_filter}[ext={current_preferred_format}]+bestaudio[ext=m4a]'
                f'/bestvideo{height_filter}[ext=webm]+bestaudio[ext=m4a]' # Common fallback
                f'/bestvideo{height_filter}+bestaudio'
                f'/best[ext={current_preferred_format}]'
                f'/best[ext=webm]'
                f'/best'
            )
            if current_quality_label == 'best':
                format_selector = (
                    f'bestvideo[ext={current_preferred_format}]+bestaudio[ext=m4a]'
                    f'/bestvideo[ext=webm]+bestaudio[ext=m4a]'
                    f'/bestvideo+bestaudio'
                    f'/best[ext={current_preferred_format}]'
                    f'/best[ext=webm]'
                    f'/best'
                )
            postprocessors = []
            merge_format = current_preferred_format

        opts = {
            'format': format_selector,
            'outtmpl': current_output_path_template,
            'noplaylist': True,
            'quiet': False, # Capture output for logging/hooks
            'progress_hooks': progress_hooks if progress_hooks else [],
            'merge_output_format': merge_format,
            'postprocessors': postprocessors,
            'add_metadata': True,
            'extract_flat': False,
            'nocheckcertificate': True, # Can help with network issues
            # 'verbose': True, # For extreme debugging
        }
        if ydl_opts_override:
            opts.update(ydl_opts_override)
        return opts

    last_error = None
    for attempt_num in range(max_retries + 1):
        current_ydl_opts = {}
        attempt_message_prefix = f"Attempt {attempt_num + 1}/{max_retries + 1}"

        if attempt_num == 0: # Initial attempt
            filename_template = f"{safe_title}.%(ext)s" # Let yt-dlp determine extension initially
            output_template = os.path.join(output_path, filename_template)
            current_ydl_opts = _get_initial_ydl_opts(quality_label, preferred_format, output_template)
            log_message = f"{attempt_message_prefix}: Downloading {url} as {quality_label} ({preferred_format})"
            download_logger.info(log_message)
            if progress_hooks: # Notify UI of initial attempt
                 for hook in progress_hooks:
                    hook({'status': 'retrying', 'message': log_message, 'id': task_id_for_hook, 'attempt_num': attempt_num + 1, 'max_retries': max_retries +1})

        else: # Retry attempts
            download_logger.warning(f"{attempt_message_prefix}: Previous attempt failed for {url}. Retrying with fallback options...")
            # Fallback: generic mp4, often more compatible
            fallback_preferred_format = 'mp4'
            fallback_quality_label = 'best' # Generic best for fallback
            # Use a slightly different name for fallback attempts to avoid conflicts if partial files exist
            fallback_filename_template = f"{safe_title}_fallback_attempt{attempt_num}.%(ext)s"
            fallback_output_template = os.path.join(output_path, fallback_filename_template)
            
            current_ydl_opts = _get_initial_ydl_opts(fallback_quality_label, fallback_preferred_format, fallback_output_template)
            # Ensure the fallback uses a very common format string
            current_ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            current_ydl_opts['merge_output_format'] = 'mp4' # Explicitly mp4 for this common fallback
            
            log_message = f"{attempt_message_prefix}: Retrying {url} with generic best quality (mp4)."
            download_logger.info(log_message)
            if progress_hooks:
                for hook in progress_hooks:
                    hook({'status': 'retrying', 'message': log_message, 'id': task_id_for_hook, 'attempt_num': attempt_num + 1, 'max_retries': max_retries +1})
        
        try:
            with yt_dlp.YoutubeDL(current_ydl_opts) as ydl:
                ydl.download([url])
            # If download successful, the 'finished' status in progress_hook should have the final filename.
            # For now, we assume the hook handles the final path.
            # If no hooks, we'd need to infer the path.
            # This function's primary role is to manage attempts and return success/failure.
            # The actual final path should ideally come from the 'finished' hook.
            download_logger.info(f"{attempt_message_prefix} for {url} succeeded.")
            # The hook should provide the actual path, but if not, we can construct a probable one.
            # This part is tricky as yt-dlp names files. The hook is the best source.
            # For now, returning a generic success message, actual path is in hook.
            return True, f"Download successful after {attempt_num+1} attempt(s)." 
        except yt_dlp.utils.DownloadError as e:
            last_error = str(e)
            download_logger.error(f"{attempt_message_prefix} failed for {url}: {last_error}")
            # Check for specific error types that shouldn't be retried
            if "Unsupported URL" in last_error or "Video unavailable" in last_error:
                break # No point retrying these
        except Exception as e: # Catch other errors like network issues, ffmpeg errors during postprocessing
            last_error = str(e)
            download_logger.error(f"{attempt_message_prefix} encountered an unexpected error for {url}: {last_error}")
            # If it's a KeyboardInterrupt, don't retry.
            if isinstance(e, KeyboardInterrupt):
                 download_logger.warning(f"Download for {url} cancelled by user.")
                 break

    download_logger.error(f"All {max_retries + 1} attempts failed for {url}. Last error: {last_error}")
    return False, f"All attempts failed. Last error: {last_error}"


def get_playlist_info(playlist_url, ydl_opts=None):
    """
    Fetches info for all videos in a playlist without downloading.

    Args:
        playlist_url: YouTube playlist URL.
        ydl_opts: Optional yt-dlp options.

    Returns:
        A list of dictionaries, each containing 'id', 'title', 'original_url'.
        Returns None if playlist info extraction fails.
    """
    base_ydl_opts = {
        'quiet': True, 'extract_flat': True, 'skip_download': True,
        'nocheckcertificate': True,
    }
    if ydl_opts:
        current_ydl_opts.update(ydl_opts)
    
    videos_info = []
    try:
        with yt_dlp.YoutubeDL(current_ydl_opts) as ydl:
            playlist_dict = ydl.extract_info(playlist_url, download=False)
            if playlist_dict and 'entries' in playlist_dict:
                for entry in playlist_dict['entries']:
                    if entry:
                        videos_info.append({
                            'id': entry.get('id'), 'title': entry.get('title', 'N/A'),
                            'original_url': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                            'playlist_title': playlist_dict.get('title', 'N/A'),
                            'playlist_id': playlist_dict.get('id', 'N/A'),
                        })
            else:
                download_logger.warning(f"No entries found in playlist: {playlist_url}")
                return None
        return videos_info
    except yt_dlp.utils.DownloadError as e:
        download_logger.error(f"yt-dlp DownloadError fetching playlist info for {playlist_url}: {e}")
        return None
    except Exception as e:
        download_logger.error(f"Generic error fetching playlist info for {playlist_url}: {e}")
        return None

def download_playlist(playlist_url, output_path, quality_label='best', preferred_format='mp4', 
                      progress_hooks=None, item_callback=None, max_retries_per_item=2):
    """
    Downloads all videos from a YouTube playlist.

    Args:
        playlist_url: YouTube playlist URL.
        output_path: Directory to save videos.
        quality_label: Desired quality for each video.
        preferred_format: Preferred video format for each video.
        progress_hooks: Progress hooks for individual video downloads.
        item_callback: Function to call for each video item before download attempt.
                       Expected signature: callback(video_info_dict)
                       video_info_dict contains 'id', 'title', 'original_url', etc.
    """
    download_logger.info(f"Fetching playlist info for {playlist_url}...")
    playlist_videos = get_playlist_info(playlist_url)

    if not playlist_videos:
        download_logger.error(f"Could not extract video list from playlist {playlist_url}. Aborting download.")
        return

    playlist_main_title = playlist_videos[0].get('playlist_title', 'youtube_playlist')
    safe_playlist_title = "".join(c for c in playlist_main_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    playlist_specific_output_path = os.path.join(output_path, safe_playlist_title)
    os.makedirs(playlist_specific_output_path, exist_ok=True)

    download_logger.info(f"Processing playlist: {safe_playlist_title} to {playlist_specific_output_path}")

    for i, video_entry in enumerate(playlist_videos):
        video_url = video_entry.get('original_url')
        video_title = video_entry.get('title', f"Video {i+1}")
        video_id = video_entry.get('id', f"playlist_item_{i}_{video_title}") # Unique ID for logging/hooks

        if not video_url:
            download_logger.warning(f"Skipping video {i+1} ('{video_title}') in playlist, no URL found.")
            continue
        
        if item_callback:
            callback_data = {
                'id': video_id, 'title': video_title, 'original_url': video_url,
                'status': 'queued_from_playlist', 'playlist_index': i,
                'quality': quality_label, 'format': preferred_format,
                'output_path': playlist_specific_output_path,
            }
            item_callback(callback_data)
        else: # Direct download (not used by UI, but kept for potential CLI use)
            download_logger.info(f"Downloading video {i+1}/{len(playlist_videos)}: {video_title} ({video_url})")
            # Pass video_id as task_id_for_hook if direct download needs detailed retry logging via hook
            success, msg_or_path = download_video(
                video_url, playlist_specific_output_path, quality_label, preferred_format,
                progress_hooks=progress_hooks, max_retries=max_retries_per_item, task_id_for_hook=video_id
            )
            if success:
                download_logger.info(f"Finished video {i+1}: {msg_or_path}")
            else:
                download_logger.error(f"Failed to download video {i+1} ({video_title}): {msg_or_path}")
    
    if not item_callback:
        download_logger.info(f"Playlist download process finished for: {safe_playlist_title}")
    else:
        download_logger.info(f"Playlist items added to queue for: {safe_playlist_title}")

# Removed old CLI from __main__ as this module is primarily for library use.
# Testing should be done via UI or dedicated test scripts.
    parser.add_argument("--url", help="URL of the single video to download")
    parser.add_argument("--playlist", help="URL of the playlist to download")
    parser.add_argument("--output", required=True, help="Output directory to save files")
    parser.add_argument("--quality", default="best", help="Desired quality (e.g., 720p, 1080p, best)")
    parser.add_argument("--format", default="mp4", help="Preferred video format (e.g., mp4, mkv)")

    args = parser.parse_args()

    if not args.url and not args.playlist:
        parser.error("Either --url or --playlist must be specified.")

    if args.url and args.playlist:
        parser.error("Cannot specify both --url and --playlist. Choose one.")

    if args.url:
        print(f"Attempting to download single video: {args.url}")
        success = download_video(args.url, args.output, args.quality, args.format)
        if success:
            print(f"Single video download process finished.")
        else:
            print(f"Single video download process failed.")
    elif args.playlist:
        print(f"Attempting to download playlist: {args.playlist}")
        download_playlist(args.playlist, args.output, args.quality, args.format)
        print(f"Playlist download process finished.")
