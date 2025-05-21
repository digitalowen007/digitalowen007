from PyQt6.QtCore import QThread, pyqtSignal, QObject
from src.downloading import downloader 
import time 
from src.utils.logger import setup_logger # Added

# Setup logger for this module
worker_logger = setup_logger('Workers', 'application.log', console_out=False) # Console out can be noisy for workers

class DownloadWorker(QObject): 
    video_info_signal = pyqtSignal(dict)
    playlist_entry_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal(dict)
    
    def __init__(self, task_id, task_type, url, output_path, quality, video_format, item_id=None):
        super().__init__()
        self.task_id = task_id 
        self.item_id = item_id if item_id else task_id 
        self.task_type = task_type
        self.url = url # Store url for logging
        self.output_path = output_path
        self.quality = quality
        self.video_format = video_format
        self._is_cancelled = False

    def _progress_hook(self, d):
        if self._is_cancelled:
            # worker_logger.debug(f"DownloadWorker (Task ID: {self.task_id}, Item ID: {self.item_id}): Progress hook called but task is cancelled. Raising exception to stop yt-dlp.")
            raise Exception("Download cancelled by user via _progress_hook") 

        if d['status'] == 'retrying':
            # worker_logger.info(f"DownloadWorker (Task ID: {self.task_id}, Item ID: {self.item_id}): Retrying download. Message: {d.get('message')}")
            self.progress_signal.emit({
                'id': d.get('id', self.task_id), 
                'item_id': self.item_id, 'status': 'retrying',
                'message': d.get('message', 'Retrying download...'),
                'attempt_num': d.get('attempt_num'), 'max_retries': d.get('max_retries')
            })
            return 

        if d['status'] == 'downloading':
            percentage = 0
            if d.get('total_bytes') and d.get('total_bytes') > 0:
                percentage = (d.get('downloaded_bytes', 0) / d.get('total_bytes')) * 100
            elif d.get('total_bytes_estimate') and d.get('total_bytes_estimate') > 0:
                percentage = (d.get('downloaded_bytes', 0) / d.get('total_bytes_estimate')) * 100
            
            base_filename = d.get('info_dict', {}).get('filename', d.get('filename', "N/A"))

            self.progress_signal.emit({
                'id': self.task_id, 'item_id': self.item_id,
                'title': d.get('info_dict', {}).get('title', base_filename),
                'percentage': percentage, 'speed': d.get('speed', 'N/A'),
                'eta': d.get('eta', 'N/A'), 'status': 'downloading',
                'total_bytes': d.get('total_bytes') or d.get('total_bytes_estimate'),
                'downloaded_bytes': d.get('downloaded_bytes'),
                '_filename': d.get('filename'),
                '_info_dict_filename': d.get('info_dict', {}).get('filename')
            })
        elif d['status'] == 'finished':
            final_filepath = d.get('info_dict', {}).get('filepath') or d.get('filename')
            self.finished_signal.emit({
                'id': self.task_id, 'item_id': self.item_id,
                'status': 'completed', 'message': 'Download finished successfully.',
                'filepath': final_filepath,
                'title': d.get('info_dict', {}).get('title', "Unknown title")
            })
        elif d['status'] == 'error':
            # This error is from within yt-dlp's processing (e.g., ffmpeg postprocessing error)
            self.finished_signal.emit({
                'id': self.task_id, 'item_id': self.item_id, 'status': 'failed', 
                'message': f"yt-dlp error: {d.get('error', 'Unknown error during processing')}",
                'filepath': None, 'title': d.get('info_dict', {}).get('title', "Unknown title")
            })
            # worker_logger.error(f"DownloadWorker (Task ID: {self.task_id}, Item ID: {self.item_id}): yt-dlp processing error: {d.get('error', 'Unknown')}")


    def run(self):
        worker_logger.info(f"DownloadWorker (Task ID: {self.task_id}, Item ID: {self.item_id}) started for URL: {self.url}, Type: {self.task_type}")
        final_status = "unknown"
        final_message = ""

        try:
            if self.task_type == 'single_video_download':
                success, msg_or_path = downloader.download_video(
                    url=self.url, output_path=self.output_path,
                    quality_label=self.quality, preferred_format=self.video_format,
                    progress_hooks=[self._progress_hook], max_retries=2, 
                    task_id_for_hook=self.task_id 
                )
                if not success and not self._is_cancelled:
                    # This path is hit if download_video itself fails after all retries,
                    # or before starting yt-dlp (e.g. info fetch fails).
                    # The _progress_hook would have handled errors *during* a yt-dlp download attempt.
                    final_status = "failed"
                    final_message = msg_or_path
                    self.finished_signal.emit({
                        'id': self.task_id, 'item_id': self.item_id,
                        'status': final_status, 'message': final_message, 'filepath': None
                    })
                # If success, _progress_hook's 'finished' status handles the signal.
                # If cancelled, the finally block will handle it.
                # If already handled by hook (e.g. yt-dlp internal error), this block might not need to do much more.

            elif self.task_type == 'playlist_info_fetch':
                playlist_items = downloader.get_playlist_info(self.url) 
                if playlist_items:
                    for index, item in enumerate(playlist_items):
                        if self._is_cancelled: break
                        self.playlist_entry_signal.emit({
                            'id': item.get('id', f"playlist_{self.task_id}_item_{index}"),
                            'task_id': f"pl_item_{item.get('id', f'new_{index}')}_{time.time()}",
                            'title': item.get('title', 'N/A'), 'playlist_index': index,
                            'original_url': item.get('original_url'), 'status': 'queued_from_playlist',
                            'playlist_title': item.get('playlist_title', 'Playlist'),
                            'quality': self.quality, 'video_format': self.video_format,
                            'output_path': self.output_path
                        })
                    self.finished_signal.emit({'id': self.task_id, 'item_id': self.item_id, 'status': 'completed', 'message': 'Playlist items fetched.'})
                else:
                    final_status = "completed"; final_message = "Playlist items fetched."
                    self.finished_signal.emit({'id': self.task_id, 'item_id': self.item_id, 'status': final_status, 'message': final_message})
                else:
                    final_status = "failed"; final_message = "Failed to fetch playlist info."
                    self.finished_signal.emit({'id': self.task_id, 'item_id': self.item_id, 'status': final_status, 'message': final_message})
            
            elif self.task_type == 'single_video_info_fetch':
                video_info = downloader.get_video_info(self.url) 
                if video_info:
                    final_status = "info_fetched" # This is a custom status for UI
                    self.video_info_signal.emit({
                        'id': video_info.get('id', self.task_id), 'task_id': self.task_id,
                        'title': video_info.get('title'), 'original_url': self.url,
                        'formats': video_info.get('formats'), 'status': final_status
                    })
                else:
                    final_status = "info_error" # Custom status
                    final_message = f"Failed to fetch video info for {self.url}"
                    self.video_info_signal.emit({
                        'id': self.task_id, 'task_id': self.task_id, 'original_url': self.url,
                        'status': final_status, 'message': final_message
                    })
        except Exception as e:
            final_status = "failed"
            final_message = f"Worker error: {str(e)}"
            worker_logger.error(f"DownloadWorker (Task ID: {self.task_id}, Item ID: {self.item_id}) encountered an unexpected error: {e}", exc_info=True)
            if not self._is_cancelled : # Avoid double signal if error is not due to cancellation itself
                self.finished_signal.emit({
                    'id': self.task_id, 'item_id': self.item_id,
                    'status': final_status, 'message': final_message, 'filepath': None
                })
        finally: 
            if self._is_cancelled:
                 final_status = "cancelled"
                 final_message = "Download cancelled by user."
                 # Check if a 'finished' or 'failed' signal has already been sent by the hook or try-except block
                 # This is tricky. For now, always emit 'cancelled' if flag is set. UI must handle multiple final signals.
                 worker_logger.info(f"DownloadWorker (Task ID: {self.task_id}, Item ID: {self.item_id}) was cancelled by user.")
                 self.finished_signal.emit({
                    'id': self.task_id, 'item_id': self.item_id,
                    'status': final_status, 'message': final_message, 'filepath': None
                })
            worker_logger.info(f"DownloadWorker (Task ID: {self.task_id}, Item ID: {self.item_id}) finished. Final status: {final_status}. Message: {final_message or 'N/A'}")


    def cancel(self):
        worker_logger.info(f"DownloadWorker (Task ID: {self.task_id}, Item ID: {self.item_id}): Cancellation requested.")
        self._is_cancelled = True

