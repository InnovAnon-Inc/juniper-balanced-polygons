#! /usr/bin/env python

import asyncio
import json
import math
import threading
from flask import Flask, render_template, request, jsonify
import webcolors
import websockets

app = Flask(__name__)

# ==========================================
# CONSTANTS & PHYSICAL LOGIC
# ==========================================
A4_FREQ = 432.0         # Reference tuning standard
SPEED_OF_LIGHT = 3e8    # m/s
LAMBDA_MIN = 380.0      # Visible violet limit (nm)
LAMBDA_MAX = 780.0      # Visible red limit (nm)

QUARTER_NOTE_NAMES = [
    "A", "A‡", "A#", "B♭‡", "B", "C", "C‡", "C#", "D♭‡", "D", "D‡", "D#",
    "E♭‡", "E", "F", "F‡", "F#", "G♭‡", "G", "G‡", "G#", "A♭‡", "A‡ (High)", "A# (High)"
]

CHORD_PRESETS = {
    "maj": {"name": "Major Triad (+ Octave)", "steps": [0, 8, 14, 24]},
    "min": {"name": "Minor Triad (+ Octave)", "steps": [0, 6, 14, 24]},
    "dim": {"name": "Diminished Triad (+ Octave)", "steps": [0, 6, 12, 24]},
    "halfdim7": {"name": "Half Diminished 7th", "steps": [0, 6, 12, 20]},
    "dim7": {"name": "Fully Diminished 7th", "steps": [0, 6, 12, 18]},
    "aug": {"name": "Augmented Triad (+ Octave)", "steps": [0, 8, 16, 24]},
    "dom7": {"name": "Dominant 7th", "steps": [0, 8, 14, 20]},
    "maj7": {"name": "Major 7th", "steps": [0, 8, 14, 22]},
    "min7": {"name": "Minor 7th", "steps": [0, 6, 14, 20]},
    "minmaj7": {"name": "Minor Major 7th", "steps": [0, 8, 14, 22]},
}

NOTE_TO_QUARTERTONE = {
    'C': 5, 'C#': 7, 'Db': 7, 'D': 9, 'D#': 11, 'Eb': 11,
    'E': 13, 'F': 14, 'F#': 16, 'Gb': 16, 'G': 17, 'G#': 19,
    'Ab': 19, 'A': 0, 'A#': 2, 'Bb': 2, 'B': 4
}

latest_chimes_data = {}

def get_color_name(requested_rgb):
    try:
        if hasattr(webcolors, 'rgb_to_name'):
            return webcolors.rgb_to_name(requested_rgb)
    except (ValueError, AttributeError):
        pass

    rgb_map = {}
    if hasattr(webcolors, 'CSS3_HEX_TO_NAMES'):
        for hex_code, name in webcolors.CSS3_HEX_TO_NAMES.items():
            h = hex_code.lstrip('#')
            rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            rgb_map[rgb] = name
    elif hasattr(webcolors, 'names'):
        for name in webcolors.names("css3"):
            try:
                rgb = webcolors.name_to_rgb(name)
                rgb_map[rgb] = name
            except Exception:
                continue

    if not rgb_map:
        return "Unknown"

    min_distance = float("inf")
    closest_name = "Unknown"

    for rgb, name in rgb_map.items():
        d = math.sqrt((rgb[0] - requested_rgb[0])**2 + (rgb[1] - requested_rgb[1])**2 + (rgb[2] - requested_rgb[2])**2)
        if d < min_distance:
            min_distance = d
            closest_name = name

    return closest_name.title() if min_distance == 0 else f"{closest_name.title()} (approx)"


def rgb_to_hsv(r, g, b):
    r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
    mx = max(r_norm, g_norm, b_norm)
    mn = min(r_norm, g_norm, b_norm)
    df = mx - mn

    if mx == mn:
        h = 0
    elif mx == r_norm:
        h = (60 * ((g_norm - b_norm) / df) + 360) % 360
    elif mx == g_norm:
        h = (60 * ((b_norm - r_norm) / df) + 120) % 360
    elif mx == b_norm:
        h = (60 * ((r_norm - g_norm) / df) + 240) % 360

    return round(h, 2)


def hsv_to_rgb(h, s=1.0, v=1.0):
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c

    if 0 <= h < 60:
        r_p, g_p, b_p = c, x, 0
    elif 60 <= h < 120:
        r_p, g_p, b_p = x, c, 0
    elif 120 <= h < 180:
        r_p, g_p, b_p = 0, c, x
    elif 180 <= h < 240:
        r_p, g_p, b_p = 0, x, c
    elif 240 <= h < 300:
        r_p, g_p, b_p = x, 0, c
    else:
        r_p, g_p, b_p = c, 0, x

    return int(round((r_p + m) * 255)), int(round((g_p + m) * 255)), int(round((b_p + m) * 255))


