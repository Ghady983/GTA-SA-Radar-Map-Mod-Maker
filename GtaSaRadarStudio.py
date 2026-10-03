#!/usr/bin/env python3
"""
GTA San Andreas Radar Map Maker - Interactive Desktop Studio
Supports both DXT1 (Opaque) and BGRA32 (Transparent) Native TXD generation.
"""

import os
import sys
import struct
import zipfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller bundle execution."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

def load_spec_config():
    """Reads APP_NAME, APP_ICON, and APP_VERSION directly from GtaSaRadarStudio.spec if present."""
    app_name = "GTA SA Radar Map Mod Maker"
    app_icon = "icon.ico"
    app_version = "1.0.1"
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
FOURCC_DXT1 = 0x31545844  # 'DXT1' identifier for compressed mode
D3DFMT_A8R8G8B8 = 21       # 32-bit BGRA identifier for transparent mode

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
    96: ("South-West Coast Waters", "Ocean / Coast"),
    97: ("Whetstone South Coast", "Whetstone"),
    98: ("Flint County South Shoreline", "Flint County"),
    99: ("Santa Maria Beach Pier & Lighthouse", "Los Santos"),
    100: ("Marina Canal / Los Santos Beach", "Los Santos"),
    101: ("Verona Beach / Conference Center", "Los Santos"),
    102: ("Idlewood / Corona / Unity Station", "Los Santos"),
    103: ("Willowfield / Ocean Docks North", "Los Santos"),
    104: ("East Beach South / Ocean Docks", "Los Santos"),
    105: ("South-East Waters (Los Santos Harbor)", "Ocean / Coast"),
    106: ("Far South-East Ocean", "Ocean / Coast"),
    107: ("Far South-East Ocean Outer", "Ocean / Coast"),
    108: ("Far South Ocean", "Ocean / Coast"),
    109: ("Far South Ocean", "Ocean / Coast"),
    110: ("Los Santos International (LSX Runways)", "Los Santos"),
    111: ("LSX Terminal & Freight Depot", "Los Santos"),
    112: ("Ocean Docks (Container Cranes)", "Los Santos"),
    113: ("Ocean Docks South Industrial", "Los Santos"),
    114: ("South Ocean Boundary", "Ocean / Coast"),
    115: ("South Ocean Boundary", "Ocean / Coast"),
    116: ("South Ocean Boundary", "Ocean / Coast"),
    117: ("South Ocean Boundary", "Ocean / Coast"),
    118: ("South Ocean Boundary", "Ocean / Coast"),
    119: ("South Ocean Boundary", "Ocean / Coast"),
    120: ("South Ocean Boundary", "Ocean / Coast"),
    121: ("South-West Ocean Outer", "Ocean / Coast"),
    122: ("South-West Ocean Outer", "Ocean / Coast"),
    123: ("South Ocean Off LSX", "Ocean / Coast"),
    124: ("South Ocean Off LSX", "Ocean / Coast"),
    125: ("South Ocean Waters", "Ocean / Coast"),
    126: ("South Ocean Waters", "Ocean / Coast"),
    127: ("South Ocean Waters", "Ocean / Coast"),
    128: ("South Ocean Waters", "Ocean / Coast"),
    129: ("South Ocean Waters", "Ocean / Coast"),
    130: ("South Ocean Waters", "Ocean / Coast"),
    131: ("South Ocean Waters", "Ocean / Coast"),
    132: ("South Ocean Waters", "Ocean / Coast"),
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
        raster_format = 0x0200  # rwRASTERFORMAT565
        d3d_format = FOURCC_DXT1
        depth = 16
        compression_flag = 0x08
    else:
        r, g, b, a = img.split()
        bgra_img = Image.merge('RGBA', (b, g, r, a))
        tex_bytes = bgra_img.tobytes()
        raster_format = 0x0500  # rwRASTERFORMAT8888
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