# Example of how to use QThread with this QObject based worker
class WorkerThread(QThread):
    def __init__(self, worker_instance, parent=None):
        super().__init__(parent)
        self.worker = worker_instance
        self.worker.moveToThread(self) # Move the worker object to this thread
        self.started.connect(self.worker.run) # Execute run when thread starts
        # Clean up:
        self.worker.finished_signal.connect(self.quit) # Make thread quit when worker is done
        self.worker.finished_signal.connect(self.worker.deleteLater) # Schedule worker for deletion
        self.finished.connect(self.deleteLater) # Schedule thread for deletion

    def request_cancel(self):
        if self.worker:
            self.worker.cancel()

# Example usage (for testing, not part of the final app structure directly here)
if __name__ == '__main__':
    app = QApplication(sys.argv) # Required for QObject based signals even in scripts

    def test_progress(data):
        print(f"Progress: {data}")

    def test_finished(data):
        print(f"Finished: {data}")
        # app.quit() # Quit app after one download for testing

    def test_playlist_entry(data):
        print(f"Playlist Entry: {data}")

    # Test single download
    # worker_obj = DownloadWorker(task_id="test1", task_type='single_video_download', url="https_www_youtube_com/watch?v=dQw4w9WgXcQ", output_path="./temp_downloads", quality="720p", video_format="mp4")
    # thread = WorkerThread(worker_obj)
    # worker_obj.progress_signal.connect(test_progress)
    # worker_obj.finished_signal.connect(test_finished)
    # thread.start()

    # Test playlist info fetch
    playlist_worker_obj = DownloadWorker(task_id="playlist_test_01", task_type='playlist_info_fetch', url="https_www_youtube_com/playlist?list=PLMC9KNkIncKtPzgY-5rmFq7n02kfjANhK", output_path="./temp_playlist_downloads", quality="best", video_format="mp4")
    playlist_thread = WorkerThread(playlist_worker_obj)
    playlist_worker_obj.playlist_entry_signal.connect(test_playlist_entry)
    playlist_worker_obj.finished_signal.connect(test_finished) # Catch overall finish/fail for playlist
    playlist_thread.start()
    
    # sys.exit(app.exec()) # Keep app running if other tests are added below, or manage exit explicitly