def calculate_single_voice(r, g, b):
    color_name = get_color_name((r, g, b))
    hue = rgb_to_hsv(r, g, b)

    quarter_index = int(round((hue / 360.0) * 23)) % 24
    closest_24_note = QUARTER_NOTE_NAMES[quarter_index]

    wavelength_nm = LAMBDA_MIN + (hue / 360.0) * (LAMBDA_MAX - LAMBDA_MIN)
    light_freq_hz = SPEED_OF_LIGHT / (wavelength_nm * 1e-9)

    audible_freq = A4_FREQ * (2 ** (quarter_index / 24.0))

    n_semitones = 12 * math.log2(audible_freq / A4_FREQ)
    semitone_ratio = 2 ** ((n_semitones % 12) / 12)
    chromatic_names = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
    closest_12_note = chromatic_names[int(round(n_semitones % 12)) % 12]

    return {
        "color_name": color_name,
        "hsv_hue": hue,
        "wavelength_nm": round(wavelength_nm, 2),
        "light_freq_thz": round(light_freq_hz / 1e12, 2),
        "audible_freq_hz": round(audible_freq, 2),
        "closest_note": f"{closest_12_note} ({round(semitone_ratio, 3)}:1 ratio)",
        "quartertone_note": closest_24_note,
        "quartertone_index": quarter_index,
        "r": r, "g": g, "b": b
    }


def calculate_note_to_color(quartertone_index):
    quartertone_index = quartertone_index % 24
    hue = (quartertone_index / 23.0) * 360.0
    r, g, b = hsv_to_rgb(hue)
    res = calculate_single_voice(r, g, b)
    res["quartertone_index"] = quartertone_index
    res["quartertone_note"] = QUARTER_NOTE_NAMES[quartertone_index]
    return res


def convert_note_list_to_colors(note_list):
    colors = []
    for note in note_list:
        clean_note = ''.join([c for c in note if not c.isdigit()])
        q_idx = NOTE_TO_QUARTERTONE.get(clean_note, 0)
        colors.append(calculate_note_to_color(q_idx))
    return colors

# ==========================================
# CHIMES SERVER WEBSOCKET LISTENER
# ==========================================
async def listen_to_chimes():
    global latest_chimes_data
    uri = "ws://127.0.0.1:65432"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    inner_colors = convert_note_list_to_colors(data.get("chord", []))
                    outer_colors = convert_note_list_to_colors(data.get("outer_chord", []))

                    latest_chimes_data = {
                        "tick": data.get("tick"),
                        "inner_hand": {
                            "key": data.get("key"),
                            "mode": data.get("mode"),
                            "chord_name": data.get("chord_name"),
                            "notes": data.get("chord"),
                            "colors": inner_colors
                        },
                        "outer_hand": {
                            "key": data.get("outer_key"),
                            "mode": data.get("outer_mode"),
                            "chord_name": data.get("outer_chord_name"),
                            "notes": data.get("outer_chord"),
                            "colors": outer_colors
                        }
                    }
        except Exception:
            await asyncio.sleep(2)

def start_chimes_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen_to_chimes())

# ==========================================
# FLASK WEB INTERFACE & ENDPOINTS
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    req = request.json or {}
    r, g, b = int(req.get('r', 0)), int(req.get('g', 0)), int(req.get('b', 0))
    return jsonify(calculate_single_voice(r, g, b))

@app.route('/calculate_note', methods=['POST'])
def calculate_note():
    req = request.json or {}
    note_index = int(req.get('note_index', 0))
    return jsonify(calculate_note_to_color(note_index))

@app.route('/sync_chimes', methods=['POST'])
def sync_chimes():
    data = request.json or {}
    inner_colors = convert_note_list_to_colors(data.get("chord", []))
    outer_colors = convert_note_list_to_colors(data.get("outer_chord", []))
    return jsonify({
        "inner_colors": inner_colors,
        "outer_colors": outer_colors
    })

@app.route('/chimes_state', methods=['GET'])
def chimes_state():
    """Exposes current scales/chords and corresponding HSV/colors for external apps."""
    return jsonify(latest_chimes_data)

if __name__ == '__main__':
    threading.Thread(target=start_chimes_listener, daemon=True).start()
    app.run(host='0.0.0.0', port=5001)
