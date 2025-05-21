from PIL import Image, UnidentifiedImageError
import ffmpeg
import argparse
import os
import sys
import json
import docx # from python-docx - typically not used directly for conversion to PDF with pypandoc
import pypandoc # For document conversion

def get_media_info(input_file_path):
    """
    Fetches media information using ffmpeg.probe.

    Args:
        input_file_path: Path to a media file.

    Returns:
        A dictionary containing media properties, or None if probing fails.
    """
    if not os.path.exists(input_file_path):
        print(f"Error: Input file not found: {input_file_path}", file=sys.stderr)
        return None
    try:
        print(f"Probing file: {input_file_path}")
        info = ffmpeg.probe(input_file_path)
        print("Probe successful.")
        return info
    except ffmpeg.Error as e:
        error_message = e.stderr.decode('utf8').strip() if e.stderr else "Unknown ffmpeg error"
        print(f"Error probing file {input_file_path}: {error_message}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred while probing {input_file_path}: {e}", file=sys.stderr)
        return None

def convert_video(input_file_path, output_file_path, target_format_extension, quality_options=None, progress_callback=None):
    """
    Converts a media file to a target format using ffmpeg-python.
    (Implementation from previous step - assumed to be correct and complete)
    """
    if not os.path.exists(input_file_path):
        return False, f"Error: Input file not found: {input_file_path}"

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    print(f"Starting video/audio conversion: {input_file_path} -> {output_file_path}")

    default_options = {
        'video_codec': 'libx264', 'crf': 23, 'audio_codec': 'aac',
        'audio_bitrate': '192k', 'preset': 'medium',
    }
    audio_only_formats = ["mp3", "aac", "wav", "flac", "ogg", "m4a"]
    is_audio_output = target_format_extension.lower() in audio_only_formats

    current_options = default_options.copy()
    if quality_options:
        current_options.update(quality_options)

    stream = ffmpeg.input(input_file_path)
    output_params = {}

    try:
        if is_audio_output:
            output_params['audio_codec'] = current_options.get('audio_codec', 'aac')
            if current_options.get('audio_bitrate'):
                output_params['audio_bitrate'] = current_options['audio_bitrate']
            stream = stream.audio
        else:
            output_params['vcodec'] = current_options.get('video_codec', 'libx264')
            if current_options.get('crf') is not None and output_params['vcodec'] in ['libx264', 'libx265']:
                output_params['crf'] = current_options['crf']
            if current_options.get('video_bitrate'):
                output_params['video_bitrate'] = current_options['video_bitrate']
            if current_options.get('preset') and output_params['vcodec'] in ['libx264', 'libx265']:
                 output_params['preset'] = current_options['preset']
            output_params['acodec'] = current_options.get('audio_codec', 'aac')
            if current_options.get('audio_bitrate'):
                output_params['audio_bitrate'] = current_options['audio_bitrate']
        
        output_params['format'] = target_format_extension

        stream = ffmpeg.output(stream, output_file_path, **output_params)
        
        if progress_callback:
            progress_callback({'status': 'starting', 'input': input_file_path, 'output': output_file_path, 'message': 'Video conversion starting...'})

        process = ffmpeg.run_async(stream, pipe_stdout=True, pipe_stderr=True, overwrite_output=True)
        out, err = process.communicate()

        if process.returncode != 0:
            error_message = err.decode('utf8').strip()
            if progress_callback:
                progress_callback({'status': 'error', 'message': error_message})
            return False, f"FFmpeg error: {error_message}"

        if progress_callback:
            progress_callback({'status': 'finished', 'filepath': output_file_path, 'message': 'Video conversion finished.'})
        return True, output_file_path

    except ffmpeg.Error as e:
        error_message = e.stderr.decode('utf8').strip() if e.stderr else "Unknown ffmpeg error during setup"
        if progress_callback:
            progress_callback({'status': 'error', 'message': error_message})
        return False, f"FFmpeg setup error: {error_message}"
    except Exception as e:
        if progress_callback:
            progress_callback({'status': 'error', 'message': str(e)})
        return False, f"Unexpected error: {str(e)}"

