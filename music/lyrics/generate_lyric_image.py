from PIL import Image, ImageDraw, ImageFilter, ImageFont
import random
import math


def read_lyrics_from_md(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Remove empty lines and clean up
    lines = [line.strip() for line in lines if line.strip()]

    # Extract song title (first line)
    title = lines[0] if lines else ""

    # Group lyrics into verses (group lines until an empty line is found)
    verses = []
    current_verse = []

    for line in lines[1:]:  # Skip the title
        if line.strip() == "":
            if current_verse:
                verses.append(current_verse)
                current_verse = []
        else:
            current_verse.append(line)

    if current_verse:  # Add the last verse if not empty
        verses.append(current_verse)

    return title, verses

def add_lyrics(draw, width, height):
    # Calculate scale factor (assuming 2x scale for high DPI)
    scale = 2 if width > 2000 else 1
    # Read lyrics from the markdown file
    try:
        lyrics_file = "/Users/nicole/workspace/github/a476678244/python_gallery/music/lyrics/离别开出花.md"
        title, verses = read_lyrics_from_md(lyrics_file)

        # Prepare lyrics for display (flatten verses and add some spacing)
        lyrics = [title, "", "就是南方凯", ""]  # Title and artist with spacing

        # Add verses with spacing in between
        for verse in verses:
            lyrics.extend(verse)
            lyrics.append("")  # Add empty line after each verse
    except Exception as e:
        print(f"Error reading lyrics file: {e}")
        # Fallback to default lyrics if file can't be read
        lyrics = [
            "离别开出花 - 就是南方凯",
            "",
            "坐上那朵离家的云霞",
            "飘去无人知晓的天涯",
            "背着妈妈说的那句话",
            "孩子人生其实不复杂",
            "",
            "当离别开出花",
            "伸出新长的枝桠",
            "像冬去春又来",
            "等待心雪融化"
        ]

    print(f"Lyrics to display: {lyrics}")

    # Try to use a nice Chinese font if available
    font = None
    # Common Chinese fonts on different systems
    try_fonts = [
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS
        "SimHei.ttf",  # Windows
        "msyh.ttc",    # Microsoft YaHei
        "NotoSansCJK-Regular.ttc", # Common Linux/Android
        "Arial Unicode.ttf",  # Fallback
        "Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf"  # Common macOS location
    ]

    # Set font sizes (scale up for high DPI)
    font_size = 22 * scale  # Scaled for high DPI
    title_font_size = 26 * scale  # Larger for title/artist
    for font_name in try_fonts:
        try:
            print(f"Trying font: {font_name}")
            font = ImageFont.truetype(font_name, font_size)
            title_font = ImageFont.truetype(font_name, title_font_size)
            print(f"Successfully loaded font: {font_name}")
            break
        except (IOError, OSError) as e:
            print(f"Failed to load font {font_name}: {e}")
            continue

    # If no font was loaded, try to load default font
    if font is None:
        try:
            print("Trying default font")
            font = ImageFont.load_default()
            print("Using default font")
        except AttributeError as e:
            print(f"Failed to load default font: {e}")
            return  # Can't draw without a font

    # Set up three-column layout with adjusted spacing for tree
    column_width = 320 * scale  # Scaled for high DPI
    gutter = 50 * scale  # Scaled for high DPI

    # Calculate column positions, shifted slightly right to make room for tree
    left_shift = 50 * scale  # Scaled for high DPI
    left_x = (width - (column_width * 3 + gutter * 2)) // 2 + left_shift
    middle_x = left_x + column_width + gutter
    right_x = middle_x + column_width + gutter

    # Calculate line height and margins
    bbox = font.getbbox("A")
    line_height = bbox[3] - bbox[1] + 8  # Further reduced padding
    top_margin = height // 8  # Start even higher up
    max_lines_per_column = (height - top_margin * 2) // line_height

    # Set text colors
    text_color = (255, 255, 255)  # White
    outline_color = (0, 0, 0)     # Black

    # Split lyrics into three columns
    column1 = []
    column2 = []
    column3 = []

    # Distribute lines evenly across three columns
    lines_per_column = (len(lyrics) + 2) // 3  # Ceiling division for 3 columns

    column1 = lyrics[:lines_per_column]
    column2 = lyrics[lines_per_column:lines_per_column*2]
    column3 = lyrics[lines_per_column*2:]

    # Function to draw a single column
    def draw_column(x_pos, lines):
        y = top_margin
        for line in lines:
            if not line.strip():
                y += line_height // 4  # Very small space for empty lines
                continue

            # Use larger font for title and artist
            current_font = title_font if line in [lyrics[0], lyrics[2]] else font
            text_width = current_font.getlength(line)
            x = x_pos + (column_width - text_width) // 2

            # Draw outline (thinner for smaller text)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), line, font=current_font, fill=outline_color)

            # Draw main text
            draw.text((x, y), line, font=current_font, fill=text_color)
            y += line_height

    # Draw all three columns
    draw_column(left_x, column1)
    draw_column(middle_x, column2)
    draw_column(right_x, column3)

def create_cherry_blossom_image(output_path="cherry_blossom_lyrics.png"):
    # Create a high resolution image (2x scale for better quality)
    scale = 2
    width, height = 1600 * scale, 900 * scale
    image = Image.new('RGB', (width, height), (20, 10, 40))
    draw = ImageDraw.Draw(image)

    # Draw gradient background (darker at top, lighter at bottom)
    for y in range(0, height, 2):  # Skip every other line for faster rendering
        # Create a gradient from dark blue to dark purple
        r = int(20 + 30 * (y / height))
        g = int(10 + 5 * (y / height))
        b = int(40 + 10 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        if y + 1 < height:  # Fill the skipped line
            draw.line([(0, y+1), (width, y+1)], fill=(r, g, b))

    # Draw stars (more stars for higher resolution)
    for _ in range(300):
        x = random.randint(0, width)
        y = random.randint(0, height//2)  # Mostly in upper half
        size = random.randint(1, 4) * scale // 2  # Scale star sizes
        brightness = random.randint(200, 255)
        draw.ellipse([x, y, x+size, y+size], fill=(brightness, brightness, brightness))

    # Draw crescent moon (scaled)
    moon_center = (width - 200 * scale, 150 * scale)
    moon_radius = 60 * scale
    draw.ellipse([moon_center[0]-moon_radius, moon_center[1]-moon_radius,
                  moon_center[0]+moon_radius, moon_center[1]+moon_radius],
                 fill=(255, 240, 200), outline=None)

    # Draw cherry blossom tree (shifted left and scaled)
    tree_shift = 100 * scale  # How much to shift the tree to the left
    trunk_bottom = (width//2 - tree_shift, height - 50 * scale)
    trunk_top = (width//2 - tree_shift, height//2)
    branch_length = 200 * scale

    # Draw trunk and branches
    def draw_branch(start, length, angle, width):
        if length < 5:
            return

        # Ensure width is at least 1 and is an integer
        width = max(1, int(width))

        # Calculate end point
        rad = math.radians(angle)
        end = (int(start[0] + math.cos(rad) * length),
               int(start[1] - math.sin(rad) * length))

        # Ensure start points are integers
        start = (int(start[0]), int(start[1]))

        # Draw branch
        draw.line([start, end], fill=(70, 35, 20), width=width)

        # Recursively draw smaller branches
        if length > 20:
            # Main branching
            draw_branch(end, length * 0.7, angle + 25, width * 0.7)
            draw_branch(end, length * 0.7, angle - 25, width * 0.7)

            # Add some random smaller branches
            if random.random() > 0.3:
                draw_branch(end, length * 0.5, angle + 10, width * 0.6)
            if random.random() > 0.3:
                draw_branch(end, length * 0.5, angle - 10, width * 0.6)

        # Add blossoms at the end of smaller branches
        if length < 30:
            for _ in range(int(5 - length/10)):
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-5, 5)
                blossom_size = random.randint(5, 10)
                blossom_pos = (end[0] + offset_x, end[1] + offset_y)

                # Draw blossom (pink with white center)
                draw.ellipse([blossom_pos[0]-blossom_size//2, blossom_pos[1]-blossom_size//2,
                              blossom_pos[0]+blossom_size//2, blossom_pos[1]+blossom_size//2],
                             fill=(255, 200, 220), outline=(255, 230, 240))

    # Start drawing the tree
    draw_branch(trunk_top, 100, 90, 15)

    # Add falling petals (more petals for higher resolution)
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(3, 8) * scale // 2  # Scale petal sizes
        opacity = random.randint(100, 200)
        petal_color = (255, 200, 220, opacity)

        # Create a new image with alpha channel for the petal
        petal = Image.new('RGBA', (size*2, size*2), (0, 0, 0, 0))
        petal_draw = ImageDraw.Draw(petal)
        petal_draw.ellipse([0, 0, size*2, size*2], fill=petal_color)

        # Rotate the petal randomly
        petal = petal.rotate(random.randint(0, 360), expand=1)

        # Paste the petal onto the main image
        image.paste(petal, (x, y), petal)

    # Add some blur to create depth (slightly more for higher resolution)
    image = image.filter(ImageFilter.GaussianBlur(radius=scale * 0.7))

    # Recreate the draw object after filtering
    draw = ImageDraw.Draw(image)

    # Add the lyrics to the image
    add_lyrics(draw, width, height)

    # Save the image with high DPI
    image.save(output_path, dpi=(300, 300), quality=95, optimize=True)
    print(f"High resolution image saved as {output_path}")

if __name__ == "__main__":
    create_cherry_blossom_image()