# --- Conversion Worker ---
from src.conversion import converter # Assuming converter.py is in src.conversion

class ConversionWorker(QObject):
    conversion_update_signal = pyqtSignal(dict) 
    conversion_finished_signal = pyqtSignal(dict) 

    def __init__(self, task_id, input_filepath, output_filepath, target_format, task_subtype='video', quality_options=None, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.input_filepath = input_filepath # Store for logging
        self.output_filepath = output_filepath
        self.target_format = target_format
        self.task_subtype = task_subtype 
        self.quality_options = quality_options if quality_options else {}
        self._is_cancelled = False

    def _progress_callback_handler(self, progress_data):
        """Handles progress data from converter.convert_video and emits signals."""
        status = progress_data.get('status')
        if self._is_cancelled: 
            # worker_logger.debug(f"ConversionWorker (Task ID: {self.task_id}): Progress callback ignored due to cancellation.")
            return

        if status == 'starting':
            # worker_logger.info(f"ConversionWorker (Task ID: {self.task_id}): Received 'starting' status from converter for {self.input_filepath}.")
            self.conversion_update_signal.emit({
                'id': self.task_id, 'type': self.task_subtype,
                'status_text': progress_data.get('message', f'{self.task_subtype.capitalize()} conversion started...'),
                'progress_value': 0, 
            })
        # Note: ffmpeg-python doesn't easily provide granular progress for convert_video.
        # If it did, those would be emitted here. For now, it's mainly start/finish/error.
    
    def run(self):
        worker_logger.info(f"ConversionWorker (Task ID: {self.task_id}) started for file: {self.input_filepath}, Subtype: {self.task_subtype}, Target: {self.target_format}")
        final_status = "unknown"
        final_message = ""
        output_filepath_on_success = None

        if self._is_cancelled:
            final_status = "cancelled"; final_message = "Conversion cancelled before start."
            self.conversion_finished_signal.emit({'id': self.task_id, 'status': final_status, 'message': final_message, 'output_filepath': None, 'type': self.task_subtype})
            worker_logger.info(f"ConversionWorker (Task ID: {self.task_id}) pre-emptively cancelled. {final_message}")
            return

        self.conversion_update_signal.emit({'id': self.task_id, 'type': self.task_subtype, 'status_text': f"Preparing for {self.task_subtype} conversion to {self.target_format.upper()}...", 'progress_value': None })

        try:
            success = False
            msg_or_path = "An unknown error occurred during conversion worker execution."

            if self.task_subtype == 'image':
                self.conversion_update_signal.emit({'id': self.task_id, 'status_text': 'Converting image...', 'progress_value': None, 'type': self.task_subtype})
                success, msg_or_path = converter.convert_image(self.input_filepath, self.output_filepath, self.target_format)
            elif self.task_subtype == 'document':
                self.conversion_update_signal.emit({'id': self.task_id, 'status_text': 'Converting document...', 'progress_value': None, 'type': self.task_subtype})
                success, msg_or_path = converter.convert_document(self.input_filepath, self.output_filepath, self.target_format)
            elif self.task_subtype in ['video', 'audio']:
                success, msg_or_path = converter.convert_video(self.input_filepath, self.output_filepath, self.target_format, self.quality_options, self._progress_callback_handler)
            else:
                msg_or_path = f"Unsupported conversion subtype: {self.task_subtype}"; success = False
            
            if self._is_cancelled: # Check after potentially long conversion
                final_status = "cancelled"; final_message = "Conversion cancelled during operation."
            elif success:
                final_status = "completed"; final_message = f"Successfully converted to {os.path.basename(msg_or_path)}"; output_filepath_on_success = msg_or_path
            else:
                final_status = "failed"; final_message = msg_or_path
        
        except Exception as e:
            final_status = "failed"; final_message = f"Worker error: {str(e)}"
            worker_logger.error(f"ConversionWorker (Task ID: {self.task_id}) encountered an unexpected error: {e}", exc_info=True)
        
        finally: # Emit final signal
            if self._is_cancelled and final_status != "cancelled": # Ensure cancel status takes precedence if flag is set late
                final_status = "cancelled"; final_message = "Conversion cancelled by user (final check)."
                worker_logger.info(f"ConversionWorker (Task ID: {self.task_id}) was cancelled (final check).")

            self.conversion_finished_signal.emit({
                'id': self.task_id, 'status': final_status, 
                'message': final_message, 'output_filepath': output_filepath_on_success, 
                'type': self.task_subtype
            })
            worker_logger.info(f"ConversionWorker (Task ID: {self.task_id}) finished. Final status: {final_status}. Message: {final_message or 'N/A'}")

    def cancel(self):
        """Requests cancellation of the conversion task."""
        # This is a basic cancellation flag. If ffmpeg is already running via
        # ffmpeg.run (blocking), this flag won't stop it.
        # It's mainly effective if checked before ffmpeg.run starts or if
        # ffmpeg.run_async was used and process handle available.
        print(f"ConversionWorker: Cancel requested for task {self.task_id}")
        self._is_cancelled = True
        # If we had a subprocess handle for ffmpeg, we'd try to terminate it here.
        # self.conversion_update_signal.emit({
        #     'id': self.task_id,
        #     'status_text': 'Cancellation requested...',
        #     'progress_value': None
        # })


if __name__ == '__main__':
    # Keep the existing DownloadWorker test code if needed, or add new tests for ConversionWorker
    app = QApplication(sys.argv)

    # Example Test for ConversionWorker (uncomment to run)
    # def handle_conv_update(data):
    #     print(f"CONV UPDATE: {data}")
    
    # def handle_conv_finished(data):
    #     print(f"CONV FINISHED: {data}")
    #     # app.quit() # Quit after one conversion for testing
    
    # # Create a dummy input file for testing
    # dummy_input_filename = "dummy_input_video.mp4"
    # if not os.path.exists(dummy_input_filename):
    #     try:
    #         # Create a very small, short, valid MP4 file using ffmpeg CLI for testing
    #         # Requires ffmpeg to be in PATH
    #         import subprocess
    #         subprocess.run([
    #             "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=1:size=128x72:rate=10",
    #             "-c:v", "libx264", "-t", "1", dummy_input_filename
    #         ], check=True, capture_output=True)
    #         print(f"Created dummy file: {dummy_input_filename}")
    #     except Exception as e:
    #         print(f"Could not create dummy input file for conversion test: {e}. Please create it manually.")
    #         # sys.exit(1) # Exit if dummy file can't be created
    
    # if os.path.exists(dummy_input_filename):
    #     conv_worker_obj = ConversionWorker(
    #         task_id="conv_test_01",
    #         input_filepath=dummy_input_filename,
    #         output_filepath="./temp_conversions/dummy_output.mp3",
    #         target_format="mp3"
    #     )
    #     conv_thread = WorkerThread(conv_worker_obj) # Reuse WorkerThread
    #     conv_worker_obj.conversion_update_signal.connect(handle_conv_update)
    #     conv_worker_obj.conversion_finished_signal.connect(handle_conv_finished)
    #     conv_thread.start()
    # else:
    #     print(f"Skipping ConversionWorker test as dummy input file '{dummy_input_filename}' was not found/created.")

    # Ensure the app event loop runs for any active tests
    if len(sys.argv) > 1 and sys.argv[1] == 'test_conversion': # crude way to trigger test
        # ... (test setup from above)
        pass # The test code is now part of the main block to avoid unconditional run
    
    # Keep download worker tests if they were there
    # ... test_progress, test_finished, test_playlist_entry ...
    # ... DownloadWorker and playlist_worker_obj setup and start ...
    
    # Only run app.exec() if there's something to test, or manage explicitly
    # For now, assume if __name__ == '__main__', some test might run that needs an event loop.
    sys.exit(app.exec())
