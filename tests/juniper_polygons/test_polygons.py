import math
import pytest
#from .polygons import (
from juniper_polygons.polygons import (
    gcd,
    bjorklund,
    get_centroid,
    is_strictly_balanced,
    is_regular_polygon,
    analyze_pattern,
    get_canonical_dihedral,
    get_full_orbit,
    circular_distance,
    generate_rhythm_library,
    is_nontrivial,
    note_to_freq_432,
    PolygonProgressionEngine,
)

# ==============================================================================
# 1. CORE ARITHMETIC & HELPER FUNCTIONS
# ==============================================================================

def test_gcd():
    assert gcd(12, 8) == 4
    assert gcd(7, 5) == 1
    assert gcd(12, 0) == 12


def test_bjorklund_basic():
    # E(3, 8) standard Euclidean rhythm
    e_3_8 = bjorklund(8, 3)
    assert len(e_3_8) == 8
    assert sum(e_3_8) == 3
    assert e_3_8 == [1, 0, 0, 1, 0, 0, 1, 0]


def test_bjorklund_edge_cases():
    assert bjorklund(6, 0) == [0, 0, 0, 0, 0, 0]
    assert bjorklund(6, 6) == [1, 1, 1, 1, 1, 1]
    assert bjorklund(6, 10) == [1, 1, 1, 1, 1, 1]  # pulses >= steps


def test_is_nontrivial():
    assert not is_nontrivial([0, 0, 0, 0])  # k=0
    assert not is_nontrivial([1, 0, 0, 0])  # k=1
    assert is_nontrivial([1, 0, 1, 0])      # k=2, N=4 (2 pulses, 2 rests)
    assert not is_nontrivial([1, 1, 1, 0])  # k=3, N=4 (N-1 pulses)
    assert not is_nontrivial([1, 1, 1, 1])  # k=4


# ==============================================================================
# 2. GEOMETRIC & CENTROID MATH
# ==============================================================================

def test_centroid_and_balance():
    # Regular 4-gon in N=8 (indices 0, 2, 4, 6) -> Centroid must be (0, 0)
    square_8 = [1, 0, 1, 0, 1, 0, 1, 0]
    cx, cy = get_centroid(square_8, 8)
    assert math.hypot(cx, cy) == pytest.approx(0.0, abs=1e-5)
    assert is_strictly_balanced(square_8, 8)

    # Unbalanced pattern -> Centroid off-center
    unbalanced = [1, 1, 0, 0, 0, 0, 0, 0]
    assert not is_strictly_balanced(unbalanced, 8)


def test_is_regular_polygon():
    # Regular 3-gon (equilateral triangle) in N=6
    triangle_6 = [1, 0, 1, 0, 1, 0]
    assert is_regular_polygon(triangle_6, 6)

    # Composite balanced (Class 2) but NOT regular polygon
    # Union of 2-gon [0, 3] and 2-gon [1, 4] in N=6 -> [1, 1, 0, 1, 1, 0]
    composite_6 = [1, 1, 0, 1, 1, 0]
    assert is_strictly_balanced(composite_6, 6)
    assert not is_regular_polygon(composite_6, 6)


def test_analyze_pattern():
    square_8 = [1, 0, 1, 0, 1, 0, 1, 0]
    analysis = analyze_pattern(square_8, 8)
    assert analysis["is_balanced"] is True
    assert analysis["class_type"] == "Class 1 (Regular)"
    assert analysis["dist_from_origin"] == pytest.approx(0.0, abs=1e-5)


# ==============================================================================
# 3. DIHEDRAL SYMMETRY & ORBIT GENERATION
# ==============================================================================

def test_get_canonical_dihedral():
    # Rotations/reflections of the same shape must map to identical canonical tuples
    pat_a = [1, 0, 1, 0, 0]
    pat_rotated = [0, 0, 1, 0, 1]
    pat_reflected = [0, 0, 1, 0, 1][::-1]

    canon_a = get_canonical_dihedral(pat_a)
    canon_rot = get_canonical_dihedral(pat_rotated)
    canon_ref = get_canonical_dihedral(pat_reflected)

    assert canon_a == canon_rot == canon_ref


def test_get_full_orbit():
    pat = [1, 0, 1, 0]
    orbit = get_full_orbit(pat)

    # Should contain distinct rotations/reflections
    assert [1, 0, 1, 0] in orbit
    assert [0, 1, 0, 1] in orbit
    assert len(orbit) <= 2 * len(pat)


def test_circular_distance():
    pat1 = [1, 0, 0, 0]
    pat2 = [1, 0, 0, 0]
    # Identical patterns have 0 distance
    assert circular_distance(pat1, pat2) == 0.0

    # Distances between different patterns should be positive
    pat3 = [0, 1, 0, 0]
    assert circular_distance(pat1, pat3) > 0.0


# ==============================================================================
# 4. TUNING & LIBRARY GENERATION
# ==============================================================================

def test_note_to_freq_432():
    # A4 anchored to 432 Hz
    assert note_to_freq_432("A4") == pytest.approx(432.0)
    # A3 is one octave lower -> 216 Hz
    assert note_to_freq_432("A3") == pytest.approx(216.0)
    # C4 frequency at 432 Hz tuning
    assert note_to_freq_432("C4") == pytest.approx(256.869, abs=1e-2)
    # Invalid note fallback
    assert note_to_freq_432("invalid") == 432.0


def test_generate_rhythm_library():
    lib = generate_rhythm_library(6)
    assert "cyclotomic" in lib
    assert "bjorklund" in lib
    assert len(lib["bjorklund"]) > 0


# ==============================================================================
# 5. POLYGON PROGRESSION ENGINE INTEGRATION TESTS
# ==============================================================================

@pytest.fixture
def test_engine():
    """Creates a fast, small-N engine instance for testing traversal logic."""
    return PolygonProgressionEngine(
        step_cycles=[4, 6],
        repeats_per_combo=2,
        bpm=120,
        shuffle_n=False
    )


def test_engine_initialization(test_engine):
    assert test_engine.repeats_per_combo == 2
    assert test_engine.bpm == 120
    assert len(test_engine.sequence) > 0


def test_engine_tick_progression(test_engine):
    # Retrieve initial state tick
    state1 = test_engine.tick()
    assert state1["N"] == 4
    assert state1["step_index"] == 0
    assert state1["repeat_count"] == 1
    assert "hits" in state1
    assert "left_hand_7th" in state1["hits"]
    assert "right_hand_7th" in state1["hits"]

    # Step forward 1 beat
    state2 = test_engine.tick()
    assert state2["step_index"] == 1


def test_engine_repeat_and_combo_advancement(test_engine):
    initial_combo = test_engine.combo_idx
    N = test_engine.sequence[0]["N"]
    repeats = test_engine.repeats_per_combo

    # Tick through all steps for all repeats of the first combo
    total_ticks_for_combo = N * repeats
    for _ in range(total_ticks_for_combo):
        test_engine.tick()

    # Engine should have advanced to the next combination
    assert test_engine.combo_idx == initial_combo + 1
    assert test_engine.step_in_pattern == 0
    assert test_engine.current_repeat == 0


def test_engine_macro_cycle_advancement():
    # Single step cycle N=4 with shuffle_n=False
    engine = PolygonProgressionEngine(
        step_cycles=[4],
        repeats_per_combo=1,
        bpm=120,
        shuffle_n=False
    )

    total_combos = len(engine.sequence)
    total_ticks = total_combos * 4  # N=4, repeats=1

    for _ in range(total_ticks):
        engine.tick()

    # Should wrap back around to the start
    assert engine.combo_idx == 0
    assert engine.current_n_idx == 0
