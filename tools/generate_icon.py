from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def draw_icon(size: int) -> Image.Image:
    scale = size / 32
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def p(points):
        return [(round(x * scale), round(y * scale)) for x, y in points]

    draw.ellipse(p([(2, 2), (30, 30)]), fill="#1e1e2e", outline="#89b4fa", width=max(1, round(2 * scale)))

    body = p([(8, 18), (10, 12), (16, 9), (22, 12), (27, 15), (25, 20), (19, 24), (10, 21)])
    draw.polygon(body, fill="#89b4fa")
    draw.polygon(p([(8, 18), (4, 14), (9, 17), (5, 20), (9, 19)]), fill="#b4befe")
    draw.ellipse(p([(20, 15), (22, 17)]), fill="#1e1e2e")
    draw.polygon(p([(14, 10), (16, 4), (18, 10), (16, 8)]), fill="#cdd6f4")
    return img


images = [draw_icon(size) for size in (256, 128, 64, 48, 32, 16)]
images[0].save(ASSETS / "app_icon.ico", sizes=[(i.width, i.height) for i in images], append_images=images[1:])
images[2].save(ASSETS / "app_icon.png")
print(ASSETS / "app_icon.ico")
