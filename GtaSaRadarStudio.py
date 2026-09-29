#!/usr/bin/env python3
"""
GTA San Andreas Radar Map Maker - Interactive Desktop Studio
Exact desktop twin of the web studio:
  - Interactive 12x12 Radar Map Grid with live cell selection & hover
  - Real-time world coordinate math (X: -3000..+3000, Y: -3000..+3000)
  - Full San Andreas Landmarks Database (Grove Street, Area 69, Mount Chiliad, Gant Bridge)
  - Built-in Procedural Maps: Satellite, Tactical Dark HUD, Vintage 1992 Paper
  - Custom High-Res Image Upload
  - Live RenderWare Chunk Hierarchy & Hex Dump Inspector
  - 1-Click single tile .txd save & 144-tile .ZIP archive batch exporter
"""

import os
import sys
import struct
import zipfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller bundle execution."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

def load_spec_config():
    """Reads APP_NAME, APP_ICON, and APP_VERSION directly from GtaSaRadarStudio.spec if present."""
    app_name = "GTA SA Radar Map Mod Maker"
    app_icon = "icon.ico"
    app_version = "1.0"
    spec_path = get_resource_path("GtaSaRadarStudio.spec")
    if os.path.exists(spec_path):
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("APP_NAME"):
                        app_name = line.split("=", 1)[1].strip().strip("'\"")
                    elif line.startswith("APP_ICON"):
                        app_icon = line.split("=", 1)[1].strip().strip("'\"")
                    elif line.startswith("APP_VERSION"):
                        app_version = line.split("=", 1)[1].strip().strip("'\"")
        except Exception:
            pass
    return app_name, app_icon, app_version

APP_NAME, APP_ICON, APP_VERSION = load_spec_config()

RW_VERSION_SA_PC = 0x1803FFFF  # RenderWare 3.6.0.3 GTA San Andreas PC

CHUNK_STRUCT = 0x0001
CHUNK_EXTENSION = 0x0003
CHUNK_TEXTURENATIVE = 0x0015
CHUNK_TEXDICTIONARY = 0x0016

PLATFORM_D3D9 = 9
FOURCC_DXT1 = 0x31545844  # 'DXT1'
D3DFMT_A8R8G8B8 = 21       # 32-bit BGRA

