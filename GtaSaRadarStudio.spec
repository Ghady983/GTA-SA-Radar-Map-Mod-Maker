# -*- mode: python ; coding: utf-8 -*-
"""
=============================================================================
PyInstaller Build Specification File: GtaSaRadarStudio.spec
-----------------------------------------------------------------------------
Controls the compilation of GtaSaRadarStudio.py into a standalone Windows .exe:
  - Custom Output Name: "GTA SA Radar Map Maker.exe"
  - Program Icon: "icon.ico" (embedded directly into Windows PE resources)
  - Hidden Imports: Tkinter, PIL (Pillow), zipfile, threading
  - Bundle Mode: Single Portable Executable (onefile)
  - Console: Disabled (Pure GUI mode, no black command prompt window)
  - UAC Admin Execution: AsInvoker (Runs smoothly without unnecessary UAC popups)

Usage:
  pyinstaller GtaSaRadarStudio.spec
=============================================================================
"""

import sys
import os

block_cipher = None

# =============================================================================
# 1. APPLICATION IDENTITY & CONFIGURATION
#    (These variables are read directly by GtaSaRadarStudio.py at runtime)
# =============================================================================
APP_NAME = 'GTA SA Radar Map Mod Maker'
APP_ICON = 'icon.ico'
APP_VERSION = '1.1'

# Project root directory
project_dir = os.path.abspath(os.path.dirname(__file__) if '__file__' in locals() else '.')

# Locate custom icon if present in current directory, otherwise builds with default icon
icon_file = os.path.join(project_dir, APP_ICON)
has_icon = os.path.exists(icon_file)

# Include the .spec file and icon inside the bundle so the executable can read them
bundle_datas = [
    ('GtaSaRadarStudio.spec', '.'),
]
if has_icon:
    bundle_datas.append((icon_file, '.'))

a = Analysis(
    ['GtaSaRadarStudio.py'],
    pathex=[project_dir],
    binaries=[],
    datas=bundle_datas,
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'zipfile',
        'struct',
        'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Strip heavy unused packages to optimize file size and boot speed
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'pytest',
        'unittest',
        'sqlite3',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,                        # <-- Output executable name: "GTA SA Radar Map Maker.exe"
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                            # Use UPX compression if installed on your system
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                       # <-- False = GUI only (no black console prompt window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if has_icon else None, # <-- Custom Windows taskbar/desktop icon file (.ico)
    uac_admin=False,                     # Runs as standard user without nagging UAC popups
)
