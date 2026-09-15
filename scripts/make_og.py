"""生成站点默认社交分享图 public/og-default.png（1200x630）。

后台没有为页面配置封面 / 照片时，<meta og:image> 会回退到这张站点卡片，
避免 twitter:card=summary_large_image 却没有图的「空卡片」。

用法：.venv/Scripts/python.exe scripts/make_og.py
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
site = json.loads((ROOT / "src" / "data" / "site.json").read_text(encoding="utf-8"))
W, H = 1200, 630
img = Image.new("RGB", (W, H), "#0b1a3a")
d = ImageDraw.Draw(img)

# 蓝色渐变背景
top, bottom = (26, 86, 219), (8, 20, 47)
for y in range(H):
    t = y / (H - 1)
    d.line([(0, y), (W, y)], fill=tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))

# 右上角装饰同心圆
for r in (300, 200, 110):
    cx, cy = 1010, 190
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=2)


def font(names, size):
    for n in names:
        p = Path("C:/Windows/Fonts") / n
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


f_name = font(["msyhbd.ttc", "msyh.ttc"], 66)
f_en = font(["arialbd.ttf", "arial.ttf"], 30)
f_tag = font(["msyh.ttc"], 32)
f_abbr = font(["msyhbd.ttc"], 40)

d.text((84, 168), site["name"], font=f_name, fill="white")
d.text((84, 258), site.get("nameEn", ""), font=f_en, fill=(178, 205, 255))
d.line([(84, 320), (180, 320)], fill=(255, 255, 255), width=4)

line, lines = "", []
for ch in site.get("tagline", ""):
    if d.textlength(line + ch, font=f_tag) > 620:
        lines.append(line)
        line = ch
    else:
        line += ch
lines.append(line)
for i, ln in enumerate(lines[:2]):
    d.text((84, 356 + i * 46), ln, font=f_tag, fill=(226, 235, 255))

d.text((84, 520), site.get("affiliation", ""), font=f_tag, fill=(150, 180, 235))
d.text((84, 92), site.get("abbr", ""), font=f_abbr, fill=(140, 180, 255))

out = ROOT / "public" / "og-default.png"
img.save(out, "PNG", optimize=True)
print("wrote", out, out.stat().st_size, "bytes")
