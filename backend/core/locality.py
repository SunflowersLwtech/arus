"""Malaysian locality mapping for the 20x20 flood grid.

Maps abstract grid quadrants to Malaysian kampung / district names so the
agency-dispatcher's hand-off briefs reference real Malaysian geography.
This is what makes commanders take the system seriously — generic
"sector NE" reports feel academic; "Kg. Manik Urai" reads like BOMBA-grade intel.

Based on historical flood zones:
- Dec 2014 Kelantan mega-flood (Gua Musang, Kuala Krai)
- Dec 2024 Johor + east-coast flood (148,024 evacuees per NADMA)
- Dec 2024 Kedah-Perlis late-season event
Demo Day is hosted at UTM Skudai (Johor), so we keep Johor front-and-centre.
"""

LOCALITIES = [
    # NW quadrant — Hulu Kelantan (mountainous, flash-flood prone)
    {"x_range": (0, 10), "y_range": (0, 10), "district": "Gua Musang, Kelantan",
     "state": "Kelantan",
     "kampungs": ["Kg. Manik Urai", "Kg. Dabong", "Kg. Kuala Krai", "Kg. Aring"]},
    # NE — Kuala Krai to Tanah Merah
    {"x_range": (0, 10), "y_range": (10, 20), "district": "Kuala Krai, Kelantan",
     "state": "Kelantan",
     "kampungs": ["Kg. Laloh", "Kg. Tualang", "Kg. Kubang Puteh", "Kg. Karangan"]},
    # SW — Johor Kota Tinggi (Dec 2024 badly hit)
    {"x_range": (10, 20), "y_range": (0, 10), "district": "Kota Tinggi, Johor",
     "state": "Johor",
     "kampungs": ["Kg. Ulu Tiram", "Kg. Lukut", "Kg. Mawai", "Kg. Panti"]},
    # SE — Segamat / Labis (Dec 2024 Johor)
    {"x_range": (10, 20), "y_range": (10, 20), "district": "Segamat, Johor",
     "state": "Johor",
     "kampungs": ["Kg. Labis", "Kg. Tenang Stesen", "Kg. Jementah", "Kg. Sagil"]},
]


def locate(x: int, y: int) -> dict:
    """Return district + best-guess kampung + state for grid cell (x, y)."""
    for zone in LOCALITIES:
        x0, x1 = zone["x_range"]
        y0, y1 = zone["y_range"]
        if x0 <= x < x1 and y0 <= y < y1:
            kampungs = zone["kampungs"]
            dx = (x - x0) / max(1, x1 - x0 - 1)
            dy = (y - y0) / max(1, y1 - y0 - 1)
            idx = min(len(kampungs) - 1, int(dx * 2) + int(dy * 2) * 2)
            return {
                "district": zone["district"],
                "kampung": kampungs[idx],
                "state": zone["state"],
                "coords": (x, y),
            }
    return {"district": "Unknown", "kampung": "Unknown", "state": "Unknown", "coords": (x, y)}


def summarise_zone() -> str:
    """One-line BM/EN zone header for the dashboard."""
    return (
        "Zon operasi: Kelantan (Gua Musang / Kuala Krai) + Johor (Kota Tinggi / Segamat) "
        "monsoon flood belt | Operational zone: east-coast monsoon belt"
    )