def create_checkerboard_image(width: int, height: int, cell_size: int = 16) -> Image.Image:
    """Generates a transparency checkerboard pattern."""
    img = Image.new('RGB', (width, height), (24, 24, 27))
    draw = ImageDraw.Draw(img)
    for y in range(0, height, cell_size):
        for x in range(0, width, cell_size):
            if ((x // cell_size) + (y // cell_size)) % 2 == 0:
                draw.rectangle([x, y, x + cell_size - 1, y + cell_size - 1], fill=(39, 39, 42))
    return img

def generate_sample_san_andreas_map(size: int = 1536, theme: str = 'satellite') -> Image.Image:
    if theme == 'transparent_islands':
        img = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    else:
        img = Image.new('RGB', (size, size), color=(18, 37, 56))
    draw = ImageDraw.Draw(img)
    palettes = {
        'satellite': {'deep': (18, 37, 56), 'land': (67, 88, 52), 'desert': (169, 140, 86), 'urban': (88, 88, 96), 'river': (39, 75, 107), 'freeway': (220, 166, 66), 'runway': (43, 43, 49), 'chiliad': (92, 82, 67), 'grove': (27, 77, 36)},
        'tactical_dark': {'deep': (9, 13, 22), 'land': (30, 41, 59), 'desert': (51, 65, 85), 'urban': (59, 66, 82), 'river': (30, 58, 138), 'freeway': (56, 189, 248), 'runway': (17, 24, 39), 'chiliad': (37, 46, 62), 'grove': (34, 197, 94)},
        'vintage_1992': {'deep': (166, 184, 190), 'land': (210, 202, 169), 'desert': (221, 199, 158), 'urban': (191, 184, 165), 'river': (152, 173, 183), 'freeway': (194, 88, 56), 'runway': (96, 88, 80), 'chiliad': (185, 168, 136), 'grove': (114, 136, 96)},
        'transparent_islands': {'deep': (0, 0, 0, 0), 'land': (56, 94, 56, 255), 'desert': (191, 161, 106, 255), 'urban': (72, 76, 86, 255), 'river': (25, 80, 140, 200), 'freeway': (251, 191, 36, 255), 'runway': (31, 41, 55, 255), 'chiliad': (97, 83, 64, 255), 'grove': (22, 163, 74, 255)}
    }.get(theme, {})

    def to_cx(wx): return int(((wx + 3000) / 6000) * size)
    def to_cy(wy): return int(((3000 - wy) / 6000) * size)

    if theme != 'transparent_islands':
        draw.rectangle([0, 0, size, size], fill=palettes.get('deep', (18, 37, 56)))
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
        self.root.geometry("1280x860")
        self.root.minsize(1120, 740)
        self.root.configure(bg="#09090b")

        self.set_app_icon()

        self.current_theme = 'satellite'
        self.custom_image = None
        self.source_map_image = None
        self.display_map_image = None  # Downsampled static preview cache for fast grid rendering
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
        self.btn_trans = tk.Button(mid, text="Transparent", font=("Segoe UI", 8), bg="#27272a", fg="#38bdf8", command=lambda: self.load_theme_map('transparent_islands'), relief="flat", padx=8, pady=3)
        self.btn_trans.pack(side="left", padx=2)
        self.btn_upload = tk.Button(mid, text="Custom Image...", font=("Segoe UI", 8, "bold"), bg="#3f3f46", fg="#ffffff", command=self.upload_custom_map, relief="flat", padx=10, pady=3)
        self.btn_upload.pack(side="left", padx=(8, 2))

        right = tk.Frame(hdr, bg="#18181b")
        right.pack(side="right", padx=12, pady=8)
        self.btn_batch = tk.Button(right, text="Export All 144 TXDs (ZIP)", font=("Segoe UI", 9, "bold"), bg="#f59e0b", fg="#09090b", command=self.batch_export_dialog, padx=14, pady=5, relief="flat", cursor="hand2")
        self.btn_batch.pack()

        main = tk.Frame(self.root, bg="#09090b")
        main.pack(fill="both", expand=True, padx=16, pady=4)

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

        right_p = tk.Frame(main, bg="#09090b", width=540)
        right_p.pack(side="right", fill="both", padx=(6, 0), pady=4)
        right_p.pack_propagate(False)

        t_card = tk.Frame(right_p, bg="#18181b", bd=1, relief="solid")
        t_card.pack(fill="x", pady=(0, 4))
        th = tk.Frame(t_card, bg="#18181b")
        th.pack(fill="x", padx=10, pady=6)
        self.lbl_tile_name = tk.Label(th, text="Selected: radar00.txd", font=("Segoe UI", 9, "bold"), fg="#f59e0b", bg="#18181b")
        self.lbl_tile_name.pack(side="left")
        tk.Button(th, text="Save .txd", font=("Segoe UI", 8, "bold"), bg="#f59e0b", fg="#09090b", command=self.save_single_txd, relief="flat", padx=6, pady=1).pack(side="right")

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

        cfg = tk.Frame(right_p, bg="#18181b", bd=1, relief="solid")
        cfg.pack(fill="x", pady=4)

        r_row = tk.Frame(cfg, bg="#18181b")
        r_row.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(r_row, text="Res:", font=("Segoe UI", 8, "bold"), fg="#71717a", bg="#18181b").pack(side="left", padx=(0, 4))

        self.res_var = tk.IntVar(value=256)

        for r_val, r_txt in [(256, "256p"), (512, "512p"), (1024, "1024p")]:
            tk.Radiobutton(r_row, text=r_txt, variable=self.res_var, value=r_val, command=self.on_preset_res_selected, bg="#18181b", fg="#ffffff", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8)).pack(side="left")

        self.btn_auto_res = tk.Radiobutton(r_row, text="Auto (Img/12)", variable=self.res_var, value=-1, command=self.on_auto_res_selected, bg="#18181b", fg="#38bdf8", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8, "bold"))
        self.btn_auto_res.pack(side="left", padx=(4, 2))

        tk.Radiobutton(r_row, text="Custom:", variable=self.res_var, value=-2, command=self.on_custom_res_selected, bg="#18181b", fg="#fbbf24", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8)).pack(side="left", padx=(4, 1))
        self.entry_custom_res = tk.Entry(r_row, width=5, bg="#09090b", fg="#fbbf24", font=("Consolas", 8, "bold"), insertbackground="#fbbf24", bd=1, relief="solid")
        self.entry_custom_res.insert(0, "667")
        self.entry_custom_res.pack(side="left", padx=1)
        self.entry_custom_res.bind("<Return>", lambda e: self.on_custom_res_enter())
        self.entry_custom_res.bind("<FocusOut>", lambda e: self.on_custom_res_enter())
        self.entry_custom_res.bind("<KeyRelease>", self.on_custom_res_key)
        self.entry_custom_res.bind("<FocusIn>", self.on_custom_res_focus)
        tk.Label(r_row, text="px", font=("Segoe UI", 7), fg="#71717a", bg="#18181b").pack(side="left", padx=1)

        f_row = tk.Frame(cfg, bg="#18181b")
        f_row.pack(fill="x", padx=8, pady=(2, 6))
        tk.Label(f_row, text="Format:", font=("Segoe UI", 8, "bold"), fg="#71717a", bg="#18181b").pack(side="left", padx=(0, 4))
        self.fmt_var = tk.StringVar(value="bgra32")
        tk.Radiobutton(f_row, text="BGRA32 (Recommended)", variable=self.fmt_var, value="bgra32", command=self.on_fmt_changed, bg="#18181b", fg="#ffffff", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Radiobutton(f_row, text="DXT1", variable=self.fmt_var, value="dxt1", command=self.on_fmt_changed, bg="#18181b", fg="#a1a1aa", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8)).pack(side="left", padx=(4, 0))

        self.var_trans = tk.BooleanVar(value=False)
        tk.Checkbutton(f_row, text="Transparent (Preserve Alpha)", variable=self.var_trans, command=self.on_trans_toggle, bg="#18181b", fg="#38bdf8", selectcolor="#09090b", activebackground="#18181b", font=("Segoe UI", 8, "bold")).pack(side="left", padx=(10, 2))

        hx = tk.Frame(right_p, bg="#18181b", bd=1, relief="solid")
        hx.pack(fill="both", expand=True, pady=(4, 0))
        tk.Label(hx, text="RenderWare TXD Chunk & Hex Dump Inspector", font=("Segoe UI", 8, "bold"), fg="#f4f4f5", bg="#18181b").pack(anchor="w", padx=8, pady=4)
        self.txt_hex = tk.Text(hx, bg="#09090b", fg="#d4d4d8", font=("Consolas", 8), bd=0, padx=6, pady=6)
        self.txt_hex.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        btm = tk.Frame(self.root, bg="#18181b", bd=1, relief="solid")
        btm.pack(fill="x", side="bottom", padx=16, pady=(4, 10))
        self.lbl_status = tk.Label(btm, text="Ready.", font=("Segoe UI", 8), fg="#a1a1aa", bg="#18181b")
        self.lbl_status.pack(side="left", padx=10, pady=3)
        self.prog = ttk.Progressbar(btm, orient="horizontal", length=220, mode="determinate")
        self.prog.pack(side="right", padx=10, pady=3)

    def update_display_cache(self):
        """Creates a cached max-1024px preview image to prevent UI lag on high-res master maps."""
        if self.source_map_image:
            preview = self.source_map_image.copy()
            preview.thumbnail((1024, 1024), Image.Resampling.BILINEAR)
            self.display_map_image = preview

    def get_effective_resolution(self) -> int:
        val = self.res_var.get()
        # POT snapping is strictly enforced for opaque DXT1 textures to avoid D3D9 NPOT crashes
        is_dxt1 = (self.fmt_var.get() == "dxt1") and (not self.var_trans.get())

        if val == -1:
            if self.source_map_image:
                w, _ = self.source_map_image.size
                raw_res = max(16, round(w / 12.0))
                if is_dxt1:
                    pot_sizes = [64, 128, 256, 512, 1024, 2048, 4096]
                    return min(pot_sizes, key=lambda x: abs(x - raw_res))
                return raw_res
            return 256
        elif val == -2:
            try:
                c_val = int(self.entry_custom_res.get().strip())
                c_val = max(16, min(4096, c_val))
                if is_dxt1:
                    pot_sizes = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
                    return min(pot_sizes, key=lambda x: abs(x - c_val))
                return c_val
            except ValueError:
                return 256
        return val

    def on_preset_res_selected(self):
        self.update_tile()

    def on_auto_res_selected(self):
        calc = self.get_effective_resolution()
        if self.source_map_image:
            w, _ = self.source_map_image.size
            self.lbl_status.config(text=f"Auto calculated tile resolution: {calc}x{calc} px (from {w}px / 12)")
        self.update_tile()

    def on_custom_res_selected(self):
        self.entry_custom_res.focus_set()
        self.update_tile()

    def on_custom_res_enter(self):
        if self.res_var.get() == -2:
            self.update_tile()

    def on_custom_res_focus(self, event=None):
        self.res_var.set(-2)
        self.update_tile()

    def on_custom_res_key(self, event=None):
        self.res_var.set(-2)
        try:
            val = int(self.entry_custom_res.get().strip())
            if 16 <= val <= 4096:
                self.update_tile()
        except ValueError:
            pass

    def on_fmt_changed(self):
        if self.fmt_var.get() == "dxt1" and self.var_trans.get():
            self.var_trans.set(False)
            self.lbl_status.config(text="Transparency disabled: DXT1 format forces 100% opaque mode.")
        self.update_tile()

    def on_trans_toggle(self):
        if self.var_trans.get():
            self.fmt_var.set("bgra32")
            if not self.custom_image and self.current_theme != "transparent_islands":
                self.load_theme_map("transparent_islands")
            else:
                self.update_tile()
        else:
            if not self.custom_image and self.current_theme == "transparent_islands":
                self.load_theme_map("satellite")
            else:
                self.update_tile()

    def load_theme_map(self, theme_key: str):
        self.custom_image = None
        self.current_theme = theme_key
        
        self.btn_sat.config(bg="#27272a", fg="#d4d4d8")
        self.btn_dark.config(bg="#27272a", fg="#d4d4d8")
        self.btn_vint.config(bg="#27272a", fg="#d4d4d8")
        self.btn_trans.config(bg="#27272a", fg="#38bdf8")

        if theme_key == 'satellite':
            self.btn_sat.config(bg="#f59e0b", fg="#09090b")
            self.var_trans.set(False)
            self.fmt_var.set("dxt1")
        elif theme_key == 'tactical_dark':
            self.btn_dark.config(bg="#f59e0b", fg="#09090b")
            self.var_trans.set(False)
            self.fmt_var.set("dxt1")
        elif theme_key == 'vintage_1992':
            self.btn_vint.config(bg="#f59e0b", fg="#09090b")
            self.var_trans.set(False)
            self.fmt_var.set("dxt1")
        elif theme_key == 'transparent_islands':
            self.btn_trans.config(bg="#38bdf8", fg="#09090b")
            self.var_trans.set(True)
            self.fmt_var.set("bgra32")

        self.source_map_image = generate_sample_san_andreas_map(1536, theme_key)
        self.update_display_cache()
        self.redraw_grid()
        self.update_tile()

    def upload_custom_map(self):
        filePath = filedialog.askopenfilename(
            title="Select San Andreas Master Map Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp;*.tga")]
        )
        if not filePath:
            return

        try:
            loaded_img = Image.open(filePath)
            if loaded_img.mode != 'RGBA':
                loaded_img = loaded_img.convert('RGBA')

            self.custom_image = loaded_img
            self.source_map_image = loaded_img
            self.update_display_cache()

            has_alpha = False
            alpha = loaded_img.split()[3]
            min_a, max_a = alpha.getextrema()
            if min_a < 255:
                has_alpha = True

            if has_alpha:
                self.var_trans.set(True)
                self.fmt_var.set("bgra32")
                self.lbl_status.config(text=f"Custom image loaded ({loaded_img.width}x{loaded_img.height}). Alpha channel detected -> Enabled Transparency.")
            else:
                self.var_trans.set(False)
                self.fmt_var.set("dxt1")
                self.lbl_status.config(text=f"Custom image loaded ({loaded_img.width}x{loaded_img.height}). Opaque image -> Enabled DXT1.")

            self.redraw_grid()
            self.update_tile()

        except Exception as ex:
            messagebox.showerror("Error", f"Failed to load image:\n{ex}")

    def redraw_grid(self):
        if not self.display_map_image:
            return

        sz = self.grid_canvas_size
        thumb = self.display_map_image.resize((sz, sz), Image.Resampling.BILINEAR)
        
        if self.var_trans.get() or self.display_map_image.mode == 'RGBA':
            bg_checker = create_checkerboard_image(sz, sz, cell_size=12)
            bg_checker.paste(thumb, (0, 0), thumb)
            composite_img = bg_checker
        else:
            composite_img = thumb

        self.cached_tk_map = ImageTk.PhotoImage(composite_img)
        self.map_canvas.delete("all")
        self.map_canvas.create_image(0, 0, image=self.cached_tk_map, anchor="nw")

        cell_sz = sz / 12.0
        if self.grid_var.get():
            for i in range(13):
                pos = i * cell_sz
                self.map_canvas.create_line(pos, 0, pos, sz, fill="#3f3f46", width=1)
                self.map_canvas.create_line(0, pos, sz, pos, fill="#3f3f46", width=1)

        if self.hovered_tile_idx is not None and self.hovered_tile_idx != self.selected_tile_idx:
            hr = self.hovered_tile_idx // 12
            hc = self.hovered_tile_idx % 12
            self.map_canvas.create_rectangle(
                hc * cell_sz, hr * cell_sz, (hc + 1) * cell_sz, (hr + 1) * cell_sz,
                outline="#38bdf8", width=2
            )

        sr = self.selected_tile_idx // 12
        sc = self.selected_tile_idx % 12
        self.map_canvas.create_rectangle(
            sc * cell_sz, sr * cell_sz, (sc + 1) * cell_sz, (sr + 1) * cell_sz,
            outline="#f59e0b", width=3
        )

    def on_click(self, event):
        cell_sz = self.grid_canvas_size / 12.0
        col = int(event.x // cell_sz)
        row = int(event.y // cell_sz)
        if 0 <= col < 12 and 0 <= row < 12:
            self.selected_tile_idx = row * 12 + col
            self.redraw_grid()
            self.update_tile()

    def on_motion(self, event):
        cell_sz = self.grid_canvas_size / 12.0
        col = int(event.x // cell_sz)
        row = int(event.y // cell_sz)
        if 0 <= col < 12 and 0 <= row < 12:
            idx = row * 12 + col
            self.set_hover(idx)
        else:
            self.set_hover(None)

    def set_hover(self, idx):
        if self.hovered_tile_idx != idx:
            self.hovered_tile_idx = idx
            self.redraw_grid()
            if idx is not None:
                lm, reg = LANDMARK_MAP.get(idx, ("Unknown", "San Andreas"))
                col = idx % 12
                row = idx // 12
                wx = int(-3000 + (col + 0.5) * 500)
                wy = int(3000 - (row + 0.5) * 500)
                self.readout.config(text=f"Hover: radar{idx:02d}.txd | {lm} ({reg}) | World: X:{wx}, Y:{wy}")

    def update_tile(self):
        if not self.source_map_image:
            return

        idx = self.selected_tile_idx
        row = idx // 12
        col = idx % 12

        w, h = self.source_map_image.size
        cw, ch = w / 12.0, h / 12.0
        crop_box = (int(col * cw), int(row * ch), int((col + 1) * cw), int((row + 1) * ch))

        tile_crop = self.source_map_image.crop(crop_box)
        target_res = self.get_effective_resolution()
        
        tile_name = f"radar{idx:02d}"
        fmt = self.fmt_var.get()
        if self.var_trans.get():
            fmt = "bgra32"

        # ALWAYS use a fixed static resolution (128x128 max) for interactive UI encoding.
        # This keeps software DXT1 compression instant (<2ms) while keeping final export high-res.
        preview_res = min(target_res, 128)
        tile_preview_resized = tile_crop.resize((preview_res, preview_res), Image.Resampling.BILINEAR)
        self.current_txd_bytes = build_radar_txd(tile_name, tile_preview_resized, format_type=fmt)

        # Calculate exact target output file size for the UI readout label
        overhead_bytes = 168
        if fmt == "bgra32":
            data_bytes = target_res * target_res * 4
        else:
            data_bytes = (target_res * target_res) // 2
        expected_total_bytes = overhead_bytes + data_bytes

        # Static 140x140 UI preview canvas rendering
        prev_sz = 140
        prev_img = tile_crop.resize((prev_sz, prev_sz), Image.Resampling.BILINEAR)
        if self.var_trans.get() or prev_img.mode == 'RGBA':
            bg = create_checkerboard_image(prev_sz, prev_sz, cell_size=10)
            bg.paste(prev_img, (0, 0), prev_img)
            display_img = bg
        else:
            display_img = prev_img

        self._cached_prev_tk = ImageTk.PhotoImage(display_img)
        self.prev_canvas.delete("all")
        self.prev_canvas.create_image(0, 0, image=self._cached_prev_tk, anchor="nw")

        lm, reg = LANDMARK_MAP.get(idx, ("Unknown Region", "San Andreas"))
        self.lbl_tile_name.config(text=f"Selected: {tile_name}.txd")
        self.lbl_spec_lm.config(text=f"Landmark: {lm}")
        self.lbl_spec_reg.config(text=f"Region: {reg}")
        self.lbl_spec_sz.config(text=f"Binary: {expected_total_bytes:,} bytes ({target_res}x{target_res}px)")

        self.update_hex_dump()

    def update_hex_dump(self):
        self.txt_hex.delete("1.0", tk.END)
        data = self.current_txd_bytes
        if not data:
            return

        lines = []
        lines.append("=== RenderWare TXD Chunk Inspector ===")
        lines.append(f"Root Chunk  : 0x16 (TEXDICTIONARY) | Fast UI Preview Mode")
        
        mode_text = '32-bit BGRA (D3DFMT_A8R8G8B8)' if self.fmt_var.get() == 'bgra32' or self.var_trans.get() else '16-bit DXT1 Compressed'
        lines.append(f"Format Mode : {mode_text}")
        lines.append("=" * 45)
        lines.append("Offset   Hex Dump                         ASCII")
        lines.append("-" * 45)

        preview_len = min(256, len(data))
        for i in range(0, preview_len, 16):
            chunk = data[i:i+16]
            hex_str = " ".join(f"{b:02X}" for b in chunk)
            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            lines.append(f"{i:04X}     {hex_str:<47} {ascii_str}")

        if len(data) > preview_len:
            lines.append(f"... ({len(data) - preview_len} bytes remaining)")

        self.txt_hex.insert(tk.END, "\n".join(lines))

    def save_single_txd(self):
        if not self.source_map_image:
            return
        idx = self.selected_tile_idx
        default_name = f"radar{idx:02d}.txd"
        file_path = filedialog.asksaveasfilename(
            title="Save Radar Tile TXD",
            initialfile=default_name,
            defaultextension=".txd",
            filetypes=[("RenderWare Texture Dictionary", "*.txd")]
        )
        if file_path:
            try:
                self.lbl_status.config(text=f"Encoding single tile at target resolution...")
                self.root.update_idletasks()

                res = self.get_effective_resolution()
                fmt = self.fmt_var.get()
                if self.var_trans.get():
                    fmt = "bgra32"

                w, h = self.source_map_image.size
                cw, ch = w / 12.0, h / 12.0
                row = idx // 12
                col = idx % 12
                crop_box = (int(col * cw), int(row * ch), int((col + 1) * cw), int((row + 1) * ch))

                tile_crop = self.source_map_image.crop(crop_box)
                tile_resized = tile_crop.resize((res, res), Image.Resampling.LANCZOS)
                
                tile_name = f"radar{idx:02d}"
                full_res_bytes = build_radar_txd(tile_name, tile_resized, format_type=fmt)

                with open(file_path, "wb") as f:
                    f.write(full_res_bytes)
                self.lbl_status.config(text=f"Saved single tile -> {os.path.basename(file_path)} ({res}x{res}px)")
                messagebox.showinfo("Saved", f"Successfully saved {os.path.basename(file_path)} at {res}x{res}px!")
            except Exception as ex:
                messagebox.showerror("Save Error", f"Failed to save file:\n{ex}")

    def batch_export_dialog(self):
        if not self.source_map_image:
            return

        file_path = filedialog.asksaveasfilename(
            title="Export All 144 Radar Tiles to ZIP Archive",
            initialfile="GTA_SA_Radar_144_Tiles.zip",
            defaultextension=".zip",
            filetypes=[("ZIP Archive", "*.zip")]
        )
        if not file_path:
            return

        self.btn_batch.config(state="disabled")
        self.prog["value"] = 0

        def run_export():
            try:
                res = self.get_effective_resolution()
                fmt = self.fmt_var.get()
                if self.var_trans.get():
                    fmt = "bgra32"

                w, h = self.source_map_image.size
                cw, ch = w / 12.0, h / 12.0

                with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for idx in range(144):
                        row = idx // 12
                        col = idx % 12
                        box = (int(col * cw), int(row * ch), int((col + 1) * cw), int((row + 1) * ch))
                        tile_crop = self.source_map_image.crop(box)
                        tile_resized = tile_crop.resize((res, res), Image.Resampling.LANCZOS)
                        
                        txd_name = f"radar{idx:02d}"
                        txd_bytes = build_radar_txd(txd_name, tile_resized, format_type=fmt)
                        zf.writestr(f"{txd_name}.txd", txd_bytes)

                        prog_val = int(((idx + 1) / 144.0) * 100)
                        self.root.after(0, lambda v=prog_val, i=idx: self.update_batch_progress(v, i))

                self.root.after(0, lambda: self.finish_batch_export(file_path))

            except Exception as ex:
                self.root.after(0, lambda e=str(ex): messagebox.showerror("Export Error", f"Failed batch export:\n{e}"))
                self.root.after(0, lambda: self.btn_batch.config(state="normal"))

        threading.Thread(target=run_export, daemon=True).start()

    def update_batch_progress(self, val, idx):
        self.prog["value"] = val
        self.lbl_status.config(text=f"Batch exporting: radar{idx:02d}.txd ({idx+1}/144)...")

    def finish_batch_export(self, file_path):
        self.btn_batch.config(state="normal")
        self.lbl_status.config(text=f"Export Complete! All 144 TXDs saved to ZIP.")
        messagebox.showinfo("Export Complete", f"Successfully generated all 144 GTA SA radar TXD files!\n\nSaved to:\n{file_path}")

if __name__ == '__main__':
    root = tk.Tk()
    app = GtaSaRadarStudioApp(root)
    root.mainloop()