# --- Image Conversion ---
def convert_image(input_file_path, output_file_path, target_format_extension):
    """
    Converts an image file to a target format using Pillow.
    """
    if not os.path.exists(input_file_path):
        print(f"Error: Input image file not found: {input_file_path}", file=sys.stderr)
        return False, f"Error: Input image file not found: {input_file_path}"

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    print(f"Starting image conversion: {input_file_path} -> {output_file_path}")

    try:
        img = Image.open(input_file_path)
        
        save_format = target_format_extension.upper()
        if save_format == "JPG":  # Pillow expects JPEG for .jpg files
            save_format = "JPEG" 
            # Handle transparency for JPEG conversion
            if img.mode == 'RGBA' or (img.mode == 'P' and 'transparency' in img.info):
                print(f"Converting image from {img.mode} to RGB for JPEG output.")
                img = img.convert('RGB')
        elif save_format == "WEBP":
            # WEBP supports RGBA, so no special handling needed for transparency by default
            pass
        elif save_format == "PNG":
            # PNG supports RGBA
            pass
        
        img.save(output_file_path, format=save_format)
        print(f"Image conversion successful: {output_file_path}")
        return True, output_file_path

    except FileNotFoundError:
        print(f"Error: Input image file disappeared: {input_file_path}", file=sys.stderr)
        return False, f"Error: Input image file disappeared: {input_file_path}"
    except UnidentifiedImageError:
        print(f"Error: Cannot identify image file (corrupt or unsupported): {input_file_path}", file=sys.stderr)
        return False, f"Error: Cannot identify image file (corrupt or unsupported): {input_file_path}"
    except IOError as e:
        print(f"Error during image processing (I/O) for {input_file_path}: {e}", file=sys.stderr)
        return False, f"Error during image processing (I/O): {str(e)}"
    except Exception as e:
        print(f"An unexpected error occurred during image conversion of {input_file_path}: {e}", file=sys.stderr)
        return False, f"Unexpected error during image conversion: {str(e)}"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Media Converter CLI (Video/Audio/Image)")
    
    # Video/Audio specific arguments
    parser.add_argument("--input", help="Input video/audio file path")
    parser.add_argument("--output", help="Output video/audio file path")
    parser.add_argument("--format", help="Target video/audio format extension (e.g., mp4, mp3)")
    parser.add_argument("--vcodec", help="Video codec")
    parser.add_argument("--acodec", help="Audio codec")
    parser.add_argument("--vb", help="Video bitrate")
    parser.add_argument("--ab", help="Audio bitrate")
    parser.add_argument("--crf", help="Constant Rate Factor for x264/x265")
    parser.add_argument("--preset", help="x264/x265 preset")
    parser.add_argument("--info", action="store_true", help="Display media info for the video/audio input file and exit.")

    # Image specific arguments
    parser.add_argument("--image_input", help="Input image file path")
    parser.add_argument("--image_output", help="Output image file path")
    parser.add_argument("--image_format", help="Target image format (e.g., png, jpg, webp)")

    args = parser.parse_args()

    action_taken = False

    if args.info and args.input:
        print(f"Fetching media information for: {args.input}")
        media_info = get_media_info(args.input)
        if media_info:
            print(json.dumps(media_info, indent=4))
        else:
            print("Failed to retrieve media information.")
        action_taken = True
    elif args.input and args.output: # Video/Audio conversion
        target_format_ext = args.format
        if not target_format_ext:
            _, target_format_ext = os.path.splitext(args.output)
            if target_format_ext.startswith('.'): target_format_ext = target_format_ext[1:]
        
        if not target_format_ext:
            parser.error("Target video/audio format could not be determined. Use --format or ensure output file has an extension.")
        
        quality_opts = {k: v for k, v in vars(args).items() if v is not None and k in ['vcodec', 'acodec', 'vb', 'ab', 'crf', 'preset']}
        if 'crf' in quality_opts: quality_opts['crf'] = int(quality_opts['crf'])

        def cli_progress(data): print(f"PROGRESS: {data}")
        
        success, message = convert_video(args.input, args.output, target_format_ext.lower(), quality_opts, cli_progress)
        if success: print(f"CLI: Video/Audio conversion success: {message}")
        else: print(f"CLI: Video/Audio conversion failure: {message}", file=sys.stderr); sys.exit(1)
        action_taken = True

    if args.image_input and args.image_output and args.image_format:
        print(f"\nAttempting image conversion:")
        img_success, img_message = convert_image(args.image_input, args.image_output, args.image_format.lower())
        if img_success: print(f"CLI: Image conversion success: {img_message}")
        else: print(f"CLI: Image conversion failure: {img_message}", file=sys.stderr); sys.exit(1)
        action_taken = True
    
    if not action_taken:
        if (args.image_input or args.image_output or args.image_format): # if some image args but not all
             print("Error: For image conversion, --image_input, --image_output, and --image_format are all required.", file=sys.stderr)
             sys.exit(1)
        elif (args.input or args.output): # if some video args but not all (and not info)
             print("Error: For video/audio conversion, --input and --output are required.", file=sys.stderr)
             sys.exit(1)
        else: # No valid set of arguments provided
            parser.print_help()
        sys.exit(0) # Exit if no action was taken, or after an action if not exited already.

