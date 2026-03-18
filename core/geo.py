"""
Lebanese area coordinates for map rendering.
All coordinates are approximate centroids in decimal degrees (WGS84).
"""

from typing import Dict, Tuple, Optional

# (latitude, longitude) for each canonical area name
AREA_COORDS: Dict[str, Tuple[float, float]] = {
    # ── Beirut East ───────────────────────────────────────────────────────────
    'Ashrafieh':         (33.892,  35.516),
    'Gemmayzeh':         (33.893,  35.512),
    'Mar Mikhael':       (33.888,  35.518),
    'Geitawi':           (33.895,  35.522),
    'Rmeil':             (33.891,  35.515),
    'Saifi':             (33.895,  35.507),
    'Bourj Hammoud':     (33.892,  35.547),
    'Sin el Fil':        (33.893,  35.545),
    'Dora':              (33.912,  35.568),
    'Jdeideh':           (33.904,  35.568),
    'Fanar':             (33.882,  35.563),
    'Dekwaneh':          (33.888,  35.561),
    'Furn el Chebbak':   (33.869,  35.533),
    'Ain Saadeh':        (33.888,  35.587),

    # ── Beirut West / Central ────────────────────────────────────────────────
    'Downtown Beirut':   (33.895,  35.502),
    'Solidere':          (33.896,  35.500),
    'Hamra':             (33.895,  35.481),
    'Verdun':            (33.882,  35.492),
    'Raouche':           (33.892,  35.472),
    'Ain el Mreisseh':   (33.900,  35.474),
    'Manara':            (33.903,  35.469),
    'Ras Beirut':        (33.900,  35.472),
    'Badaro':            (33.874,  35.505),
    'Mar Elias':         (33.873,  35.497),
    'Bachoura':          (33.880,  35.500),
    'Sanayeh':           (33.889,  35.489),
    'Zokak el Blat':     (33.886,  35.494),
    'Corniche el Mazraa':(33.875,  35.499),
    'Ramlet el Bayda':   (33.882,  35.470),

    # ── South Beirut / Inner Suburbs ─────────────────────────────────────────
    'Chiyah':            (33.857,  35.508),
    'Ghobeiry':          (33.848,  35.501),
    'Haret Hreik':       (33.848,  35.497),
    'Bir Hassan':        (33.851,  35.483),
    'Jnah':              (33.860,  35.476),
    'Ouzai':             (33.832,  35.483),
    'Laylaki':           (33.855,  35.494),
    'Kafaat':            (33.854,  35.490),

    # ── Baabda / Metn (East suburbs) ─────────────────────────────────────────
    'Hazmieh':           (33.837,  35.549),
    'Baabda':            (33.833,  35.543),
    'Yarze':             (33.848,  35.560),
    'Mansourieh':        (33.892,  35.588),
    'Mtayleb':           (33.900,  35.618),
    'Bikfaya':           (33.923,  35.666),
    'Beit Meri':         (33.871,  35.604),
    'Broumana':          (33.880,  35.607),
    'Aintoura':          (33.979,  35.635),
    'Metn':              (33.890,  35.580),

    # ── Keserwan / North Coast ────────────────────────────────────────────────
    'Zalka':             (33.947,  35.576),
    'Dbayeh':            (33.969,  35.587),
    'Naccache':          (33.960,  35.571),
    'Antelias':          (33.964,  35.590),
    'Zouk Mosbeh':       (33.996,  35.607),
    'Zouk Mikael':       (33.997,  35.603),
    'Jounieh':           (33.983,  35.617),
    'Kaslik':            (33.993,  35.618),
    'Safra':             (34.028,  35.633),
    'Tabarja':           (34.050,  35.640),
    'Kfar Aabida':       (34.073,  35.643),

    # ── Jbeil (Byblos area) ───────────────────────────────────────────────────
    'Jbeil':             (34.124,  35.649),
    'Byblos':            (34.124,  35.649),
    'Amchit':            (34.094,  35.648),
    'Blat':              (34.141,  35.649),

    # ── South Lebanon ─────────────────────────────────────────────────────────
    'Saida':             (33.558,  35.371),
    'Tyre':              (33.270,  35.204),
    'Nabatieh':          (33.378,  35.484),
    'Bint Jbeil':        (33.120,  35.432),
    'Marjayoun':         (33.362,  35.591),
    'Hasbaya':           (33.399,  35.687),
    'Jezzine':           (33.545,  35.579),
    'Khiam':             (33.333,  35.603),
    'Kfar Rumman':       (33.441,  35.492),

    # ── South / Khalde corridor ───────────────────────────────────────────────
    'Khalde':            (33.790,  35.477),
    'Damour':            (33.715,  35.462),
    'Naameh':            (33.757,  35.472),
    'Kfarchima':         (33.818,  35.530),
    'Barja':             (33.659,  35.416),
    'Rmeileh':           (33.681,  35.432),
    'Jiyeh':             (33.706,  35.448),

    # ── North Lebanon ─────────────────────────────────────────────────────────
    'Tripoli':           (34.437,  35.836),
    'Mina':              (34.452,  35.822),
    'Zgharta':           (34.400,  35.889),
    'Batroun':           (34.257,  35.657),
    'Koura':             (34.330,  35.825),
    'Minieh':            (34.404,  35.844),
    'Halba':             (34.548,  36.076),
    'Akkar':             (34.603,  36.197),
    'Bcharre':           (34.251,  36.012),
    'Ehden':             (34.296,  36.013),
    'Kousba':            (34.314,  35.841),

    # ── Bekaa Valley ──────────────────────────────────────────────────────────
    'Zahle':             (33.847,  35.902),
    'Chtaura':           (33.831,  35.887),
    'Baalbek':           (34.004,  36.211),
    'Rayak':             (33.861,  35.991),
    'Anjar':             (33.724,  35.934),
    'Hermel':            (34.395,  36.387),
    'Yohmor':            (34.167,  36.074),
    'Taalbaya':          (33.766,  35.933),

    # ── Chouf / Aley (Mountain) ───────────────────────────────────────────────
    'Aley':              (33.810,  35.600),
    'Chouf':             (33.682,  35.540),
    'Barouk':            (33.673,  35.671),
    'Deir el Qamar':     (33.690,  35.580),
    'Beiteddine':        (33.688,  35.559),
    'Jdita':             (33.751,  35.628),
    'Bchamoun':          (33.810,  35.560),
    'Souk el Gharb':     (33.816,  35.584),
}

# Lebanon map bounds for folium
LEBANON_CENTER = (33.872, 35.862)  # geographic center of Lebanon
LEBANON_BOUNDS = [[33.05, 35.10], [34.69, 36.62]]


def get_coords(area: Optional[str]) -> Optional[Tuple[float, float]]:
    """Return (lat, lng) for an area name, or None if not found."""
    if not area:
        return None
    coords = AREA_COORDS.get(area)
    if coords:
        return coords
    # Case-insensitive fallback
    area_lower = area.lower()
    for name, c in AREA_COORDS.items():
        if name.lower() == area_lower:
            return c
    return None


def get_all_areas() -> list:
    """Return sorted list of all area names with coordinates."""
    return sorted(AREA_COORDS.keys())
