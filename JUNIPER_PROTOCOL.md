# Technical Specification: Distributed Polyphonic Clock & Harmonized Microservice Standards

## 1. System Overview & Architecture

The system architecture defines a multi-server environment where up to 8 independent application servers (such as TTS dictionary narrators, display agents, and audio synthesized nodes) operate concurrently in a shared acoustic and visual space. Servers maintain harmonic, rhythmic, and visual coherence without direct peer-to-peer communication by synchronizing state with central upstream clock and palette authority servers.

```
┌───────────────────────────────────────┐
│         Balanced Polygon App          │  (Upstream Universe Generator)
└───────────────────┬───────────────────┘
                    │ WebSocket (ws://127.0.0.1:65403)[cite: 69]
                    ▼
┌───────────────────────────────────────┐
│              Chimes App               │  (Master Time & Pitch Server)
└─────────┬───────────────────┬─────────┘
          │                   │
  WebSocket / State Stream    │
          │                   ▼
          │         ┌───────────────────────────────────┐
          │         │        Synesthesia Server         │  (Visual Palette Coordinator)
          │         └───────────────────────────────────┘
          │
          ├───► Application Server 0 (Voice A / Chord Tone 0)[cite: 65]
          ├───► Application Server 1 (Voice B / Chord Tone 1)[cite: 65]
          ├───► ...
          └───► Application Server 7 (Voice H / Chord Tone 7)[cite: 65]

```

### Server Roles & Responsibilities

| Component | Role & Function | Interface / Communication Protocol |
| --- | --- | --- |
| **Balanced Polygon App** | Generates upstream geometric polyrhythms and Euclidean step patterns across multi-dimensional universe topologies.

 | Outbound WebSocket stream (`ws://127.0.0.1:65403`)

 |
| **Chimes App (Master Clock)** | Establishes master 60 BPM pulse, generates N-EDO microtonal pitches, constructs diatonic 7th/polychord progressions, and broadcasts tick updates.

 | Inbound WS (`ws://127.0.0.1:65432`) & HTTP API (`:5004`)

 |
| **Application Servers** | Consume Chimes state, execute domain logic (e.g., TTS dictionary narration, Morse audio generation), and jitter events to the 60 BPM grid.

 | HTTP API (`:5003`) & Server-Sent Events (`/api/stream`)

 |
| **Synesthesia Server** | Coordinates visual color palettes derived from active chord tone index allocations across display frontends.

 | Index mapping protocol based on chord tone index $i$ |

---

## 2. Timing & Synchronization Specification

### 2.1 Master Metronome & Sub-Grid

* **Master Pulse**: Global beat is anchored at $60\text{ BPM}$ ($1.0\text{ second}$ per master tick).


* **Sub-Tick 16th-Note Grid**: The fundamental rhythmic subdivision is a 16th note, calculated as:

$$\Delta t_{\text{16th}} = \frac{60\text{ seconds}}{60\text{ BPM} \times 4} = 0.125\text{ seconds } (125\text{ ms})$$



* **Fractional Narration Ratios**: Speech generation and narration state durations are structured as fractional ratios relative to the $60\text{ BPM}$ master clock.



### 2.2 Beat Jitter Correction Algorithm

To eliminate drift across independent nodes without hard-coding arbitrary wait timers, application servers calculate execution modulo ($t \bmod 0.125\text{ s}$) following dynamic tasks (e.g., TTS rendering or I/O) and jitter sleep back onto the nearest $125\text{ ms}$ grid boundary.

```python
import time

def align_to_metronome_grid(sub_grid_sec=0.125):
    """Aligns execution back onto the 60 BPM / 125ms sub-note grid."""
    now = time.time()
    remainder = now % sub_grid_sec
    sleep_to_next_tick = sub_grid_sec - remainder if remainder > 0 else 0.0
    
    if sleep_to_next_tick < 0.02:
        sleep_to_next_tick += sub_grid_sec
        
    time.sleep(sleep_to_next_tick)
```[cite: 65]

---

## 3. Pitch, Microtonality & Chord Architecture

### 3.1 N-EDO Tuning & Pitch References

* **Master Tuning Reference Anchor**: $A_4 = 432.0\text{ Hz}$[cite: 67, 69].
* **Microtonal EDO Support**: Pitch space is parameterized using Equal Division of the Octave systems ($N\text{-EDO}$, supporting 12, 24, 31, or 53 divisions)[cite: 67, 69].
* **Pitch Frequency Calculation**:
  $$f(\text{step}) = f_{A_4} \times 2^{\frac{\text{step} - \text{step}_{A_4}}{N}}$$
[cite: 67]

### 3.2 Polychord & Chord Tone Pool ($n=8$)

