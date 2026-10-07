import cmath
import math
import requests
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# ==============================================================================
# RIGOROUS MATHEMATICAL & BALANCED RHYTHM ENGINE
# ==============================================================================

def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

def lcm(a: int, b: int) -> int:
    return (a * b) // gcd(a, b) if a and b else 0

def bjorklund(steps: int, pulses: int) -> list[int]:
    """Generates standard Bjorklund Euclidean rhythm E(pulses, steps)."""
    if pulses <= 0: return [0] * steps
    if pulses >= steps: return [1] * steps

    pattern = [[1] for _ in range(pulses)]
    remainder = [[0] for _ in range(steps - pulses)]

    while len(remainder) > 1:
        count = min(len(pattern), len(remainder))
        for i in range(count):
            pattern[i].extend(remainder.pop(0))

    pattern.extend(remainder)
    return [bit for group in pattern for bit in group]

def get_centroid(pattern: list[int], N: int) -> tuple[float, float]:
    if not pattern or sum(pattern) == 0:
        return 0.0, 0.0
    total_vector = 0j
    for i, active in enumerate(pattern):
        if active:
            angle = 2 * math.pi * i / N
            total_vector += cmath.exp(1j * angle)
    center = total_vector / sum(pattern)
    return center.real, center.imag

def is_strictly_balanced(pattern: list[int], N: int, tol: float = 1e-5) -> bool:
    cx, cy = get_centroid(pattern, N)
    return math.hypot(cx, cy) < tol

def is_regular_polygon(pattern: list[int], N: int) -> bool:
    k = sum(pattern)
    if k < 2 or N % k != 0:
        return False
    stride = N // k
    active_indices = [i for i, b in enumerate(pattern) if b]
    start = active_indices[0]
    expected = [(start + j * stride) % N for j in range(k)]
    return sorted(active_indices) == sorted(expected)

def analyze_pattern(pattern: list[int], N: int) -> dict:
    cx, cy = get_centroid(pattern, N)
    balanced = is_strictly_balanced(pattern, N)
    regular = is_regular_polygon(pattern, N) if balanced else False
    class_type = "Class 1 (Regular)" if regular else ("Class 2 (Composite)" if balanced else "Unbalanced")
    
    return {
        "pattern": pattern,
        "is_balanced": balanced,
        "class_type": class_type,
        "centroid": [round(cx, 5), round(cy, 5)],
        "dist_from_origin": round(math.hypot(cx, cy), 5)
    }

