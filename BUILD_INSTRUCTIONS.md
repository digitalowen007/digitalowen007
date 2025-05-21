# Building VersaDownloader & Converter

This application can be packaged into a standalone executable using PyInstaller.

## Prerequisites
- Python 3.x
- Install dependencies: `pip install -r requirements.txt` (this will include `pyinstaller`)

## Build Command
To build the application, navigate to the project root directory in your terminal and run:
```bash
pyinstaller VersaDownloader.spec
```
This command uses the `VersaDownloader.spec` file, which provides more control over the build process.
The output will be in the `dist/VersaDownloaderApp` folder.

Alternatively, for a simpler one-off build (less recommended for this project's complexity):
```bash
pyinstaller --name VersaDownloader --windowed --onefile src/main.py --hidden-import="plyer.platforms.win.notification" --hidden-import="plyer.platforms.linux.notification" --hidden-import="plyer.platforms.macosx.notification"
```
(Additional hidden imports might be needed for the simple command).

## Important Considerations & Challenges

### 1. External Dependencies (FFmpeg & Pandoc)
- **FFmpeg:** This application relies on FFmpeg for video and audio conversion tasks. FFmpeg is **not** bundled with the packaged application by default.
    - **Solution for Users:** Users must install FFmpeg separately and ensure that `ffmpeg` (and `ffprobe`) are available in their system's PATH.
    - **Future Enhancement (Bundling):** To make it more user-friendly, FFmpeg executables could be bundled. This would involve:
        1. Acquiring the static FFmpeg builds for target platforms (Windows, macOS, Linux).
        2. Adding them to the `datas` section in `VersaDownloader.spec`: `datas=[('path/to/ffmpeg.exe', 'bin/ffmpeg'), ...]`
        3. Modifying the Python code (`src/conversion/converter.py`) to look for FFmpeg in this bundled location first (e.g., using `sys._MEIPASS` to find the path when frozen, or a relative path from the executable).

- **Pandoc:** This application uses Pandoc (via `pypandoc`) for DOCX to PDF and TXT to PDF conversions. Pandoc is **not** bundled.
    - **Solution for Users:** Users must install Pandoc separately and ensure it's available in their system's PATH.
    - **Future Enhancement (Bundling):** Similar to FFmpeg, Pandoc could potentially be bundled, but this is less common and might be more complex.

### 2. Platform Specifics
- The provided `.spec` file is a general starting point. Minor adjustments might be needed for optimal builds on Windows, macOS, or Linux (e.g., specific library paths, entitlements on macOS).
- Testing on each target platform is crucial.

### 3. Application Icon
- An application icon is not yet included. To add one:
    1. Create an icon file (e.g., `app_icon.ico` for Windows, `app_icon.icns` for macOS).
    2. Update the `icon` parameter in the `EXE` section of `VersaDownloader.spec`.

### 4. UPX
- The `.spec` file is configured to use UPX (`upx=True`) to compress the executable, which can reduce file size. UPX must be installed separately and be in the system PATH for this to work. If UPX is not available, PyInstaller will skip this step, or you can set `upx=False`.

### 5. Hidden Imports
- The `.spec` file includes a list of `hiddenimports`. These are modules that PyInstaller might not detect automatically. If you encounter `ModuleNotFoundError` when running the bundled app, you might need to add more modules to this list.
