"""Renders the RustOS logo (same geometry as logo.svg) to PNGs + a wallpaper.
Only needs Pillow:  pip install pillow"""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 4  # supersampling

def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def draw_logo(size):
    k = size * S / 256.0
    W = int(size * S)
    pt = lambda x, y: (x * k, y * k)
    # gradient
    top, bot = (255, 154, 60), (194, 65, 12)
    grad = Image.new("RGB", (W, W))
    px = grad.load()
    for y in range(W):
        for x in range(W):
            px[x, y] = lerp(top, bot, (x + y) / (2 * W))
    hexa = [(128,12),(228,70),(228,186),(128,244),(28,186),(28,70)]
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).polygon([pt(*p) for p in hexa], fill=255)
    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img, "RGBA")
    inner = [(128,30),(212,79),(212,177),(128,226),(44,177),(44,79)]
    d.line([pt(*p) for p in inner + [inner[0]]], fill=(255,255,255,90), width=int(4*k), joint="curve")

    sw = 22 * k
    def stroke(points):
        for a, b in zip(points, points[1:]):
            d.line([pt(*a), pt(*b)], fill=(255,255,255,255), width=int(sw))
        for p in points:
            x, y = pt(*p); r = sw / 2
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255,255,255,255))
    # R: stem, top bar, bowl (arc), back bar, leg
    arc = [(136 + 35*math.cos(math.radians(a)), 107 + 35*math.sin(math.radians(a)))
           for a in range(-90, 91, 6)]
    stroke([(98,184),(98,72),(136,72)] + arc + [(98,142)])
    stroke([(136,142),(170,184)])
    return img.resize((size, size), Image.LANCZOS)

here = os.path.dirname(os.path.abspath(__file__))
for s in (512, 256, 128, 64, 48):
    draw_logo(s).save(os.path.join(here, f"logo-{s}.png"))

# wallpaper 1920x1080
W, H = 1920, 1080
bg = Image.new("RGB", (W, H))
p = bg.load()
c1, c2 = (20, 17, 15), (58, 26, 8)
for y in range(H):
    for x in range(W):
        t = (x / W * 0.6 + y / H * 0.4)
        p[x, y] = lerp(c1, c2, t)
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse([W//2 - 420, H//2 - 420, W//2 + 420, H//2 + 420], fill=(255, 120, 30, 60))
glow = glow.filter(ImageFilter.GaussianBlur(160))
bg = Image.alpha_composite(bg.convert("RGBA"), glow)
logo = draw_logo(360)
bg.alpha_composite(logo, (W//2 - 180, H//2 - 250))
try:
    import matplotlib
    font = ImageFont.truetype(os.path.join(os.path.dirname(matplotlib.__file__),
                              "mpl-data/fonts/ttf/DejaVuSans-Bold.ttf"), 84)
except Exception:
    font = ImageFont.load_default()
dd = ImageDraw.Draw(bg)
text = "RustOS"
w = dd.textlength(text, font=font)
dd.text(((W - w) / 2, H//2 + 150), text, font=font, fill=(255, 255, 255, 235))
bg.convert("RGB").save(os.path.join(here, "wallpaper.png"))
print("ok")