The Chimes master clock computes simultaneous 4-voice diatonic 7th chords across two register hands:
1. **Left Hand (Lower Register)**: Primary 4-voice chord ($t_0, t_1, t_2, t_3$)[cite: 67, 69].
2. **Right Hand (Upper Register)**: Parallel or shifted 4-voice chord ($t_4, t_5, t_6, t_7$)[cite: 67, 69].

Together, these form an 8-tone polychord pool ($n = 8$ well-known chord tones) broadcast on every clock cycle[cite: 67, 69]:
$$\text{ChordTonePool} = [f_0, f_1, f_2, f_3, f_4, f_5, f_6, f_7]$$
[cite: 67, 69]

---

## 4. Peer-to-Peer Harmony & Port-like Tone Indexing

### 4.1 Peer Independence Protocol

* **Decentralized Peer Execution**: Application servers do not communicate with each other.
* **Tone Index Allocation**: Each server selects a unique Chord Tone Index $i \in \{0, 1, 2, 3, 4, 5, 6, 7\}$ (0-indexed) or $i \in \{1 \dots 8\}$ (1-indexed), configured in the same manner as selecting network port numbers[cite: 65].
* **Tone Frequency Standard**: Server $i$ plays on well-known tone $i/n$ (where $n=8$) extracted directly from the active Chimes state[cite: 65].


```

```
             Chimes Master State Broadcast[cite: 66, 69]
                       │
   ┌───────────────────┼───────────────────┐
   ▼                   ▼                   ▼

```

Server Index i=0    Server Index i=1    Server Index i=7
Tone: f_0           Tone: f_1           Tone: f_7
Narrator: Voice 0   Narrator: Voice 1   Narrator: Voice 7
Color: Primary      Color: Secondary    Color: Octary

```

### 4.2 Frequency Alignment Rule

* Server $i$ binds its dynamic pitch events to frequency $f_i$ corresponding to index $i$ from the master state[cite: 65, 69].
* Application servers may down-shift selected chord frequencies by octaves ($f_{\text{morse}} = f_i / 2^k$) to bring Morse audio into lower auditory registers while maintaining exact harmonic pitch resonance[cite: 65].

---

## 5. Morse Code & TTS Narration Standards

### 5.1 Morse Audio Parameters

* **Dot Duration ($\text{dit}$)**: Fixed strictly to 1 16th-note ($125\text{ ms}$)[cite: 65].
* **Dash Duration ($\text{dah}$)**: Fixed to 3 16th-notes ($375\text{ ms}$)[cite: 65].
* **Element Space**: 1 16th-note ($125\text{ ms}$) silence between symbols[cite: 65].
* **Character Space**: 3 16th-notes ($375\text{ ms}$) silence between letters[cite: 65].
* **Tone Frequency**: Derived from the nearest chord tone $f_i$ dynamically updated from the Chimes state[cite: 65].

### 5.2 Narrator Differentiation & Pipeline Sequence

Each server instantiates a distinct TTS voice narrator and processes dictionary terms through a synchronized sequence[cite: 65]:

1. **Say Word**: Announce target word over TTS engine[cite: 65].
2. **Metrical Foot**: Announce prosodic foot pattern (e.g., Iamb, Trochee, Dactyl)[cite: 65].
3. **Morse Code Spelling**: Spell the word in Morse code using chord tone frequency $f_i$ at $125\text{ ms}$ dits[cite: 65].
4. **Repeat Word & Palindrome Check**: Re-announce word; identify palindromic properties[cite: 65].
5. **Lexical Senses**: Broadcast definitions, synonyms, antonyms, hyponyms, and hypernyms[cite: 65].
6. **Sub-Grid Jitter**: Execute grid jitter correction after every step to ensure timing remains anchored to the master clock[cite: 65].

---

## 6. Synesthesia Color Palette Standard

Display agents and visual frontends synchronize color themes using the same Chord Tone Index $i \in \{0 \dots 7\}$ assigned to the server[cite: 68]:

| Chord Tone Index ($i$) | Visual Palette Role | Hierarchy / Relationship |
| :---: | :--- | :--- |
| **0** | Primary Base | Tonic / Master Key Accent[cite: 68] |
| **1** | Secondary Base | Dominant Contrast[cite: 68] |
| **2** | Tertiary Accent | Subdominant Complement[cite: 68] |
| **3** | Quaternary Accent | Harmonic Highlight[cite: 68] |
| **4** | Quinary (Upper Base) | Right-Hand Primary[cite: 68] |
| **5** | Senary (Upper Secondary) | Right-Hand Secondary[cite: 68] |
| **6** | Septenary (Upper Accent) | Polytonal Highlight[cite: 68] |
| **7** | Octary (Upper Accent) | Microtonal Edge[cite: 68] |

By linking color generation directly to index $i$, visual displays automatically reflect the multi-server musical harmony across physical environments without requiring peer coordination[cite: 68].

```