def generate_rhythm_library(N: int) -> dict:
    cyclotomic = []
    bjorklund_rhythms = []
    seen_cyc = set()
    seen_bjork = set()

    for k in range(1, N):
        pat = bjorklund(N, k)
        key = tuple(pat)
        if key not in seen_bjork:
            seen_bjork.add(key)
            info = analyze_pattern(pat, N)
            info["label"] = f"Euclidean E({k},{N})"
            info["is_coprime"] = gcd(k, N) == 1
            bjorklund_rhythms.append(info)

    total_combos = 1 << N
    step_size = max(1, total_combos // 4096)
    
    for i in range(1, total_combos, step_size):
        pat = [(i >> j) & 1 for j in range(N)]
        if is_strictly_balanced(pat, N):
            key = tuple(pat)
            if key not in seen_cyc:
                seen_cyc.add(key)
                info = analyze_pattern(pat, N)
                info["label"] = f"Cyclotomic {info['class_type']} ({sum(pat)} pulses)"
                cyclotomic.append(info)

    return {
        "cyclotomic": cyclotomic,
        "bjorklund": bjorklund_rhythms
    }

# ==============================================================================
# EXTERNAL SERVER SYNC & FLASK ROUTES
# ==============================================================================

@app.route('/api/library', methods=['GET'])
def get_library():
    n_steps = int(request.args.get('n', 12))
    lib = generate_rhythm_library(n_steps)
    return jsonify({"n": n_steps, "library": lib})

@app.route('/api/chimes_synesthesia', methods=['GET'])
def get_chimes_synesthesia():
    try:
        res = requests.get('http://127.0.0.1:5001/chimes_state', timeout=1.0)
        if res.status_code == 200 and res.json():
            return jsonify(res.json())
    except Exception:
        pass

    fallback_data = {
        "left_hand": {
            "chord_name": "Cmaj7 (LH)",
            "notes": ["C2", "G2", "B2", "E3"],
            "colors": [
                {"r": 255, "g": 87,  "b": 34,  "quartertone_note": "C2",  "quartertone_index": -19},
                {"r": 76,  "g": 175, "b": 80,  "quartertone_note": "G2",  "quartertone_index": -12},
                {"r": 33,  "g": 150, "b": 243, "quartertone_note": "B2",  "quartertone_index": -8},
                {"r": 255, "g": 193, "b": 7,   "quartertone_note": "E3",  "quartertone_index": -3}
            ]
        },
        "right_hand": {
            "chord_name": "Am9 (RH)",
            "notes": ["C4", "E4", "G4", "B4", "D5"],
            "colors": [
                {"r": 255, "g": 87,  "b": 34,  "quartertone_note": "C4",  "quartertone_index": 5},
                {"r": 255, "g": 193, "b": 7,   "quartertone_note": "E4",  "quartertone_index": 13},
                {"r": 76,  "g": 175, "b": 80,  "quartertone_note": "G4",  "quartertone_index": 17},
                {"r": 33,  "g": 150, "b": 243, "quartertone_note": "B4",  "quartertone_index": 21},
                {"r": 156, "g": 39,  "b": 176, "quartertone_note": "D5",  "quartertone_index": 25}
            ]
        }
    }
    return jsonify(fallback_data)

@app.route('/api/evaluate_voice_bitwise', methods=['POST'])
def evaluate_voice_bitwise():
    data = request.json
    polygons = data.get('polygons', [])
    N = data.get('N', 12)
    
    voices = {}
    for poly in polygons:
        tone_id = poly.get('tone_id')
        pat = poly.get('pattern', [0] * N)
        is_pos = poly.get('type') == 'positive'
        
        if tone_id not in voices:
            voices[tone_id] = {'pos': [0] * N, 'neg': [0] * N, 'tone_name': poly.get('tone_name')}
        
        for i in range(len(pat)):
            idx = i % N
            if pat[i]:
                if is_pos:
                    voices[tone_id]['pos'][idx] = 1
                else:
                    voices[tone_id]['neg'][idx] = 1

    global_combined_pattern = [0] * N
    voice_results = {}
    
    for tone_id, vdata in voices.items():
        res_pat = [1 if (pos and not neg) else 0 for pos, neg in zip(vdata['pos'], vdata['neg'])]
        voice_results[tone_id] = {
            "tone_name": vdata['tone_name'],
            "pattern": res_pat,
            "analysis": analyze_pattern(res_pat, N)
        }
        for i in range(N):
            if res_pat[i]:
                global_combined_pattern[i] = 1

    global_analysis = analyze_pattern(global_combined_pattern, N)

    return jsonify({
        "voices": voice_results,
        "global_analysis": global_analysis
    })

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# ==============================================================================
# FRONTEND INTERFACE
# ==============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Harmonic Milne Granular Polyrhythm Engine</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #121214;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 { margin-bottom: 5px; color: #4db6ac; }
        p.subtitle { color: #888; margin-top: 0; margin-bottom: 20px; text-align: center; }
        
        .top-bar {
            background: #1e1e24;
            padding: 15px 25px;
            border-radius: 8px;
            display: flex;
            gap: 20px;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        label { font-weight: bold; font-size: 14px; }
        input, button, select {
            background: #2a2a32;
            border: 1px solid #444;
            color: #fff;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
        }
        button { background: #00897b; cursor: pointer; font-weight: bold; }
        button:hover { background: #00bfa5; }
        
        .workspace {
            display: flex;
            gap: 25px;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 1450px;
            width: 100%;
        }
        
        .canvas-card {
            background: #1e1e24;
            padding: 20px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        canvas { background: #18181c; border-radius: 50%; border: 1px solid #333; }
        
        .panel {
            background: #1e1e24;
            padding: 15px;
            border-radius: 8px;
            width: 520px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .poly-item {
            background: #2a2a32;
            padding: 10px;
            border-radius: 6px;
            border-left: 6px solid #00e676;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .poly-item.negative { border-left-style: dashed; }

        .row { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
        .badge { font-size: 10px; padding: 2px 6px; border-radius: 3px; text-transform: uppercase; font-weight: bold; }
        .badge-bal { background: #2e7d32; color: #fff; }
        .badge-unbal { background: #c62828; color: #fff; }
        
        .status-box {
            background: #25252e;
            padding: 12px;
            border-radius: 6px;
            font-size: 13px;
            border-left: 4px solid #ffeb3b;
        }
    </style>
</head>
<body>

    <h1>Harmonic Cyclotomic & Euclidean Granular Engine</h1>
    <p class="subtitle">Precise Web Audio Clock Scheduler | Granular Tick Rotations | LCM Subdivisions</p>

    <div class="top-bar">
        <label for="n-input">Pulses (N):</label>
        <input type="number" id="n-input" value="12" min="3" max="32" style="width: 60px;">
        <button id="update-n-btn">Update N</button>

        <label for="bpm-input">Master BPM:</label>
        <input type="number" id="bpm-input" value="60" min="30" max="300" style="width: 65px;">

        <button onclick="syncChimes()">Sync Chimes Polychord</button>
        <button id="play-btn" onclick="togglePlay()">Play Poly-Rhythm</button>
    </div>

    <div class="workspace">
        <div class="canvas-card">
            <canvas id="polyCanvas" width="500" height="500"></canvas>
            <div class="status-box" id="bitwise-status" style="margin-top: 15px; width: 470px;">
                Evaluating voice-specific cancellation...
            </div>
        </div>

        <div class="panel">
            <h3>Polygons & Voice Stacks</h3>
            <div id="lcm-info" style="font-size: 13px; color: #00e676; font-weight: bold;">LCM Grid: 0 Divisions</div>
            <div id="chord-info" style="font-size: 12px; color: #888;">Active Polychord: Syncing...</div>
            <div id="polygons-container"></div>
            <button onclick="addPolygon()">+ Add Polygon</button>
        </div>
    </div>

    <script>
        const A4_FREQ = 432.0;
        let audioCtx = null;
        
        let rhythmLibrary = { cyclotomic: [], bjorklund: [] };
        let activeChordTones = [];
        let polygons = [];
        let voiceRatios = {};
        let isPlaying = false;
        
        // Lookahead Scheduler Variables
        let timerID = null;
        let currentLcmTick = 0;
        let nextTickTime = 0.0;
        const lookahead = 25.0; // ms
        const scheduleAheadTime = 0.1; // sec

        let globalLCMDivisions = 12;

        const HARMONIC_RATIOS = [
            { label: "1/4 (Whole)", ratio: 0.25 },
            { label: "1/2 (Half)", ratio: 0.5 },
            { label: "1/1 (Quarter)", ratio: 1.0 },
            { label: "3/2 (3-Tuplet)", ratio: 1.5 },
            { label: "2/1 (8th Note)", ratio: 2.0 },
            { label: "5/2 (5-Tuplet)", ratio: 2.5 },
            { label: "3/1 (3-8ths)", ratio: 3.0 },
            { label: "4/1 (16th Note)", ratio: 4.0 },
            { label: "5/1 (5-Tuplet 16ths)", ratio: 5.0 },
            { label: "8/1 (32nd Note)", ratio: 8.0 }
        ];

        function gcd(a, b) { return b === 0 ? a : gcd(b, a % b); }
        function lcm(a, b) { return (a * b) / gcd(a, b); }

        function calculateGlobalLCM() {
            const N = parseInt(document.getElementById('n-input').value);
            if (polygons.length === 0) return N;
            
            let currentLCM = N;
            polygons.forEach(p => {
                const effectiveSteps = Math.round(N * p.ratio);
                currentLCM = lcm(currentLCM, effectiveSteps);
            });
            return currentLCM;
        }

        function scheduleTone(time, freq, rgbColor, isPositive) {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();

            osc.type = isPositive ? 'sine' : 'sawtooth';
            const actualFreq = isPositive ? freq : freq / 2;
            
            osc.frequency.setValueAtTime(actualFreq, time);
            gain.gain.setValueAtTime(isPositive ? 0.35 : 0.15, time);
            gain.gain.exponentialRampToValueAtTime(0.001, time + 0.15);

            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start(time);
            osc.stop(time + 0.15);
        }

        async function syncChimes() {
            try {
                const res = await fetch('/api/chimes_synesthesia');
                const data = await res.json();
                activeChordTones = [];

                ['left_hand', 'right_hand', 'inner_hand'].forEach(handKey => {
                    if (data[handKey] && data[handKey].colors) {
                        data[handKey].colors.forEach((c, idx) => {
                            const noteName = data[handKey].notes[idx] || `${handKey} Tone ${idx+1}`;
                            activeChordTones.push({
                                id: `${handKey}_${noteName}`,
                                note: noteName,
                                color: `rgb(${c.r}, ${c.g}, ${c.b})`,
                                freq: A4_FREQ * Math.pow(2, ((c.quartertone_index || 0) - 9) / 12)
                            });
                        });
                    }
                });

                document.getElementById('chord-info').innerText = `Loaded Tones: ${activeChordTones.length} across hands`;
            } catch(e) {
                console.log("Using octave-specific pitch fallback.");
            }
            renderPolygons();
            updateBitwiseResult();
        }

        async function loadLibrary() {
            const N = parseInt(document.getElementById('n-input').value);
            const res = await fetch(`/api/library?n=${N}`);
            const data = await res.json();
            rhythmLibrary = data.library;

            if (polygons.length === 0) {
                polygons = [
                    { tone_index: 0, type: 'positive', mode: 'cyclotomic', index: 0, rotation: 0, ratio: 1.0 },
                    { tone_index: 0, type: 'negative', mode: 'bjorklund', index: 0, rotation: 0, ratio: 1.0 }
                ];
            }
            
            await syncChimes();
        }

        function renderPolygons() {
            const container = document.getElementById('polygons-container');
            container.innerHTML = '';
            
            globalLCMDivisions = calculateGlobalLCM();
            document.getElementById('lcm-info').innerText = `LCM Grid: ${globalLCMDivisions} Divisions`;

            polygons.forEach((poly, idx) => {
                const el = document.createElement('div');
                el.className = `poly-item ${poly.type}`;
                
                const toneInfo = activeChordTones[poly.tone_index % activeChordTones.length] || { note: 'Tone', color: '#00e676' };
                el.style.borderLeftColor = toneInfo.color;

                const toneOptions = activeChordTones.map((t, i) => 
                    `<option value="${i}" ${i === poly.tone_index ? 'selected' : ''}>Chord Tone ${i+1} (${t.note})</option>`
                ).join('');

                const list = rhythmLibrary[poly.mode] || [];
                let optionsHtml = list.map((item, i) => `<option value="${i}" ${i === poly.index ? 'selected' : ''}>${item.label}</option>`).join('');
                
                let ratioOptionsHtml = HARMONIC_RATIOS.map(r => 
                    `<option value="${r.ratio}" ${r.ratio === poly.ratio ? 'selected' : ''}>${r.label}</option>`
                ).join('');

                el.innerHTML = `
                    <div class="row">
                        <span style="font-weight:bold; color:${toneInfo.color}">Polygon ${idx+1}</span>
                        <select onchange="onToneChange(${idx}, parseInt(this.value))">
                            ${toneOptions}
                        </select>
                        <select onchange="updatePolygon(${idx}, 'type', this.value)">
                            <option value="positive" ${poly.type === 'positive' ? 'selected' : ''}>+ POSITIVE</option>
                            <option value="negative" ${poly.type === 'negative' ? 'selected' : ''}>- NEGATIVE</option>
                        </select>
                        <button onclick="removePolygon(${idx})" style="background:#555; padding: 2px 6px;">✕</button>
                    </div>
                    
                    <div class="row">
                        <select onchange="updatePolygon(${idx}, 'mode', this.value)">
                            <option value="cyclotomic" ${poly.mode === 'cyclotomic' ? 'selected' : ''}>Cyclotomic</option>
                            <option value="bjorklund" ${poly.mode === 'bjorklund' ? 'selected' : ''}>Bjorklund</option>
                        </select>
                        <select onchange="updatePolygon(${idx}, 'index', parseInt(this.value))" style="flex-grow:1;">
                            ${optionsHtml}
                        </select>
                    </div>

                    <div class="row">
                        <label>Rotate (${globalLCMDivisions} grid):</label>
                        <button onclick="stepRotation(${idx}, -1)">◀</button>
                        <span>${poly.rotation} / ${globalLCMDivisions}</span>
                        <button onclick="stepRotation(${idx}, 1)">▶</button>
                        
                        <label>Ratio:</label>
                        <select onchange="onRatioChange(${idx}, parseFloat(this.value))">
                            ${ratioOptionsHtml}
                        </select>
                    </div>
                `;
                container.appendChild(el);
            });
        }

        function onToneChange(polyIdx, toneIdx) {
            polygons[polyIdx].tone_index = toneIdx;
            if (voiceRatios[toneIdx] !== undefined) {
                polygons[polyIdx].ratio = voiceRatios[toneIdx];
            } else {
                voiceRatios[toneIdx] = polygons[polyIdx].ratio;
            }
            renderPolygons();
            updateBitwiseResult();
        }

        function onRatioChange(polyIdx, ratioVal) {
            polygons[polyIdx].ratio = ratioVal;
            const toneIdx = polygons[polyIdx].tone_index;
            voiceRatios[toneIdx] = ratioVal;
            renderPolygons();
            updateBitwiseResult();
        }

        function addPolygon() {
            const defaultToneIndex = 0;
            const inheritedRatio = voiceRatios[defaultToneIndex] !== undefined ? voiceRatios[defaultToneIndex] : 1.0;
            
            polygons.push({ 
                tone_index: defaultToneIndex, 
                type: 'positive', 
                mode: 'cyclotomic', 
                index: 0, 
                rotation: 0, 
                ratio: inheritedRatio 
            });
            renderPolygons();
            updateBitwiseResult();
        }

        function removePolygon(idx) {
            polygons.splice(idx, 1);
            renderPolygons();
            updateBitwiseResult();
        }

        function stepRotation(idx, dir) {
            polygons[idx].rotation = (polygons[idx].rotation + dir + globalLCMDivisions) % globalLCMDivisions;
            renderPolygons();
            updateBitwiseResult();
        }

        function updatePolygon(idx, key, value) {
            polygons[idx][key] = value;
            if (key === 'mode') polygons[idx].index = 0;
            renderPolygons();
            updateBitwiseResult();
        }

        function getRotatedPattern(poly) {
            const N = parseInt(document.getElementById('n-input').value);
            const list = rhythmLibrary[poly.mode] || [];
            if (!list[poly.index]) return new Array(N).fill(0);
            
            const base = list[poly.index].pattern;
            const stepShift = Math.round((poly.rotation / globalLCMDivisions) * N) % N;
            return base.slice(N - stepShift).concat(base.slice(0, N - stepShift));
        }

        async function updateBitwiseResult() {
            const N = parseInt(document.getElementById('n-input').value);
            
            const payloadPolygons = polygons.map(p => {
                const toneInfo = activeChordTones[p.tone_index % activeChordTones.length] || { id: 'default', note: 'Tone' };
                return {
                    tone_id: toneInfo.id,
                    tone_name: toneInfo.note,
                    type: p.type,
                    pattern: getRotatedPattern(p)
                };
            });

            const res = await fetch('/api/evaluate_voice_bitwise', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ N: N, polygons: payloadPolygons })
            });

            const analysisData = await res.json();
            window.currentVoiceAnalysis = analysisData;
            
            const statusBox = document.getElementById('bitwise-status');
            let voiceSummaries = '';

            for (const [toneId, v] of Object.entries(analysisData.voices)) {
                const badge = v.analysis.is_balanced ? 
                    '<span class="badge badge-bal">BALANCED</span>' : 
                    '<span class="badge badge-unbal">UNBALANCED</span>';
                voiceSummaries += `<div><strong>${v.tone_name}:</strong> ${badge} [${v.pattern.join('')}]</div>`;
            }

            statusBox.innerHTML = `
                <strong>Voice-Specific Cancellation Results:</strong><br>
                ${voiceSummaries || 'No polygons active.'}
            `;
            drawCanvas();
        }

        function drawCanvas() {
            const canvas = document.getElementById('polyCanvas');
            const ctx = canvas.getContext('2d');
            const N = parseInt(document.getElementById('n-input').value);
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const baseRadius = 180;

            // Draw LCM Fine-Grained Subdivision Ticks on Outer Ring
            for (let i = 0; i < globalLCMDivisions; i++) {
                const angle = (2 * Math.PI * i / globalLCMDivisions) - (Math.PI / 2);
                const x1 = centerX + (baseRadius + 18) * Math.cos(angle);
                const y1 = centerY + (baseRadius + 18) * Math.sin(angle);
                const x2 = centerX + (baseRadius + 24) * Math.cos(angle);
                const y2 = centerY + (baseRadius + 24) * Math.sin(angle);

                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.strokeStyle = '#00e676';
                ctx.lineWidth = (i % (globalLCMDivisions / N) === 0) ? 2.0 : 0.8;
                ctx.stroke();
            }

            // High-granularity vertex placement with precise angular rotation
            polygons.forEach((poly, pIdx) => {
                const list = rhythmLibrary[poly.mode] || [];
                if (!list[poly.index]) return;
                
                const pat = list[poly.index].pattern;
                const toneInfo = activeChordTones[poly.tone_index % activeChordTones.length] || { color: '#00e676' };
                const radOffset = pIdx * 12;

                const vertices = [];
                for (let i = 0; i < N; i++) {
                    if (pat[i]) {
                        // Rotation mapped smoothly across the LCM tick grid
                        const angle = (2 * Math.PI * (i / N + poly.rotation / globalLCMDivisions)) - (Math.PI / 2);
                        const r = baseRadius - radOffset;
                        vertices.push({
                            x: centerX + r * Math.cos(angle),
                            y: centerY + r * Math.sin(angle)
                        });
                    }
                }

                if (vertices.length > 1) {
                    ctx.beginPath();
                    ctx.moveTo(vertices[0].x, vertices[0].y);
                    vertices.forEach(v => ctx.lineTo(v.x, v.y));
                    ctx.closePath();

                    if (poly.type === 'positive') {
                        ctx.strokeStyle = toneInfo.color;
                        ctx.setLineDash([]);
                        ctx.lineWidth = 2.5;
                    } else {
                        ctx.strokeStyle = '#ff5252';
                        ctx.setLineDash([5, 5]);
                        ctx.lineWidth = 1.5;
                    }
                    ctx.stroke();
                    ctx.setLineDash([]);
                }

                // Render vertex dots directly at rotated locations
                vertices.forEach(v => {
                    ctx.beginPath();
                    ctx.arc(v.x, v.y, 4, 0, 2 * Math.PI);
                    ctx.fillStyle = poly.type === 'positive' ? toneInfo.color : '#ff5252';
                    ctx.fill();
                });
            });

            if (window.currentVoiceAnalysis && window.currentVoiceAnalysis.global_analysis) {
                const cmX = centerX + window.currentVoiceAnalysis.global_analysis.centroid[0] * baseRadius;
                const cmY = centerY - window.currentVoiceAnalysis.global_analysis.centroid[1] * baseRadius;

                ctx.beginPath();
                ctx.arc(cmX, cmY, 8, 0, 2 * Math.PI);
                ctx.fillStyle = window.currentVoiceAnalysis.global_analysis.is_balanced ? '#ffeb3b' : '#ff5252';
                ctx.fill();
                ctx.strokeStyle = '#000';
                ctx.stroke();
            }
        }

        // ==============================================================================
        // PRECISION WEB AUDIO LOOKAHEAD SCHEDULER
        // ==============================================================================

        function nextLcmTick() {
            const bpm = parseInt(document.getElementById('bpm-input').value);
            // Measure length (4 beats) divided into the total LCM subdivisions
            const secondsPerMeasure = (60.0 / bpm) * 4.0;
            const secondsPerLcmTick = secondsPerMeasure / globalLCMDivisions;

            nextTickTime += secondsPerLcmTick;
            currentLcmTick = (currentLcmTick + 1) % globalLCMDivisions;
        }

        function scheduleLcmTick(tickIndex, time) {
            const N = parseInt(document.getElementById('n-input').value);

            polygons.forEach(poly => {
                const list = rhythmLibrary[poly.mode] || [];
                if (!list[poly.index]) return;

                const pat = list[poly.index].pattern;
                const effectiveSteps = Math.round(N * poly.ratio);
                const ticksPerPolyStep = globalLCMDivisions / effectiveSteps;

                // Check if this tick corresponds to an active pulse for this polygon
                const adjustedTick = (tickIndex - poly.rotation + globalLCMDivisions * 100) % globalLCMDivisions;

                if (adjustedTick % ticksPerPolyStep === 0) {
                    const stepIdx = Math.floor(adjustedTick / ticksPerPolyStep) % N;
                    if (pat[stepIdx]) {
                        const toneInfo = activeChordTones[poly.tone_index % activeChordTones.length] || { freq: 220, color: '#00e676' };
                        scheduleTone(time, toneInfo.freq, toneInfo.color, poly.type === 'positive');
                    }
                }
            });
        }

        function scheduler() {
            while (nextTickTime < audioCtx.currentTime + scheduleAheadTime) {
                scheduleLcmTick(currentLcmTick, nextTickTime);
                nextLcmTick();
            }
            timerID = setTimeout(scheduler, lookahead);
        }

        function togglePlay() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }

            if (isPlaying) {
                clearTimeout(timerID);
                isPlaying = false;
                document.getElementById('play-btn').innerText = 'Play Poly-Rhythm';
            } else {
                isPlaying = true;
                document.getElementById('play-btn').innerText = 'Stop';
                currentLcmTick = 0;
                nextTickTime = audioCtx.currentTime + 0.05;
                scheduler();
            }
        }

        syncPollInterval = setInterval(syncChimes, 60000);

        document.getElementById('update-n-btn').addEventListener('click', loadLibrary);
        loadLibrary();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    print("Running Granular Milne Engine on http://0.0.0.0:5007")
    app.run(host='0.0.0.0', port=5007, debug=True)
