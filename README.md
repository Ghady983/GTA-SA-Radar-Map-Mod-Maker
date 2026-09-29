# 🗺️ GTA SA Radar Map Mod Maker


**The easiest way to create custom radar map mods for Grand Theft Auto: San Andreas.**

Simply upload a full high-resolution map image, and this program will automatically slice, format, and package it into the 144 individual `.txd` tiles needed for the game. The output is a complete `.zip` archive ready to drop directly into Modloader—no manual cropping, hex editing, or scripting required!

The program currently supports only `256x256` `512x512` `1024x1024` resolutions

## ✨ Features

* 🗺️ **12x12 Interactive Radar Grid**: Full visual grid representing all 144 GTA San Andreas radar tiles (`radar00.txd` through `radar143.txd`) with live cell hover and selection.


* 🎯 **Landmark & Coordinate Math**: Real-time GTA world coordinate mapping ($-3000$ to $+3000$ on X/Y axes) coupled with an integrated database of San Andreas landmarks and regions.


* 🎨 **Procedural Map Themes**: Built-in map generators including **Satellite**, **Tactical Dark HUD**, and **Vintage 1992 Paper** styles.


* 🖼️ **Custom Image Upload**: Load any custom high-resolution map image (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`) and automatically slice it into the grid.


* ⚙️ **Flexible Tile Formats & Resolutions**:
* **Resolutions**: `256x256`, `512x512`, and `1024x1024`.


* **Formats**: `DXT1` (Compressed) or `BGRA32` (Uncompressed 32-bit).




* 🔬 **RenderWare Binary Inspector**: Built-in chunk hierarchy inspector and hex dump viewer for RenderWare 3.6.0.3 (`RW_VERSION_SA_PC` = `0x1803FFFF`).


* 📦 **1-Click Batch Exporter**: Instantly crop, generate, and package all 144 `.txd` tiles into a compressed `.zip` archive ready for ModLoader.



---

## 📸 Preview & UI Overview

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 🗺️ GTA SA Radar Map Mod Maker v1.0                                                  │
├──────────────────────────────────────┬─────────────────────────────────────────────────┤
│                                      │  Selected: radar00.txd (256x256 DXT1)           │
│   San Andreas 12x12 Radar Grid       │  Landmark: North-West Ocean                     │
│  ┌───┬───┬───┬───┬───┬───┬───┐       │  Binary: 32,840 bytes                           │
│  │00 │01 │02 │03 │04 │05 │.. │       ├─────────────────────────────────────────────────┤
│  ├───┼───┼───┼───┼───┼───┼───┤       │  Res:  (•) 256p  ( ) 512p  ( ) 1024p           │
│  │12 │13 │14 │15 │16 │17 │.. │       │  Format: (•) DXT1  ( ) BGRA32                   │
│  └───┴───┴───┴───┴───┴───┴───┘       ├─────────────────────────────────────────────────┤
│                                      │  RenderWare Chunk & Hex Dump Inspector          │
│  Target: radar00.txd | World X/Y     │  00000000  16 00 00 00 ...  ASCII             │
└──────────────────────────────────────┴─────────────────────────────────────────────────┘

```

---

## 🚀 Getting Started

### 📋 Prerequisites

* **Python 3.8+**
* **Tkinter** (included by default in standard Python installers for Windows/macOS)
* **Pillow (PIL)** for image processing



### 📥 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/gta-sa-radar-studio.git
cd gta-sa-radar-studio

```


2. **Install required dependencies:**
```bash
pip install pillow

```


3. **Run the application:**
```bash
python GtaSaRadarStudio.py

```



---

## 🛠️ Building the Executable (.exe)

This project includes a pre-configured PyInstaller specification file (`GtaSaRadarStudio.spec`) designed to compile the application into a standalone Windows executable.

### 🧰 Build Requirements

Install PyInstaller in your Python environment:

```bash
pip install pyinstaller pillow

```

### ⚡ Build Command

Run PyInstaller using the provided `.spec` configuration file:

```bash
pyinstaller GtaSaRadarStudio.spec

```

*(Optional: Use `--clean` to clear PyInstaller cache before building)*

```bash
pyinstaller --clean GtaSaRadarStudio.spec

```

### 📦 Executable Build Features

The `.spec` configuration includes:

* 🎯 **Custom Output Name**: Generates `GTA SA Radar Map Maker.exe` inside the `dist/` directory.


* 🖼️ **Embedded Window Icon**: Integrates `icon.ico` directly into the PE headers and taskbar.


* 🤫 **Console-Free GUI**: Suppresses the dark command prompt window on launch (`console=False`).


* 🪶 **Optimized Executable Size**: Excludes heavy unused modules (`numpy`, `matplotlib`, `pandas`, etc.) to keep boot times fast and binary sizes low.


* 🛡️ **UAC Invoker Level**: Configured as `AsInvoker` so standard user accounts can run it without UAC prompts.



Once the build finishes, find your compiled binary in:

```text
dist/GTA SA Radar Map Maker.exe

```

---

## 📁 Project Structure

```text
gta-sa-radar-studio/
├── GtaSaRadarStudio.py      # Main application source code[cite: 1]
├── GtaSaRadarStudio.spec    # PyInstaller compilation specification[cite: 2]
├── icon.ico                 # Application icon file[cite: 2]
└── README.md                # Project documentation

```

---

## 🎮 How to Install Exported Mods in GTA: San Andreas

1. Open **GTA SA Radar Map Mod Maker** and select or upload your map.


2. Click **⚡ Export All 144 TXDs (ZIP)**.


3. Extract the contents of the generated `.zip` file.


4. Move the extracted `GTA_SA_Radar_Mod` folder directly into your GTA San Andreas **ModLoader** directory:


```text
C:\Program Files (x86)\Rockstar Games\GTA San Andreas\modloader\GTA_SA_Radar_Mod\

```


5. Launch the game and enjoy your custom radar map! 🚗💨

---

## 📄 License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).

---
[![Donate on Patreon](https://img.shields.io/badge/Patreon-Donate-F96854?style=for-the-badge&logo=patreon&logoColor=white)](https://patreon.com/ghady983)