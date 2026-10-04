"""Renders the RustOS logo as colored block art for fastfetch.
Output: overlay/airootfs/usr/share/rustos/fastfetch-logo.txt  ($1..$5 = orange bands, $6 = white)"""
import math, os
COLS, ROWS = 44, 25
X0, X1, Y0, Y1 = 28, 228, 12, 244
hexa = [(128,12),(228,70),(228,186),(128,244),(28,186),(28,70)]

def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c

def dseg(px, py, a, b):
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

arc = [(136 + 35 * math.cos(math.radians(a)), 107 + 35 * math.sin(math.radians(a))) for a in range(-90, 91, 10)]
polys = [[(98,184),(98,72),(136,72)] + arc + [(98,142)], [(136,142),(170,184)]]
segs = [(p[i], p[i+1]) for p in polys for i in range(len(p) - 1)]

lines = []
for r in range(ROWS):
    y = Y0 + (r + 0.5) * (Y1 - Y0) / ROWS
    band = min(4, r * 5 // ROWS) + 1
    out, cur = "", None
    for c in range(COLS):
        x = X0 + (c + 0.5) * (X1 - X0) / COLS
        if min(dseg(x, y, a, b) for a, b in segs) <= 8.5:
            col, ch = 6, "█"
        elif inside(x, y, hexa):
            col, ch = band, "█"
        else:
            col, ch = cur, " "
        if ch != " " and col != cur:
            out += f"${col}"; cur = col
        out += ch
    lines.append(out.rstrip())
dest = os.path.join(os.path.dirname(__file__), "..", "overlay/airootfs/usr/share/rustos/fastfetch-logo.txt")
open(dest, "w").write("\n".join(lines) + "\n")
print(open(dest).read().replace("$1","").replace("$2","").replace("$3","").replace("$4","").replace("$5","").replace("$6","").replace("█","#" ))