LANDMARK_MAP = {
    0: ("North-West Ocean", "Ocean / Coast"),
    1: ("Bayside Marina & North Bay", "Tierra Robada"),
    2: ("North Bayside Waters", "Tierra Robada"),
    3: ("El Quebrados North Desert", "Tierra Robada"),
    4: ("Sherman Dam Reservoir / North Waters", "Tierra Robada"),
    5: ("Arco del Oeste & North Desert", "Bone County"),
    6: ("North Desert / Las Payasadas", "Bone County"),
    7: ("Las Venturas North Boundary", "Las Venturas"),
    8: ("Prickle Pine (North Las Venturas)", "Las Venturas"),
    9: ("Yellow Bell Golf Club", "Las Venturas"),
    10: ("North-East Desert Ocean", "Ocean / Coast"),
    11: ("Far North-East Ocean", "Ocean / Coast"),
    12: ("North Gant Bridge Waters", "Ocean / Coast"),
    13: ("Gant Bridge (North End)", "San Fierro"),
    14: ("San Fierro Bay / Garver Bridge Approach", "San Fierro"),
    15: ("El Quebrados Village", "Tierra Robada"),
    16: ("Sherman Dam & Power Station", "Tierra Robada"),
    17: ("Verdant Meadows Aircraft Graveyard", "Bone County"),
    18: ("Area 69 Restricted Zone (North Gate)", "Bone County"),
    19: ("Las Venturas Airport Approach", "Las Venturas"),
    20: ("Redsands East / The Emerald Isle", "Las Venturas"),
    21: ("Pilson Intersection / Spinybed", "Las Venturas"),
    22: ("North-East Coast Waters", "Ocean / Coast"),
    23: ("East Ocean (North)", "Ocean / Coast"),
    24: ("Pacific Ocean (West Coast)", "Ocean / Coast"),
    25: ("Esplanade North / Battery Point", "San Fierro"),
    26: ("Downtown San Fierro / Financial", "San Fierro"),
    27: ("Kincaid Bridge / Garver Bridge Span", "San Fierro"),
    28: ("Tierra Robada Hills & Valle Ocultado", "Tierra Robada"),
    29: ("Lil' Probe'Inn & The Big Ear Antenna", "Bone County"),
    30: ("Area 69 Underground Facility", "Bone County"),
    31: ("Las Venturas Airport (Terminals)", "Las Venturas"),
    32: ("The Strip (Caligula's & The Visage)", "Las Venturas"),
    33: ("Sobell Rail Yards / Linden Station", "Las Venturas"),
    34: ("East Las Venturas Bypass", "Las Venturas"),
    35: ("East Sea Waters", "Ocean / Coast"),
    36: ("West Ocean (San Fierro Shore)", "Ocean / Coast"),
    37: ("Ocean Flats & Palisades", "San Fierro"),
    38: ("King's / Queens / Doherty Garage", "San Fierro"),
    39: ("Easter Basin Naval Base & Aircraft Carrier", "San Fierro"),
    40: ("San Fierro Bay (South Crossing)", "San Fierro"),
    41: ("Fort Carson / Martin Bridge", "Bone County"),
    42: ("Hunter Quarry", "Bone County"),
    43: ("Blackfield Stadium & Circus Circus", "Las Venturas"),
    44: ("The Strip South / Four Dragons Casino", "Las Venturas"),
    45: ("Rockshore West & East", "Las Venturas"),
    46: ("South-East Las Venturas Freeway", "Las Venturas"),
    47: ("East Ocean Shore", "Ocean / Coast"),
    48: ("West Ocean Off San Fierro", "Ocean / Coast"),
    49: ("Missionary Hill / Radio Tower", "San Fierro"),
    50: ("Foster Valley / Mount Chiliad Foothills", "San Fierro"),
    51: ("Easter Bay Airport (Runways)", "San Fierro"),
    52: ("Easter Bay Waterway / Red County Border", "Red County"),
    53: ("The Panopticon Timber Yard", "Red County"),
    54: ("Blueberry Town & Blueberry Acres", "Red County"),
    55: ("Montgomery Town & Intersection", "Red County"),
    56: ("Montgomery Crippen Memorial / North Hills", "Red County"),
    57: ("Las Venturas South Freeway", "Red County"),
    58: ("Fisher's Lagoon North Coast", "Red County"),
    59: ("East Coast Deep Water", "Ocean / Coast"),
    60: ("Pacific Ocean (West)", "Ocean / Coast"),
    61: ("Whetstone North Forests", "Whetstone"),
    62: ("Shady Creeks North / Back o Beyond", "Flint County"),
    63: ("Flint Range / Beacon Hill", "Flint County"),
    64: ("Flint County Farmlands / The Farm", "Flint County"),
    65: ("Flint Intersection / Red County Border", "Red County"),
    66: ("Fern Ridge & Catalina's Hideout", "Red County"),
    67: ("Dillimore Town & Police Station", "Red County"),
    68: ("Hankypanky Point / Mulholland Hills", "Red County"),
    69: ("Mulholland Intersection", "Los Santos"),
    70: ("Palomino Creek Town & Church", "Red County"),
    71: ("Fisher's Lagoon & Abandoned Pier", "Red County"),
    72: ("West Ocean (Mount Chiliad Approach)", "Ocean / Coast"),
    73: ("Mount Chiliad Summit (1000m Peak)", "Whetstone"),
    74: ("Mount Chiliad Eastern Trails", "Whetstone"),
    75: ("Leafy Hollow / Shady Cabin", "Flint County"),
    76: ("Back o' Beyond Ghost Glade", "Flint County"),
    77: ("Fallen Tree Woods / Flint County", "Flint County"),
    78: ("Mulholland Madd Dogg's Mansion", "Los Santos"),
    79: ("Richman Mansions & Vinewood Sign", "Los Santos"),
    80: ("Vinewood Hills & Temple", "Los Santos"),
    81: ("East Los Santos & Las Colinas", "Los Santos"),
    82: ("Las Colinas Hilltops", "Los Santos"),
    83: ("East Coast Shore / Palomino Bay", "Ocean / Coast"),
    84: ("South-West Ocean", "Ocean / Coast"),
    85: ("Angel Pine Town & Sawmill", "Whetstone"),
    86: ("Angel Pine Junkyard & Mountains", "Whetstone"),
    87: ("Shady Creeks South Riverbed", "Whetstone"),
    88: ("Flint Waterway / Marina Approach", "Flint County"),
    89: ("Rodeo / Santa Maria Causeway", "Los Santos"),
    90: ("Market / Downtown Los Santos Hospital", "Los Santos"),
    91: ("Commerce / City Hall / Pershing Square", "Los Santos"),
    92: ("Jefferson / Glen Park / Skate Park", "Los Santos"),
    93: ("Ganton (Grove Street Cul-de-Sac!)", "Los Santos"),
    94: ("Playa del Seville / East Beach North", "Los Santos"),
    95: ("Far East Coast Waters", "Ocean / Coast"),
    96: ("South Whetstone Ocean", "Ocean / Coast"),
    97: ("South Angel Pine Wilderness", "Whetstone"),
    98: ("Whetstone South Coast Cliffs", "Whetstone"),
    99: ("Flint Bay Waters", "Flint County"),
    100: ("Verona Beach Canals", "Los Santos"),
    101: ("Marina & Santa Maria Beach Pier", "Los Santos"),
    102: ("Verona Beach & Conference Center", "Los Santos"),
    103: ("Idlewood / Reece's Barbershop / Gas", "Los Santos"),
    104: ("Willowfield / Train Yards", "Los Santos"),
    105: ("Corona / El Corona Station", "Los Santos"),
    106: ("East Beach Boardwalk & Shoreline", "Los Santos"),
    107: ("East Coast Deep Sea", "Ocean / Coast"),
    108: ("South-West Pacific Deep Ocean", "Ocean / Coast"),
    109: ("South Whetstone Ocean Water", "Ocean / Coast"),
    110: ("South-West Coastline Waters", "Ocean / Coast"),
    111: ("South Bay Entrance", "Ocean / Coast"),
    112: ("Santa Maria Beach Open Ocean", "Ocean / Coast"),
    113: ("Verona Beach South Waters", "Ocean / Coast"),
    114: ("Los Santos International Airport (Gate)", "Los Santos"),
    115: ("LSX Airport Runways & Hangars", "Los Santos"),
    116: ("Ocean Docks (Terminals & Cranes)", "Los Santos"),
    117: ("Ocean Docks (Cargo Ships)", "Los Santos"),
    118: ("East Beach South Waters", "Ocean / Coast"),
    119: ("South-East Ocean", "Ocean / Coast"),
    120: ("Far South-West Ocean", "Ocean / Coast"),
    121: ("Far South-West Ocean", "Ocean / Coast"),
    122: ("South Coast Waters", "Ocean / Coast"),
    123: ("South Coast Waters", "Ocean / Coast"),
    124: ("South Ocean Waters", "Ocean / Coast"),
    125: ("South Ocean Waters", "Ocean / Coast"),
    126: ("LSX Airport South Waterway", "Ocean / Coast"),
    127: ("Ocean Docks South Basin", "Ocean / Coast"),
    128: ("South-East Ocean Docks Waters", "Ocean / Coast"),
    129: ("South-East Coast Waters", "Ocean / Coast"),
    130: ("South-East Deep Ocean", "Ocean / Coast"),
    131: ("South-East Far Ocean", "Ocean / Coast"),
    132: ("South Edge Ocean", "Ocean / Coast"),
    133: ("South Edge Ocean", "Ocean / Coast"),
    134: ("South Edge Ocean", "Ocean / Coast"),
    135: ("South Edge Ocean", "Ocean / Coast"),
    136: ("South Edge Ocean", "Ocean / Coast"),
    137: ("South Edge Ocean", "Ocean / Coast"),
    138: ("South Edge Ocean", "Ocean / Coast"),
    139: ("South Edge Ocean", "Ocean / Coast"),
    140: ("South Edge Ocean", "Ocean / Coast"),
    141: ("South Edge Ocean", "Ocean / Coast"),
    142: ("South Edge Ocean", "Ocean / Coast"),
    143: ("South-East Corner Ocean (radar143)", "Ocean / Coast"),
}

