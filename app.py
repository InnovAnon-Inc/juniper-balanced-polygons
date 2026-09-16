import cmath
import math
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# ==============================================================================
# RIGOROUS MATHEMATICAL & BALANCED RHYTHM ENGINE
# ==============================================================================

def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

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
    """Calculates vector sum center of mass on complex unit circle."""
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
    """A rhythm is balanced IF AND ONLY IF its center of mass is at (0,0)."""
    cx, cy = get_centroid(pattern, N)
    return math.hypot(cx, cy) < tol

def is_regular_polygon(pattern: list[int], N: int) -> bool:
    """Class 1: Single regular equilateral polygon inscribed in the circle."""
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
    
    # Class 1 = Single regular polygon; Class 2 = Composite sum of regular polygons (both center at 0,0)
    class_type = "Class 1 (Regular)" if regular else ("Class 2 (Composite)" if balanced else "Unbalanced")
    
    return {
        "pattern": pattern,
        "is_balanced": balanced,
        "class_type": class_type,
        "centroid": [round(cx, 5), round(cy, 5)],
        "dist_from_origin": round(math.hypot(cx, cy), 5)
    }

def generate_rhythm_library(N: int) -> dict:
    """Generates catalog of strictly balanced cyclotomic and Bjorklund rhythms."""
    cyclotomic = []
    bjorklund_rhythms = []
    seen_cyc = set()
    seen_bjork = set()

    # 1. Bjorklund Euclidean Rhythms
    for k in range(1, N):
        pat = bjorklund(N, k)
        key = tuple(pat)
        if key not in seen_bjork:
            seen_bjork.add(key)
            info = analyze_pattern(pat, N)
            info["label"] = f"Euclidean E({k},{N})"
            info["is_coprime"] = gcd(k, N) == 1
            bjorklund_rhythms.append(info)

    # 2. Exhaustive Search for Strictly Balanced Cyclotomic Polygons
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
# FLASK ROUTES
# ==============================================================================

@app.route('/api/library', methods=['GET'])
def get_library():
    n_steps = int(request.args.get('n', 12))
    lib = generate_rhythm_library(n_steps)
    return jsonify({"n": n_steps, "library": lib})

