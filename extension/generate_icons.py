from PIL import Image, ImageDraw

sizes = [16, 48, 128]

for size in sizes:
    img = Image.new("RGB", (size, size), color="#1e7e34")
    draw = ImageDraw.Draw(img)
    margin = size // 6
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill="#e6f4ea",
        outline="#1e7e34",
        width=max(1, size // 20),
    )
    img.save(f"extension/icon{size}.png")

print("Icons generated.")