# VersaDownloader.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
block_cipher = None

# Add project root to path for PyInstaller to find modules if running from outside root
# sys.path.append('.') # Usually not needed if spec is in root and run from root

a = Analysis(['src/main.py'],
             pathex=['.'], # Project root
             binaries=[],
             datas=[
                 # ('path/to/your_icon.ico', '.') # Example for icon if available later
             ],
             hiddenimports=[
                 'plyer.platforms.win.notification',
                 'plyer.platforms.linux.notification',
                 'plyer.platforms.macosx.notification',
                 'PIL.Image', # Ensure Pillow's core Image module is included
                 'PIL.WebPImagePlugin', # For WebP
                 'PIL.JpegImagePlugin', # For JPG
                 'PIL.PngImagePlugin',  # For PNG
                 # Add other specific Pillow plugins if more formats are supported
                 'pypandoc', # Ensure pypandoc itself is found
                 'docx',     # Ensure python-docx is found
                 # Project modules (though PyInstaller often finds these via Analysis)
                 'src.config', 'src.config.settings_manager',
                 'src.conversion', 'src.conversion.converter',
                 'src.downloading', 'src.downloading.downloader',
                 'src.ui', 'src.ui.main_window', 'src.ui.settings_dialog', 'src.ui.workers', 'src.ui.themes',
                 'src.utils', 'src.utils.logger', 'src.utils.notifications',
                 # PyQt6 modules are usually handled by PyInstaller's hooks, but sometimes need specifics
                 'PyQt6.sip', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets',
                 'PyQt6.QtNetwork', # If any network features directly used by Qt
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# Collect PyQt6 data files (e.g., translations, plugins)
# This is often crucial for PyQt6 apps to function correctly when bundled.
from PyInstaller.utils.hooks import collect_data_files
datas += collect_data_files('PyQt6', include_py_files=False) # Exclude .py files from Qt itself

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='VersaDownloader', # Name of the executable
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True, # Set to False if UPX is not installed or causes issues
          console=False, # True for CLI app, False for GUI
          windowed=True, # Use with console=False for GUI
          icon=None) # Replace None with 'path/to/icon.ico' or 'path/to/icon.xpm'

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='VersaDownloaderApp') # Name of the output folder in 'dist'