@app.route('/api/evaluate_bitwise', methods=['POST'])
def evaluate_bitwise():
    data = request.json
    positive_mask = data.get('positive_mask', [])
    negative_mask = data.get('negative_mask', [])
    N = len(positive_mask)
    
    # Perform Bitwise Operation: Positive AND NOT Negative (P & ~N)
    result_pattern = [1 if (pos and not neg) else 0 for pos, neg in zip(positive_mask, negative_mask)]
    analysis = analyze_pattern(result_pattern, N)
    return jsonify(analysis)

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
    <title>Harmonic Milne Balanced Polygons</title>
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
            max-width: 1300px;
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
            width: 380px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .stack-item {
            background: #2a2a32;
            padding: 10px;
            border-radius: 6px;
            border-left: 4px solid #00e676;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .stack-item.negative { border-left-color: #ff5252; }

        .row { display: flex; justify-content: space-between; align-items: center; }
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

    <h1>Harmonic Cyclotomic & Euclidean Rhythm Engine</h1>
    <p class="subtitle">A4 = 432 Hz Master Tuning | Strict Center of Mass Balance | Bitwise Logic (P & ~N)</p>

    <div class="top-bar">
        <label for="n-input">Pulses (N):</label>
        <input type="number" id="n-input" value="12" min="3" max="32" style="width: 60px;">
        <button onclick="loadLibrary()">Update N</button>

        <label for="bpm-input">Master BPM:</label>
        <input type="number" id="bpm-input" value="120" min="30" max="300" style="width: 65px;">

        <button id="play-btn" onclick="togglePlay()">Play Poly-Rhythm</button>
    </div>

    <div class="workspace">
        <!-- Visualization Canvas -->
        <div class="canvas-card">
            <canvas id="polyCanvas" width="420" height="420"></canvas>
            <div class="status-box" id="bitwise-status" style="margin-top: 15px; width: 390px;">
                Evaluating combined bitwise pattern...
            </div>
        </div>

        <!-- Dynamic Polygon Multi-Stack Control -->
        <div class="panel">
            <h3>Polygon Stacks & Harmonic Ratios</h3>
            <div id="stacks-container"></div>
            <button onclick="addStack()">+ Add Polygon Stack</button>
        </div>
    </div>

    <script>
        const A4_FREQ = 432.0;
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        
        let rhythmLibrary = { cyclotomic: [], bjorklund: [] };
        let stacks = [];
        let isPlaying = false;
        let masterTimer = null;
        let globalTick = 0;

        function playTone(freq, isPositive) {
            if (audioCtx.state === 'suspended') audioCtx.resume();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();

            osc.type = isPositive ? 'sine' : 'sawtooth';
            const actualFreq = isPositive ? freq : freq / 2;
            
            osc.frequency.setValueAtTime(actualFreq, audioCtx.currentTime);
            gain.gain.setValueAtTime(isPositive ? 0.35 : 0.15, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);

            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.15);
        }

        async function loadLibrary() {
            const N = parseInt(document.getElementById('n-input').value);
            const res = await fetch(`/api/library?n=${N}`);
            const data = await res.json();
            rhythmLibrary = data.library;

            // Reset stacks with initial Positive and Negative default layers
            stacks = [
                { type: 'positive', mode: 'cyclotomic', index: 0, rotation: 0, ratio: 1.0 },
                { type: 'negative', mode: 'bjorklund', index: 0, rotation: 0, ratio: 1.0 }
            ];
            
            renderStacks();
            updateBitwiseResult();
        }

        function renderStacks() {
            const container = document.getElementById('stacks-container');
            container.innerHTML = '';

            stacks.forEach((stack, idx) => {
                const el = document.createElement('div');
                el.className = `stack-item ${stack.type}`;
                
                const list = rhythmLibrary[stack.mode] || [];
                let optionsHtml = list.map((item, i) => `<option value="${i}" ${i === stack.index ? 'selected' : ''}>${item.label}</option>`).join('');

                el.innerHTML = `
                    <div class="row">
                        <select onchange="updateStack(${idx}, 'type', this.value)">
                            <option value="positive" ${stack.type === 'positive' ? 'selected' : ''}>+ POSITIVE</option>
                            <option value="negative" ${stack.type === 'negative' ? 'selected' : ''}>- NEGATIVE</option>
                        </select>
                        <select onchange="updateStack(${idx}, 'mode', this.value)">
                            <option value="cyclotomic" ${stack.mode === 'cyclotomic' ? 'selected' : ''}>Cyclotomic</option>
                            <option value="bjorklund" ${stack.mode === 'bjorklund' ? 'selected' : ''}>Bjorklund</option>
                        </select>
                        <button onclick="removeStack(${idx})" style="background:#555; padding: 2px 6px;">✕</button>
                    </div>
                    
                    <select onchange="updateStack(${idx}, 'index', parseInt(this.value))">
                        ${optionsHtml}
                    </select>

                    <div class="row">
                        <label>Rotate:</label>
                        <button onclick="stepRotation(${idx}, -1)">◀</button>
                        <span>${stack.rotation}</span>
                        <button onclick="stepRotation(${idx}, 1)">▶</button>
                        
                        <label>Ratio:</label>
                        <select onchange="updateStack(${idx}, 'ratio', parseFloat(this.value))">
                            <option value="0.5" ${stack.ratio === 0.5 ? 'selected' : ''}>1/2 (8ths)</option>
                            <option value="0.6666" ${stack.ratio === 0.6666 ? 'selected' : ''}>2/3 (Triplets)</option>
                            <option value="1.0" ${stack.ratio === 1.0 ? 'selected' : ''}>1/1 (Base)</option>
                            <option value="2.0" ${stack.ratio === 2.0 ? 'selected' : ''}>2/1 (16ths)</option>
                        </select>
                    </div>
                `;
                container.appendChild(el);
            });
        }

        function addStack() {
            stacks.push({ type: 'positive', mode: 'cyclotomic', index: 0, rotation: 0, ratio: 1.0 });
            renderStacks();
            updateBitwiseResult();
        }

        function removeStack(idx) {
            stacks.splice(idx, 1);
            renderStacks();
            updateBitwiseResult();
        }

        function stepRotation(idx, dir) {
            const N = parseInt(document.getElementById('n-input').value);
            stacks[idx].rotation = (stacks[idx].rotation + dir + N) % N;
            renderStacks();
            updateBitwiseResult();
        }

        function updateStack(idx, key, value) {
            stacks[idx][key] = value;
            if (key === 'mode') stacks[idx].index = 0;
            renderStacks();
            updateBitwiseResult();
        }

        function getRotatedPattern(stack) {
            const N = parseInt(document.getElementById('n-input').value);
            const list = rhythmLibrary[stack.mode] || [];
            if (!list[stack.index]) return new Array(N).fill(0);
            
            const base = list[stack.index].pattern;
            const r = stack.rotation % N;
            return base.slice(N - r).concat(base.slice(0, N - r));
        }

        async function updateBitwiseResult() {
            const N = parseInt(document.getElementById('n-input').value);
            let posMask = new Array(N).fill(0);
            let negMask = new Array(N).fill(0);

            stacks.forEach(s => {
                const pat = getRotatedPattern(s);
                for (let i = 0; i < N; i++) {
                    if (s.type === 'positive' && pat[i]) posMask[i] = 1;
                    if (s.type === 'negative' && pat[i]) negMask[i] = 1;
                }
            });

            const res = await fetch('/api/evaluate_bitwise', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ positive_mask: posMask, negative_mask: negMask })
            });

            const analysis = await res.json();
            window.currentAnalysis = analysis;
            
            const statusBox = document.getElementById('bitwise-status');
            const badge = analysis.is_balanced ? 
                '<span class="badge badge-bal">STRICTLY BALANCED</span>' : 
                '<span class="badge badge-unbal">UNBALANCED</span>';

            statusBox.innerHTML = `
                <strong>Bitwise Result (P & ~N):</strong> ${badge}<br>
                Pattern: [${analysis.pattern.join('')}]<br>
                Center of Mass: (${analysis.centroid[0]}, ${analysis.centroid[1]})
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
            const radius = 160;

            // Base Circle
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 2;
            ctx.stroke();

            const getCoords = (i) => {
                const angle = (2 * Math.PI * i / N) - (Math.PI / 2);
                return {
                    x: centerX + radius * Math.cos(angle),
                    y: centerY + radius * Math.sin(angle)
                };
            };

            // Draw stack polygons
            stacks.forEach(s => {
                const pat = getRotatedPattern(s);
                const active = pat.reduce((acc, v, i) => v ? [...acc, i] : acc, []);
                if (active.length > 1) {
                    ctx.beginPath();
                    const start = getCoords(active[0]);
                    ctx.moveTo(start.x, start.y);
                    active.forEach(idx => {
                        const pt = getCoords(idx);
                        ctx.lineTo(pt.x, pt.y);
                    });
                    ctx.closePath();
                    ctx.strokeStyle = s.type === 'positive' ? 'rgba(0, 230, 118, 0.6)' : 'rgba(255, 82, 82, 0.6)';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            });

            // Draw Combined Output Vertices
            if (window.currentAnalysis) {
                const pat = window.currentAnalysis.pattern;
                for (let i = 0; i < N; i++) {
                    const pt = getCoords(i);
                    ctx.beginPath();
                    ctx.arc(pt.x, pt.y, 6, 0, 2 * Math.PI);
                    ctx.fillStyle = pat[i] ? '#00e676' : '#444';
                    ctx.fill();
                }

                // Plot Center of Mass
                const cmX = centerX + window.currentAnalysis.centroid[0] * radius;
                const cmY = centerY - window.currentAnalysis.centroid[1] * radius;

                ctx.beginPath();
                ctx.arc(cmX, cmY, 8, 0, 2 * Math.PI);
                ctx.fillStyle = window.currentAnalysis.is_balanced ? '#ffeb3b' : '#ff5252';
                ctx.fill();
                ctx.strokeStyle = '#000';
                ctx.stroke();
            }
        }

        function togglePlay() {
            if (isPlaying) {
                clearInterval(masterTimer);
                isPlaying = false;
                document.getElementById('play-btn').innerText = 'Play Poly-Rhythm';
            } else {
                isPlaying = true;
                document.getElementById('play-btn').innerText = 'Stop';
                globalTick = 0;

                const bpm = parseInt(document.getElementById('bpm-input').value);
                const N = parseInt(document.getElementById('n-input').value);
                
                // Fast master clock tick rate (96 ticks per quarter note)
                const tickIntervalMs = (60000 / bpm) / 24;

                masterTimer = setInterval(() => {
                    stacks.forEach(s => {
                        const pat = getRotatedPattern(s);
                        const stepDurationTicks = Math.round(24 * s.ratio);
                        
                        if (globalTick % stepDurationTicks === 0) {
                            const stepIdx = Math.floor(globalTick / stepDurationTicks) % N;
                            if (pat[stepIdx]) {
                                const baseFreq = (A4_FREQ / 2) * Math.pow(2, stepIdx / N);
                                playTone(baseFreq, s.type === 'positive');
                            }
                        }
                    });

                    globalTick++;
                }, tickIntervalMs);
            }
        }

        loadLibrary();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    print("Running Milne Balanced Polygons Engine on http://0.0.0.0:5007")
    app.run(host='0.0.0.0', port=5007, debug=True)
