from PIL import Image, ImageDraw, ImageFilter, ImageFont
import random
import math


def read_lyrics_from_md(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    lines = [line.strip() for line in lines if line.strip()]

    # Extract metadata (first 3 lines)
    metadata = lines[:3] if len(lines) >= 3 else []

    lyrics_lines = []
    for line in lines[3:]:
        if line.strip():
            lyrics_lines.append(line)

    return metadata, lyrics_lines


def add_lyrics(draw, width, height, lyrics_lines):
    scale = 2 if width > 2000 else 1

    # Prepare display lines with header
    display_lines = [
        "ZOO - Shakira & Ed Sheeran",
        "",
        "作词 : Blake Slatkin/Shakira/Ed Sheeran",
        "中文填词：白勺",
        ""
    ]
    # Add all lyrics from file
    display_lines.extend(lyrics_lines)

    # Try fonts - smaller size to fit all lyrics
    font = None
    try_fonts = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "SimHei.ttf",
        "msyh.ttc",
        "NotoSansCJK-Regular.ttc",
        "Arial Unicode.ttf",
        "Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf"
    ]

    # Smaller font to fit all lyrics
    font_size = 24 * scale
    title_font_size = 36 * scale

    for font_name in try_fonts:
        try:
            font = ImageFont.truetype(font_name, font_size)
            title_font = ImageFont.truetype(font_name, title_font_size)
            break
        except (IOError, OSError):
            continue

    if font is None:
        font = ImageFont.load_default()
        title_font = font

    # Three-column layout - wider spacing between columns
    column_width = 380 * scale
    gutter = 150 * scale

    left_x = (width - (column_width * 3 + gutter * 2)) // 2
    middle_x = left_x + column_width + gutter
    right_x = middle_x + column_width + gutter

    bbox = font.getbbox("A")
    line_height = bbox[3] - bbox[1] + 14  # Tighter line spacing
    top_margin = 60 * scale

    # Split into three columns
    total_lines = len(display_lines)
    lines_per_col = (total_lines + 2) // 3

    left_lines = display_lines[:lines_per_col]
    middle_lines = display_lines[lines_per_col:lines_per_col*2]
    right_lines = display_lines[lines_per_col*2:]

    text_color = (0, 0, 0)  # Black text
    outline_color = (255, 255, 255)  # White outline
    shadow_color = (255, 255, 255, 150)  # White shadow

    def draw_column(x_pos, lines):
        y = top_margin
        for line in lines:
            if not line.strip():
                y += line_height // 3
                continue

            current_font = title_font if line == display_lines[0] or "作词" in line or "中文填词" in line else font
            text_width = current_font.getlength(line)
            x = x_pos + (column_width - text_width) // 2

            # Draw shadow
            draw.text((x + 2, y + 2), line, font=current_font, fill=shadow_color)

            # Draw outline
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), line, font=current_font, fill=outline_color)

            # Draw main text
            draw.text((x, y), line, font=current_font, fill=text_color)
            y += line_height

    draw_column(left_x, left_lines)
    draw_column(middle_x, middle_lines)
    draw_column(right_x, right_lines)


def draw_leopard_spots(draw, cx, cy, size, color, scale):
    """Draw leopard-style spots"""
    num_spots = 8
    for i in range(num_spots):
        angle = i * (360 / num_spots) + random.uniform(-15, 15)
        rad = math.radians(angle)
        dist = size * 0.6
        sx = cx + math.cos(rad) * dist
        sy = cy + math.sin(rad) * dist
        spot_size = int(size * 0.25)

        # Irregular spot shape
        draw.ellipse([sx - spot_size, sy - spot_size, sx + spot_size, sy + spot_size], fill=color)
        # Add smaller inner spot
        inner_size = spot_size // 2
        draw.ellipse([sx - inner_size, sy - inner_size, sx + inner_size, sy + inner_size], fill=(50, 30, 20))