# --- Document Conversion ---
def convert_document(input_file_path, output_file_path, target_format_extension):
    """
    Converts a document file (DOCX or TXT) to PDF using pypandoc.
    """
    if not os.path.exists(input_file_path):
        return False, f"Error: Input document file not found: {input_file_path}"

    if target_format_extension.lower() != 'pdf':
        return False, f"Error: Target format for documents must be 'pdf'. Got '{target_format_extension}'."

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    print(f"Starting document conversion: {input_file_path} -> {output_file_path}")

    input_ext = os.path.splitext(input_file_path)[1].lower()

    try:
        if input_ext == '.docx' or input_ext == '.txt':
            pypandoc.convert_file(input_file_path, 'pdf', outputfile=output_file_path)
            print(f"Document conversion successful: {output_file_path}")
            return True, output_file_path
        else:
            return False, f"Unsupported document conversion type: {input_ext}"
    except RuntimeError as e:
        # This is often where Pandoc not being found is caught.
        err_str = str(e)
        if "pandoc" in err_str.lower() and ("not found" in err_str.lower() or "isn't available" in err_str.lower() or "No such file" in err_str.lower()):
            pandoc_missing_msg = "Error: Pandoc is not installed or not found in PATH. pypandoc requires Pandoc to function."
            print(pandoc_missing_msg, file=sys.stderr)
            return False, pandoc_missing_msg
        else:
            print(f"An unexpected runtime error occurred during document conversion: {e}", file=sys.stderr)
            return False, f"Unexpected runtime error: {str(e)}"
    except Exception as e:
        print(f"An unexpected error occurred during document conversion of {input_file_path}: {e}", file=sys.stderr)
        return False, f"Unexpected error during document conversion: {str(e)}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Media and Document Converter CLI")
    
    # ... (Existing video/audio args) ...
    parser.add_argument("--input", help="Input video/audio file path")
    parser.add_argument("--output", help="Output video/audio file path")
    parser.add_argument("--format", help="Target video/audio format extension (e.g., mp4, mp3)")
    # ... (vcodec, acodec, etc.) ...
    parser.add_argument("--info", action="store_true", help="Display media info for the video/audio input file and exit.")

    # ... (Existing image args) ...
    parser.add_argument("--image_input", help="Input image file path")
    parser.add_argument("--image_output", help="Output image file path")
    parser.add_argument("--image_format", help="Target image format (e.g., png, jpg, webp)")

    # Document conversion arguments
    parser.add_argument("--doc_input", help="Input document file path (docx, txt)")
    parser.add_argument("--doc_output", help="Output PDF file path for document conversion")
    # --doc_format is implicitly 'pdf'

    args = parser.parse_args()
    action_taken = False

    # ... (Existing info, video/audio, image conversion logic from previous state) ...
    if args.info and args.input:
        # ... (info logic) ...
        action_taken = True
    elif args.input and args.output: 
        # ... (video/audio conversion logic) ...
        action_taken = True

    if args.image_input and args.image_output and args.image_format:
        # ... (image conversion logic) ...
        action_taken = True
    
    # Handle Document Conversion
    if args.doc_input and args.doc_output:
        print(f"\nAttempting document conversion:")
        doc_success, doc_message = convert_document(args.doc_input, args.doc_output, "pdf")
        if doc_success:
            print(f"CLI: Document conversion success: {doc_message}")
        else:
            print(f"CLI: Document conversion failure: {doc_message}", file=sys.stderr)
            # Consider sys.exit(1) here if this is the only action
        action_taken = True
    elif (args.doc_input and not args.doc_output) or (not args.doc_input and args.doc_output):
        print("Error: For document conversion, both --doc_input and --doc_output must be specified.", file=sys.stderr)
        action_taken = True # Still an action, albeit an erroneous one for CLI.
        # sys.exit(1)

    if not action_taken:
        parser.print_help()
    
    sys.exit(0) # Default exit if any action was attempted or help printed.
