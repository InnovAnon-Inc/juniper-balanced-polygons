def circular_distance(pat1: list[int], pat2: list[int]) -> float:
    """Calculates the rotational distance and density difference between two patterns."""
    N = len(pat1)
    idx1 = [i for i, x in enumerate(pat1) if x]
    idx2 = [i for i, x in enumerate(pat2) if x]
    
    if not idx1 and not idx2: return 0.0
    if not idx1 or not idx2: return float(N)
    
    dist = 0
    # Distance from each pulse in pat1 to its nearest neighbor in pat2
    for p1 in idx1:
        dist += min(min(abs(p1 - p2), N - abs(p1 - p2)) for p2 in idx2)
    
    # Distance from each pulse in pat2 to its nearest neighbor in pat1
    for p2 in idx2:
        dist += min(min(abs(p2 - p1), N - abs(p2 - p1)) for p1 in idx1)
        
    # Penalty for changing pulse density (dropping or adding notes)
    density_penalty = abs(len(idx1) - len(idx2)) * (N / 4.0)
    
    return dist + density_penalty

def sequence_smooth_path(rhythm_list: list[dict]) -> list[dict]:
    """Sorts a list of rhythms into a smooth path minimizing the circular distance."""
    if not rhythm_list: return []

    unvisited = rhythm_list[:]
    path = [unvisited.pop(0)] # Start with the simplest/first pattern

    while unvisited:
        current_pat = path[-1]['pattern']
        closest_idx = 0
        min_dist = float('inf')

        for i, candidate in enumerate(unvisited):
            dist = circular_distance(current_pat, candidate['pattern'])
            if dist < min_dist:
                min_dist = dist
                closest_idx = i

        path.append(unvisited.pop(closest_idx))

    return path

def generate_rhythm_library(N: int) -> dict:
    cyclotomic = []
    bjorklund_rhythms = []
    seen_cyc = set()
    seen_bjork = set()

    # 1. Euclidean / Bjorklund (Non-Trivial & Coprime Only)
    for k in range(2, N - 1): # Excludes trivial k=1 and k=N-1
        if gcd(k, N) == 1:
            pat = bjorklund(N, k)
            canonical = get_canonical_rotation(pat)
            if canonical not in seen_bjork:
                seen_bjork.add(canonical)
                info = analyze_pattern(list(canonical), N)
                info["label"] = f"Euclidean E({k},{N})"
                info["is_coprime"] = True
                bjorklund_rhythms.append(info)

    # 2. Constructive Cyclotomic generation (Avoids O(2^N) limitations)
    divisors = [d for d in range(2, N) if N % d == 0]
    basis_polygons = []

    # Generate all possible shifted regular polygons for each divisor
    for d in divisors:
        stride = N // d
        for offset in range(stride):
            pat_set = frozenset(offset + i * stride for i in range(d))
            basis_polygons.append(pat_set)

    # Recursive search to layer disjoint regular polygons
    def build_balanced_combinations(index: int, current_union: frozenset):
        # Cap large N combinations to prevent excessive memory usage on heavily divisible numbers
        if len(seen_cyc) > 2000:
            return

        if current_union:
            canonical = get_canonical_rotation([1 if i in current_union else 0 for i in range(N)])
            if canonical not in seen_cyc:
                seen_cyc.add(canonical)
                canonical_pat = list(canonical)
                info = analyze_pattern(canonical_pat, N)
                info["label"] = f"Cyclotomic {info['class_type']} ({sum(canonical_pat)} pulses)"
                cyclotomic.append(info)

        for i in range(index, len(basis_polygons)):
            if not current_union.intersection(basis_polygons[i]):
                build_balanced_combinations(i + 1, current_union.union(basis_polygons[i]))

    build_balanced_combinations(0, frozenset())

    # 3. Sort both lists to ensure smooth, non-jarring transitions
    return {
        "cyclotomic": sequence_smooth_path(cyclotomic),
        "bjorklund": sequence_smooth_path(bjorklund_rhythms)
    }