def create_zoo_image(output_path="zoo.jpg"):
    scale = 2
    # Increase width and height to fit all lyrics
    width, height = 2400 * scale, 1400 * scale
    image = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Yellow-based gradient background - warm yellow tones
    for y in range(0, height, 2):
        progress = y / height
        if progress < 0.33:
            # Light yellow to golden yellow
            p = progress / 0.33
            r = int(255)
            g = int(250 + (220 - 250) * p)
            b = int(200 + (100 - 200) * p)
        elif progress < 0.66:
            # Golden yellow to amber
            p = (progress - 0.33) / 0.33
            r = int(255)
            g = int(220 + (180 - 220) * p)
            b = int(100 - 50 * p)
        else:
            # Amber to deep gold
            p = (progress - 0.66) / 0.34
            r = int(255)
            g = int(180 + (140 - 180) * p)
            b = int(50 - 30 * p)

        draw.line([(0, y), (width, y)], fill=(r, g, b))
        if y + 1 < height:
            draw.line([(0, y+1), (width, y+1)], fill=(r, g, b))

    # Draw abstract "wild" animal print patterns in background
    print_colors = [(255, 200, 100, 30), (255, 150, 50, 25), (200, 100, 200, 20)]

    # Leopard spots scattered
    for _ in range(15):
        cx = random.randint(100 * scale, width - 100 * scale)
        cy = random.randint(100 * scale, height - 100 * scale)
        size = random.randint(60, 120) * scale
        color = (255, 180, 80)
        draw_leopard_spots(draw, cx, cy, size, color, scale)

    # Zebra stripes in corners
    stripe_colors = [(40, 40, 40), (255, 255, 255)]
    for corner in [(0, 0), (width - 200 * scale, 0), (0, height - 200 * scale), (width - 200 * scale, height - 200 * scale)]:
        for i in range(10):
            x1 = corner[0] + i * 20 * scale
            y1 = corner[1]
            x2 = corner[0] + i * 20 * scale + 10 * scale
            y2 = corner[1] + 150 * scale
            color = stripe_colors[i % 2]
            draw.polygon([(x1, y1), (x2, y1), (x2 + 30 * scale, y2), (x1 + 30 * scale, y2)], fill=color)

    # Disco lights effect
    light_colors = [
        (255, 50, 100),   # Hot pink
        (255, 150, 0),    # Orange
        (255, 255, 50),   # Yellow
        (50, 255, 150),   # Green
        (50, 150, 255),   # Blue
        (200, 50, 255),   # Purple
    ]

    # Draw light beams
    for i in range(12):
        angle = i * 30
        rad = math.radians(angle)
        beam_length = width
        start_x = width // 2
        start_y = -50 * scale

        end_x = start_x + math.cos(rad) * beam_length
        end_y = start_y + math.sin(rad) * beam_length

        color = light_colors[i % len(light_colors)]
        # Draw fading beam
        for offset in range(-20, 21, 5):
            alpha = max(0, 30 - abs(offset))
            perp_angle = angle + 90
            perp_rad = math.radians(perp_angle)
            dx = math.cos(perp_rad) * offset
            dy = math.sin(perp_rad) * offset

            draw.line([(start_x + dx, start_y + dy), (end_x + dx, end_y + dy)],
                     fill=color, width=2)

    # Random bright spotlights
    for _ in range(8):
        x = random.randint(100 * scale, width - 100 * scale)
        y = random.randint(50 * scale, 200 * scale)
        radius = random.randint(50, 100) * scale
        color = random.choice(light_colors)

        # Glow effect
        for r in range(radius, 0, -5):
            alpha = int(255 * (r / radius) * 0.3)
            glow_color = tuple(min(255, c + alpha // 3) for c in color)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=None, outline=glow_color, width=3)

    # Party confetti
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(5, 15)
        color = random.choice(light_colors)

        # Small rectangles as confetti
        rotation = random.randint(0, 45)
        draw.rectangle([x, y, x + size, y + size], fill=color)

    # Floor/grid pattern at bottom
    floor_y = int(height * 0.90)
    for x in range(0, width + 1, 40 * scale):
        # Perspective lines
        draw.line([(x, floor_y), (width // 2 + (x - width // 2) * 2, height)],
                 fill=(255, 255, 255), width=1)

    # Horizontal floor lines
    for y in range(floor_y, height, 20 * scale):
        progress = (y - floor_y) / (height - floor_y)
        line_width = int(width * (0.5 + progress))
        x_start = (width - line_width) // 2
        x_end = x_start + line_width
        draw.line([(x_start, y), (x_end, y)], fill=(255, 255, 255), width=1)

    # Add very strong blur for background虚化 effect
    image = image.filter(ImageFilter.GaussianBlur(radius=scale * 6.0))

    # Recreate draw object
    draw = ImageDraw.Draw(image)

    # Read lyrics and add to image
    try:
        filepath = "/Users/nicole/workspace/github/a476678244/python_gallery/music/lyrics/zoo.md"
        metadata, lyrics = read_lyrics_from_md(filepath)
        add_lyrics(draw, width, height, lyrics)
    except Exception as e:
        print(f"Error reading lyrics: {e}")
        # Fallback
        add_lyrics(draw, width, height, [])

    # Save as JPEG
    image = image.convert('RGB')
    image.save(output_path, quality=95, optimize=True)
    print(f"ZOO image saved as {output_path}")


if __name__ == "__main__":
    create_zoo_image("/Users/nicole/workspace/github/a476678244/python_gallery/music/lyrics/zoo.jpg")