def write_chunk(chunk_type: int, size: int) -> bytes:
    return struct.pack('<III', chunk_type, size, RW_VERSION_SA_PC)

def encode_dxt1_block(pixels_16_rgba) -> bytes:
    min_r, min_g, min_b = 255, 255, 255
    max_r, max_g, max_b = 0, 0, 0
    for r, g, b, _ in pixels_16_rgba:
        if r < min_r: min_r = r
        if r > max_r: max_r = r
        if g < min_g: min_g = g
        if g > max_g: max_g = g
        if b < min_b: min_b = b
        if b > max_b: max_b = b

    def to_565(r, g, b):
        return (((r >> 3) & 0x1F) << 11) | (((g >> 2) & 0x3F) << 5) | ((b >> 3) & 0x1F)

    def from_565(c):
        return (int(((c >> 11) & 0x1F) * 255 / 31), int(((c >> 5) & 0x3F) * 255 / 63), int((c & 0x1F) * 255 / 31))

    c0 = to_565(max_r, max_g, max_b)
    c1 = to_565(min_r, min_g, min_b)
    if c0 < c1:
        c0, c1 = c1, c0
    elif c0 == c1 and c0 > 0:
        c1 -= 1

    r0, g0, b0 = from_565(c0)
    r1, g1, b1 = from_565(c1)
    palette = [
        (r0, g0, b0), (r1, g1, b1),
        (int((2 * r0 + r1) / 3), int((2 * g0 + g1) / 3), int((2 * b0 + b1) / 3)),
        (int((r0 + 2 * r1) / 3), int((r0 + 2 * g1) / 3), int((r0 + 2 * b1) / 3)),
    ]

    indices = 0
    for i, (pr, pg, pb, _) in enumerate(pixels_16_rgba):
        best_dist = float('inf')
        best_idx = 0
        for p_idx, (cr, cg, cb) in enumerate(palette):
            dr = pr - cr
            dg = pg - cg
            db = pb - cb
            dist = dr * dr * 2 + dg * dg * 4 + db * db
            if dist < best_dist:
                best_dist = dist
                best_idx = p_idx
        indices |= (best_idx & 0x3) << (i * 2)

    return struct.pack('<HHI', c0, c1, indices)

