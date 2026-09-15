"""从 favicon.svg 的视觉风格生成 public/favicon.ico（多尺寸），补齐浏览器默认请求。"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 圆角蓝底 + 竖向渐变
grad = Image.new("RGBA", (S, S))
gd = ImageDraw.Draw(grad)
for y in range(S):
    t = y / (S - 1)
    gd.line([(0, y), (S, y)], fill=(round(47 + (20 - 47) * t), round(107 + (66 - 107) * t), 255, 255))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 15 / 64), fill=255)
img.paste(grad, (0, 0), mask)

def sc(v):
    return v * S / 64

# 与 favicon.svg 相同的几何：圆圈 + 圆点 + 连线
d.ellipse([sc(17), sc(19), sc(31), sc(33)], outline=(255, 255, 255, 255), width=int(sc(3)))
d.ellipse([sc(36.5), sc(33.5), sc(45.5), sc(42.5)], fill=(255, 255, 255, 255))
d.line([sc(29), sc(30.5), sc(37), sc(35)], fill=(255, 255, 255, 255), width=int(sc(3)))

out = ROOT / "public" / "favicon.ico"
img.save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote", out, out.stat().st_size, "bytes")
