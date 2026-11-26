"""Builds the SVG charts (light and dark) from data/.

Usage: python tools/make_charts.py
"""
import csv
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", soft="#52514e", axis="#c3c2b7", grid="#e1e0d9",
                  s1="#2a78d6", s2="#eb6834", muted="#b4b2a8"),
    "dark": dict(surface="#1a1a19", ink="#f0efec", soft="#c3c2b7", axis="#4a4a46", grid="#2c2c2a",
                 s1="#3987e5", s2="#d95926", muted="#6a6964"),
}
FONT = "system-ui,-apple-system,'Segoe UI',sans-serif"


def num(v, decimals=1):
    return f"{v:.{decimals}f}"


def text(x, y, content, color, size=13, anchor="start", weight=400):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(content)}</text>')


def bar(x, y, width, height, color, tooltip):
    """A bar with a rounded data end and a square baseline."""
    r = min(4, width / 2)
    d = (f"M{x},{y}h{width - r}a{r},{r} 0 0 1 {r},{r}v{height - 2 * r}"
         f"a{r},{r} 0 0 1 -{r},{r}h-{width - r}z")
    return f'<path d="{d}" fill="{color}"><title>{escape(tooltip)}</title></path>'


def chart(name, title, subtitle, rows, series, maximum, step, unit, decimals=1, margin=290, highlight=None):
    """rows: [(label, [values])]; series: [(name, colour key)]."""
    for theme, c in THEMES.items():
        n = len(series)
        bar_h, gap = 18, 2
        group_h = n * bar_h + (n - 1) * gap
        row_h = group_h + 16
        top = 96 if n > 1 else 70
        width, height = 880, top + row_h * len(rows) + 34
        plot = width - margin - 90
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
             f'<rect width="{width}" height="{height}" rx="8" fill="{c["surface"]}"/>',
             text(20, 30, title, c["ink"], 17, weight=600),
             text(20, 52, subtitle, c["soft"], 13)]
        if n > 1:
            x = 20
            for label, key in series:
                s.append(f'<rect x="{x}" y="68" width="12" height="12" rx="3" fill="{c[key]}"/>')
                s.append(text(x + 18, 79, label, c["soft"], 12))
                x += 48 + 7 * len(label)
        bottom = top + row_h * len(rows)
        v = 0
        while v <= maximum + 1e-9:
            gx = margin + plot * v / maximum
            s.append(f'<line x1="{gx}" y1="{top}" x2="{gx}" y2="{bottom}" '
                     f'stroke="{c["axis"] if v == 0 else c["grid"]}" stroke-width="1"/>')
            s.append(text(gx, bottom + 18, num(v, 0), c["soft"], 11, "middle"))
            v += step
        for i, (label, values) in enumerate(rows):
            y = top + i * row_h + 8
            strong = highlight is not None and i in highlight
            s.append(text(margin - 10, y + group_h / 2 + 4, label,
                          c["ink"] if strong else c["soft"], 13, "end", 600 if strong else 400))
            for j, value in enumerate(values):
                colour = c[series[j][1]]
                if highlight is not None and not strong:
                    colour = c["muted"]
                by = y + j * (bar_h + gap)
                w = max(2, plot * value / maximum)
                s.append(bar(margin, by, w, bar_h, colour, f"{label}: {num(value, decimals)} {unit}"))
                s.append(text(margin + w + 6, by + 13, f"{num(value, decimals)} {unit}", c["ink"], 12))
        s.append("</svg>")
        path = os.path.join(ROOT, "charts", f"{name}-{theme}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(s) + "\n")


def read(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


os.makedirs(os.path.join(ROOT, "charts"), exist_ok=True)
runs = {r["id"]: r for r in read("same_scene_runs.csv")}
order = [("base", "Baseline"), ("lowfx", "Fewer effects"), ("scale50", "Half render scale"),
         ("awake0", "Card keep-awake off"), ("card1024", "Copies on the card: 1 GB"),
         ("c1", "Copies on the card: 2 GB"), ("c2", "2 GB + keep-awake off")]
chart("fps-same-scene", "From 7.2 to 12.6 fps in the same scene",
      "cool_fox · RTX 2070 at x16 · prologue, about 6,000 draws per frame · higher is better",
      [(label, [float(runs[i]["fps"])]) for i, label in order], [("fps", "s1")], 14, 2, "fps", highlight={6})

before, after = runs["base"], runs["c2"]
chart("frame-time", "Where each frame goes (milliseconds)",
      "Same scene · lower is better · separate measures, they do not add up",
      [(label, [float(before[k]), float(after[k])]) for k, label in (
          ("frame_ms", "Whole frame"),
          ("prepare_ms", "Preparing submissions (CPU)"),
          ("copy_back_ms", "Copying memory back"))],
      [("Baseline (7.2 fps)", "s1"), ("Best configuration (12.6 fps)", "s2")], 160, 40, "ms", 0)

memory = [("Belobug, unmodified", 27.1, 7.7), ("Belobug, light mode", 23.6, 6.9),
          ("cool_fox, 256 px textures, 1080p", 19.3, 6.2), ("cool_fox, 256 px textures, 720p", 18.2, 6.3)]
chart("memory-ram", "System memory used by the game (GB)",
      "Private memory of the process · the PC has 32 GB · lower is better",
      [(label, [ram]) for label, ram, _ in memory], [("GB", "s1")], 32, 8, "GB")
chart("memory-vram", "Video memory in use (GB)",
      "As reported by nvidia-smi, other apps included · the card has 8 GB · lower is better",
      [(label, [vram]) for label, _, vram in memory], [("GB", "s1")], 8, 2, "GB")
print("charts written:", len(os.listdir(os.path.join(ROOT, "charts"))))