def compress_image_dxt1(img: Image.Image) -> bytes:
    width, height = img.size
    pixels = img.load()
    out = bytearray()
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            block = []
            for py in range(4):
                for px in range(4):
                    ix = min(bx + px, width - 1)
                    iy = min(by + py, height - 1)
                    block.append(pixels[ix, iy])
            out.extend(encode_dxt1_block(block))
    return bytes(out)

def build_radar_txd(name: str, tile_img: Image.Image, format_type: str = 'dxt1') -> bytes:
    img = tile_img.convert('RGBA')
    width, height = img.size

    if format_type == 'dxt1':
        tex_bytes = compress_image_dxt1(img)
        raster_format = 0x0800
        d3d_format = FOURCC_DXT1
        depth = 16
        compression_flag = 0x08
    else:
        r, g, b, a = img.split()
        bgra_img = Image.merge('RGBA', (b, g, r, a))
        tex_bytes = bgra_img.tobytes()
        raster_format = 0x0200
        d3d_format = D3DFMT_A8R8G8B8
        depth = 32
        compression_flag = 0x00

    hdr = bytearray(88)
    struct.pack_into('<I', hdr, 0, PLATFORM_D3D9)
    struct.pack_into('<I', hdr, 4, 0x1102)
    clean_name = name[:31].encode('ascii')
    hdr[8:8 + len(clean_name)] = clean_name
    struct.pack_into('<I', hdr, 72, raster_format)
    struct.pack_into('<I', hdr, 76, d3d_format)
    struct.pack_into('<HH', hdr, 80, width, height)
    hdr[84] = depth
    hdr[85] = 1
    hdr[86] = 4
    hdr[87] = compression_flag

    tex_struct_payload = bytes(hdr) + struct.pack('<I', len(tex_bytes)) + tex_bytes
    tex_struct_chunk = write_chunk(CHUNK_STRUCT, len(tex_struct_payload)) + tex_struct_payload
    tex_ext_chunk = write_chunk(CHUNK_EXTENSION, 0)
    tex_native_payload = tex_struct_chunk + tex_ext_chunk
    tex_native_chunk = write_chunk(CHUNK_TEXTURENATIVE, len(tex_native_payload)) + tex_native_payload

    dict_struct_payload = struct.pack('<HH', 1, 1)
    dict_struct_chunk = write_chunk(CHUNK_STRUCT, len(dict_struct_payload)) + dict_struct_payload
    dict_ext_chunk = write_chunk(CHUNK_EXTENSION, 0)
    dict_payload = dict_struct_chunk + tex_native_chunk + dict_ext_chunk
    return write_chunk(CHUNK_TEXDICTIONARY, len(dict_payload)) + dict_payload

def generate_sample_san_andreas_map(size: int = 1536, theme: str = 'satellite') -> Image.Image:
    img = Image.new('RGB', (size, size), color=(18, 37, 56))
    draw = ImageDraw.Draw(img)
    palettes = {
        'satellite': {'deep': (18, 37, 56), 'land': (67, 88, 52), 'desert': (169, 140, 86), 'urban': (88, 88, 96), 'river': (39, 75, 107), 'freeway': (220, 166, 66), 'runway': (43, 43, 49), 'chiliad': (92, 82, 67), 'grove': (27, 77, 36)},
        'tactical_dark': {'deep': (9, 13, 22), 'land': (30, 41, 59), 'desert': (51, 65, 85), 'urban': (59, 66, 82), 'river': (30, 58, 138), 'freeway': (56, 189, 248), 'runway': (17, 24, 39), 'chiliad': (37, 46, 62), 'grove': (34, 197, 94)},
        'vintage_1992': {'deep': (166, 184, 190), 'land': (210, 202, 169), 'desert': (221, 199, 158), 'urban': (191, 184, 165), 'river': (152, 173, 183), 'freeway': (194, 88, 56), 'runway': (96, 88, 80), 'chiliad': (185, 168, 136), 'grove': (114, 136, 96)}
    }.get(theme, {})

    def to_cx(wx): return int(((wx + 3000) / 6000) * size)
    def to_cy(wy): return int(((3000 - wy) / 6000) * size)

    draw.rectangle([0, 0, size, size], fill=palettes['deep'])
    draw.polygon([(to_cx(-2800), to_cy(1500)), (to_cx(-1200), to_cy(1500)), (to_cx(-1000), to_cy(1000)), (to_cx(-1100), to_cy(0)), (to_cx(-1400), to_cy(-500)), (to_cx(-1700), to_cy(-1800)), (to_cx(-2200), to_cy(-2800)), (to_cx(-2800), to_cy(-2200)), (to_cx(-2900), to_cy(0))], fill=palettes['land'])
    cx, cy = to_cx(-2250), to_cy(-1650)
    rad = int(size * 0.08)
    draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=palettes['chiliad'])
    draw.polygon([(to_cx(-2400), to_cy(2600)), (to_cx(-700), to_cy(2800)), (to_cx(1200), to_cy(2850)), (to_cx(2850), to_cy(2700)), (to_cx(2850), to_cy(600)), (to_cx(1200), to_cy(500)), (to_cx(0), to_cy(600)), (to_cx(-400), to_cy(1100)), (to_cx(-1500), to_cy(1700)), (to_cx(-2400), to_cy(2000))], fill=palettes['desert'])
    draw.polygon([(to_cx(-1200), to_cy(500)), (to_cx(200), to_cy(700)), (to_cx(2300), to_cy(600)), (to_cx(2800), to_cy(-300)), (to_cx(2900), to_cy(-2000)), (to_cx(1500), to_cy(-2800)), (to_cx(200), to_cy(-2400)), (to_cx(-500), to_cy(-1800)), (to_cx(-1000), to_cy(-1000))], fill=palettes['land'])
    draw.rectangle([to_cx(800), to_cy(-1000), to_cx(800) + int(size * 0.28), to_cy(-1000) + int(size * 0.24)], fill=palettes['urban'])
    draw.rectangle([to_cx(-2700), to_cy(1400), to_cx(-2700) + int(size * 0.22), to_cy(1400) + int(size * 0.24)], fill=palettes['urban'])
    draw.rectangle([to_cx(1200), to_cy(2400), to_cx(1200) + int(size * 0.25), to_cy(2400) + int(size * 0.28)], fill=palettes['urban'])
    draw.line([(to_cx(-1800), to_cy(2500)), (to_cx(-1300), to_cy(1700)), (to_cx(-800), to_cy(1200)), (to_cx(-800), to_cy(0))], fill=palettes['river'], width=int(size * 0.02))
    draw.line([(to_cx(500), to_cy(2500)), (to_cx(100), to_cy(1400)), (to_cx(700), to_cy(400)), (to_cx(2300), to_cy(0))], fill=palettes['river'], width=int(size * 0.02))
    draw.line([(to_cx(-2700), to_cy(1600)), (to_cx(-2700), to_cy(2300))], fill=palettes['freeway'], width=int(size * 0.008))
    draw.rectangle([to_cx(1000), to_cy(2600), to_cx(1000) + int(size * 0.28), to_cy(2600) + int(size * 0.32)], outline=palettes['freeway'], width=int(size * 0.008))
    gx, gy = to_cx(2490), to_cy(-1670)
    gr = int(size * 0.012)
    draw.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=palettes['grove'])
    return img

class GtaSaRadarStudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1240x840")
        self.root.minsize(1080, 720)
        self.root.configure(bg="#09090b")

        self.set_app_icon()

        self.current_theme = 'satellite'
        self.custom_image = None
        self.source_map_image = None
        self.selected_tile_idx = 0
        self.hovered_tile_idx = None
        self.grid_canvas_size = 540
        self.cached_tk_map = None
        self.current_txd_bytes = b''

        self.build_ui()
        self.load_theme_map('satellite')

    def set_app_icon(self):
        icon_path = get_resource_path(APP_ICON)
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                try:
                    icon_img = ImageTk.PhotoImage(Image.open(icon_path))
                    self.root.iconphoto(True, icon_img)
                    self._app_icon_ref = icon_img
                except Exception:
                    pass

    def build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg="#18181b", bd=1, relief="solid")
        hdr.pack(fill="x", side="top", padx=16, pady=(12, 6))

        left = tk.Frame(hdr, bg="#18181b")
        left.pack(side="left", padx=12, pady=8)
        tk.Label(left, text=APP_NAME, font=("Segoe UI", 12, "bold"), fg="#f4f4f5", bg="#18181b").pack(anchor="w")
        tk.Label(left, text=f"v{APP_VERSION}", font=("Segoe UI", 8), fg="#a1a1aa", bg="#18181b").pack(anchor="w")

        mid = tk.Frame(hdr, bg="#18181b")
        mid.pack(side="left", expand=True, padx=10)
        self.btn_sat = tk.Button(mid, text="Satellite", font=("Segoe UI", 8, "bold"), bg="#f59e0b", fg="#09090b", command=lambda: self.load_theme_map('satellite'), relief="flat", padx=8, pady=3)
        self.btn_sat.pack(side="left", padx=2)
        self.btn_dark = tk.Button(mid, text="Tactical Dark", font=("Segoe UI", 8), bg="#27272a", fg="#d4d4d8", command=lambda: self.load_theme_map('tactical_dark'), relief="flat", padx=8, pady=3)
        self.btn_dark.pack(side="left", padx=2)
        self.btn_vint = tk.Button(mid, text="Vintage 1992", font=("Segoe UI", 8), bg="#27272a", fg="#d4d4d8", command=lambda: self.load_theme_map('vintage_1992'), relief="flat", padx=8, pady=3)
        self.btn_vint.pack(side="left", padx=2)
        self.btn_upload = tk.Button(mid, text="📁 Custom Image...", font=("Segoe UI", 8, "bold"), bg="#3f3f46", fg="#ffffff", command=self.upload_custom_map, relief="flat", padx=10, pady=3)
        self.btn_upload.pack(side="left", padx=(8, 2))

        right = tk.Frame(hdr, bg="#18181b")
        right.pack(side="right", padx=12, pady=8)
        self.btn_batch = tk.Button(right, text="⚡ Export All 144 TXDs (ZIP)", font=("Segoe UI", 9, "bold"), bg="#f59e0b", fg="#09090b", command=self.batch_export_dialog, padx=14, pady=5, relief="flat", cursor="hand2")
        self.btn_batch.pack()

        # Workspace
        main = tk.Frame(self.root, bg="#09090b")
        main.pack(fill="both", expand=True, padx=16, pady=4)

        # Left Canvas
        left_p = tk.Frame(main, bg="#18181b", bd=1, relief="solid")
        left_p.pack(side="left", fill="both", expand=True, padx=(0, 6), pady=4)

        c_bar = tk.Frame(left_p, bg="#18181b")
        c_bar.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(c_bar, text="San Andreas 12x12 Radar Grid", font=("Segoe UI", 10, "bold"), fg="#f4f4f5", bg="#18181b").pack(side="left")
        self.grid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(c_bar, text="Show Grid", variable=self.grid_var, command=self.redraw_grid, bg="#18181b", fg="#a1a1aa", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8)).pack(side="right")

        self.map_canvas = tk.Canvas(left_p, width=self.grid_canvas_size, height=self.grid_canvas_size, bg="#09090b", highlightthickness=1, highlightbackground="#3f3f46")
        self.map_canvas.pack(pady=4)
        self.map_canvas.bind("<Button-1>", self.on_click)
        self.map_canvas.bind("<Motion>", self.on_motion)
        self.map_canvas.bind("<Leave>", lambda e: self.set_hover(None))

        self.readout = tk.Label(left_p, text="Target: radar00.txd | North-West Ocean", font=("Consolas", 8), fg="#34d399", bg="#18181b")
        self.readout.pack(pady=(2, 8))

        # Right Panel
        right_p = tk.Frame(main, bg="#09090b", width=520)
        right_p.pack(side="right", fill="both", padx=(6, 0), pady=4)
        right_p.pack_propagate(False)

        # Preview Card
        t_card = tk.Frame(right_p, bg="#18181b", bd=1, relief="solid")
        t_card.pack(fill="x", pady=(0, 4))
        th = tk.Frame(t_card, bg="#18181b")
        th.pack(fill="x", padx=10, pady=6)
        self.lbl_tile_name = tk.Label(th, text="Selected: radar00.txd", font=("Segoe UI", 9, "bold"), fg="#f59e0b", bg="#18181b")
        self.lbl_tile_name.pack(side="left")
        tk.Button(th, text="💾 Save .txd", font=("Segoe UI", 8, "bold"), bg="#f59e0b", fg="#09090b", command=self.save_single_txd, relief="flat", padx=6, pady=1).pack(side="right")

        tb = tk.Frame(t_card, bg="#18181b")
        tb.pack(fill="x", padx=10, pady=(0, 8))
        self.prev_canvas = tk.Canvas(tb, width=140, height=140, bg="#09090b", highlightthickness=1, highlightbackground="#3f3f46")
        self.prev_canvas.pack(side="left", padx=(0, 10))

        sb = tk.Frame(tb, bg="#09090b", bd=1, relief="solid")
        sb.pack(side="left", fill="both", expand=True)
        self.lbl_spec_lm = tk.Label(sb, text="Landmark: North-West Ocean", font=("Segoe UI", 8, "bold"), fg="#e4e4e7", bg="#09090b", anchor="w")
        self.lbl_spec_lm.pack(fill="x", padx=6, pady=(4, 1))
        self.lbl_spec_reg = tk.Label(sb, text="Region: Ocean / Coast", font=("Segoe UI", 8), fg="#a1a1aa", bg="#09090b", anchor="w")
        self.lbl_spec_reg.pack(fill="x", padx=6, pady=1)
        self.lbl_spec_sz = tk.Label(sb, text="Binary: 32,840 bytes", font=("Consolas", 8, "bold"), fg="#f59e0b", bg="#09090b", anchor="w")
        self.lbl_spec_sz.pack(fill="x", padx=6, pady=(2, 4))

        # Settings
        cfg = tk.Frame(right_p, bg="#18181b", bd=1, relief="solid")
        cfg.pack(fill="x", pady=4)
        tk.Label(cfg, text="Res:", font=("Segoe UI", 8, "bold"), fg="#71717a", bg="#18181b").pack(side="left", padx=(8, 2), pady=6)
        self.res_var = tk.IntVar(value=256)
        for r_val, r_txt in [(256, "256p"), (512, "512p"), (1024, "1024p")]:
            tk.Radiobutton(cfg, text=r_txt, variable=self.res_var, value=r_val, command=self.update_tile, bg="#18181b", fg="#ffffff", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8)).pack(side="left")

        tk.Label(cfg, text="Format:", font=("Segoe UI", 8, "bold"), fg="#71717a", bg="#18181b").pack(side="left", padx=(10, 2))
        self.fmt_var = tk.StringVar(value="dxt1")
        tk.Radiobutton(cfg, text="DXT1", variable=self.fmt_var, value="dxt1", command=self.update_tile, bg="#18181b", fg="#ffffff", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8)).pack(side="left")
        tk.Radiobutton(cfg, text="BGRA32", variable=self.fmt_var, value="bgra32", command=self.update_tile, bg="#18181b", fg="#ffffff", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8)).pack(side="left")

        # Hex Dump Box
        hx = tk.Frame(right_p, bg="#18181b", bd=1, relief="solid")
        hx.pack(fill="both", expand=True, pady=(4, 0))
        tk.Label(hx, text="RenderWare TXD Chunk & Hex Dump Inspector", font=("Segoe UI", 8, "bold"), fg="#f4f4f5", bg="#18181b").pack(anchor="w", padx=8, pady=4)
        self.txt_hex = tk.Text(hx, bg="#09090b", fg="#d4d4d8", font=("Consolas", 8), bd=0, padx=6, pady=6)
        self.txt_hex.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # Bottom Bar
        btm = tk.Frame(self.root, bg="#18181b", bd=1, relief="solid")
        btm.pack(fill="x", side="bottom", padx=16, pady=(4, 10))
        self.lbl_status = tk.Label(btm, text="Ready.", font=("Segoe UI", 8), fg="#a1a1aa", bg="#18181b")
        self.lbl_status.pack(side="left", padx=10, pady=3)
        self.prog = ttk.Progressbar(btm, orient="horizontal", length=220, mode="determinate")
        self.prog.pack(side="right", padx=10, pady=3)

    def load_theme_map(self, t):
        self.current_theme = t
        self.custom_image = None
        self.source_map_image = generate_sample_san_andreas_map(1536, t)
        disp = self.source_map_image.resize((self.grid_canvas_size, self.grid_canvas_size), Image.Resampling.BILINEAR)
        self.cached_tk_map = ImageTk.PhotoImage(disp)
        self.redraw_grid()
        self.update_tile()

    def upload_custom_map(self):
        f = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp")])
        if f:
            try:
                self.custom_image = Image.open(f)
                self.source_map_image = self.custom_image
                disp = self.source_map_image.resize((self.grid_canvas_size, self.grid_canvas_size), Image.Resampling.BILINEAR)
                self.cached_tk_map = ImageTk.PhotoImage(disp)
                self.redraw_grid()
                self.update_tile()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image:\n{e}")

    def redraw_grid(self):
        self.map_canvas.delete("all")
        if self.cached_tk_map:
            self.map_canvas.create_image(0, 0, anchor="nw", image=self.cached_tk_map)
        cs = self.grid_canvas_size / 12.0
        for r in range(12):
            for c in range(12):
                idx = r * 12 + c
                x0, y0 = c * cs, r * cs
                x1, y1 = x0 + cs, y0 + cs
                is_sel = (idx == self.selected_tile_idx)
                is_hov = (idx == self.hovered_tile_idx)
                if is_sel:
                    self.map_canvas.create_rectangle(x0, y0, x1, y1, fill="#f59e0b", stipple="gray25", outline="#f59e0b", width=2)
                elif is_hov:
                    self.map_canvas.create_rectangle(x0, y0, x1, y1, fill="#fbbf24", stipple="gray25", outline="#fbbf24", width=1)
                elif self.grid_var.get():
                    self.map_canvas.create_rectangle(x0, y0, x1, y1, outline="#52525b", width=1)

                if is_sel or is_hov:
                    self.map_canvas.create_rectangle(x0 + 2, y0 + 2, x0 + 18, y0 + 14, fill="#09090b", outline="")
                    self.map_canvas.create_text(x0 + 10, y0 + 8, text=f"{idx:02d}", fill="#f59e0b" if is_sel else "#ffffff", font=("Consolas", 7, "bold"))
                elif self.grid_var.get():
                    self.map_canvas.create_text(x0 + 10, y0 + 8, text=f"{idx:02d}", fill="#a1a1aa", font=("Consolas", 6))

    def on_click(self, event):
        cs = self.grid_canvas_size / 12.0
        c, r = int(event.x // cs), int(event.y // cs)
        if 0 <= c < 12 and 0 <= r < 12:
            self.selected_tile_idx = r * 12 + c
            self.redraw_grid()
            self.update_tile()

    def on_motion(self, event):
        cs = self.grid_canvas_size / 12.0
        c, r = int(event.x // cs), int(event.y // cs)
        if 0 <= c < 12 and 0 <= r < 12:
            idx = r * 12 + c
            if self.hovered_tile_idx != idx:
                self.set_hover(idx)
        else:
            self.set_hover(None)

    def set_hover(self, idx):
        self.hovered_tile_idx = idx
        self.redraw_grid()
        curr = idx if idx is not None else self.selected_tile_idx
        row, col = curr // 12, curr % 12
        lm, reg = LANDMARK_MAP.get(curr, ("Landmark", "Region"))
        self.readout.config(text=f"Target: radar{curr:02d}.txd | {lm} ({reg}) | World X: {-3000+col*500}..{-2500+col*500}, Y: {2500-row*500}..{3000-row*500}")

    def update_tile(self):
        if not self.source_map_image: return
        idx = self.selected_tile_idx
        r, c = idx // 12, idx % 12
        name = f"radar{idx:02d}"
        w, h = self.source_map_image.size
        x0 = round((c * w) / 12)
        x1 = round(((c + 1) * w) / 12)
        y0 = round((r * h) / 12)
        y1 = round(((r + 1) * h) / 12)

        sz = self.res_var.get()
        fmt = self.fmt_var.get()
        tile = self.source_map_image.crop((x0, y0, x1, y1)).resize((sz, sz), Image.Resampling.LANCZOS)
        txd = build_radar_txd(name, tile, fmt)
        self.current_txd_bytes = txd

        prev = tile.resize((140, 140), Image.Resampling.BILINEAR)
        self.cached_prev = ImageTk.PhotoImage(prev)
        self.prev_canvas.delete("all")
        self.prev_canvas.create_image(0, 0, anchor="nw", image=self.cached_prev)

        lm, reg = LANDMARK_MAP.get(idx, ("Landmark", "Region"))
        self.lbl_tile_name.config(text=f"Selected: {name}.txd ({sz}x{sz} {fmt.upper()})")
        self.lbl_spec_lm.config(text=f"Landmark: {lm}")
        self.lbl_spec_reg.config(text=f"Region: {reg}")
        self.lbl_spec_sz.config(text=f"Binary: {len(txd):,} bytes ({round(len(txd)/1024, 1)} KB)")

        # Render Hex
        self.txt_hex.delete("1.0", "end")
        lines = [
            f"=== RenderWare Chunk Hierarchy [{name}.txd] ===",
            f"├── rwID_TEXDICTIONARY (0x16) [{len(txd)-12:,} bytes | RW 3.6.0.3]",
            f"│   ├── rwID_STRUCT (0x01) [Count: 1, D3D]",
            f"│   └── rwID_TEXTURENATIVE (0x15) [Platform: D3D9]",
            f"│       └── rwID_STRUCT (0x01) [{fmt.upper()}, {sz}x{sz}]",
            "",
            "=== Hex Dump (First 160 Bytes) ===",
            "OFFSET   00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  ASCII",
        ]
        for off in range(0, min(len(txd), 160), 16):
            chk = txd[off:off+16]
            h_str = " ".join(f"{b:02X}" for b in chk).ljust(48)
            a_str = "".join(chr(b) if 32 <= b <= 126 else "·" for b in chk)
            lines.append(f"{off:08X} {h_str}  {a_str}")
        self.txt_hex.insert("1.0", "\n".join(lines))

    def save_single_txd(self):
        if not self.current_txd_bytes: return
        f = filedialog.asksaveasfilename(initialfile=f"radar{self.selected_tile_idx:02d}.txd", defaultextension=".txd")
        if f:
            with open(f, "wb") as fp: fp.write(self.current_txd_bytes)
            messagebox.showinfo("Saved!", f"Exported {os.path.basename(f)} successfully!")

    def batch_export_dialog(self):
        zip_path = filedialog.asksaveasfilename(initialfile="GTA_SA_Radar_Mod_144Tiles.zip", defaultextension=".zip")
        if not zip_path: return
        threading.Thread(target=self.run_zip_export, args=(zip_path,), daemon=True).start()

    def run_zip_export(self, zip_path):
        self.btn_batch.config(state="disabled")
        sz, fmt = self.res_var.get(), self.fmt_var.get()
        w, h = self.source_map_image.size
        try:
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("GTA_SA_Radar_Mod/README.txt", f"GTA SA Radar Mod (144 Tiles)\nCopy into GTA San Andreas/modloader/\nRes: {sz}x{sz} {fmt.upper()}\n")
                for i in range(144):
                    r, c = i // 12, i % 12
                    name = f"radar{i:02d}"
                    x0 = round((c * w) / 12)
                    x1 = round(((c + 1) * w) / 12)
                    y0 = round((r * h) / 12)
                    y1 = round(((r + 1) * h) / 12)
                    tile = self.source_map_image.crop((x0, y0, x1, y1)).resize((sz, sz), Image.Resampling.LANCZOS)
                    zf.writestr(f"GTA_SA_Radar_Mod/{name}.txd", build_radar_txd(name, tile, fmt))
                    self.prog["value"] = int(((i + 1) / 144) * 100)
                    self.lbl_status.config(text=f"Packaging {name}.txd ({i+1}/144)...")
                    self.root.update_idletasks()
            messagebox.showinfo("Success!", f"Successfully created 144 radar TXD files in:\n{zip_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed:\n{e}")
        finally:
            self.btn_batch.config(state="normal")
            self.prog["value"] = 0
            self.lbl_status.config(text="Ready.")

if __name__ == '__main__':
    root = tk.Tk()
    app = GtaSaRadarStudioApp(root)
    root.mainloop()