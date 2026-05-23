#!/usr/bin/env python3
"""
Lyric Image Generation Script
Generates beautiful lyric images with themed backgrounds based on song lyrics.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import random
import math
import argparse
import os


def read_lyrics_from_md(filepath):
    """Read lyrics from markdown file and extract title, verses, and credits."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Remove empty lines and clean up
    lines = [line.strip() for line in lines if line.strip()]

    # Extract song title (first line)
    title = lines[0] if lines else ""

    # Identify metadata/credits lines (contain: 作词, 作曲, 编曲, 制作, etc.)
    credit_keywords = ['作词', '作曲', '编曲', '制作', '监制', '录音', '混音', '母带', '出品', '发行']
    credits = []
    lyrics_lines = []

    for line in lines[1:]:  # Skip the title
        is_credit = any(kw in line for kw in credit_keywords)
        if is_credit:
            credits.append(line)
        else:
            lyrics_lines.append(line)

    # Group lyrics into verses
    verses = []
    current_verse = []

    for line in lyrics_lines:
        if line.strip() == "":
            if current_verse:
                verses.append(current_verse)
                current_verse = []
        else:
            current_verse.append(line)

    if current_verse:  # Add the last verse if not empty
        verses.append(current_verse)

    return title, verses, credits


def detect_theme(lyrics):
    """Detect the appropriate theme based on lyrics content."""
    lyrics_text = " ".join(lyrics).lower()
    
    # Theme keywords
    sunny_keywords = ["阳光", "清晨", "太阳", "sun", "morning", "day"]
    nature_keywords = ["山川", "江河", "山", "河", "mountain", "river", "nature"]
    flower_keywords = ["花朵", "花儿", "花", "flower", "blossom"]
    night_keywords = ["傍晚", "夜晚", "月", "星", "evening", "night", "moon", "star"]
    
    scores = {
        "sunny": sum(1 for kw in sunny_keywords if kw in lyrics_text),
        "nature": sum(1 for kw in nature_keywords if kw in lyrics_text),
        "flower": sum(1 for kw in flower_keywords if kw in lyrics_text),
        "night": sum(1 for kw in night_keywords if kw in lyrics_text)
    }
    
    # Return theme with highest score
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "sunny"


def add_lyrics(draw, width, height, lyrics_file, artist_credit=""):
    """Add lyrics to the image with three-column layout and credits at bottom."""
    # Calculate scale factor (assuming 2x scale for high DPI)
    scale = 2 if width > 2000 else 1
    
    # Read lyrics from the markdown file
    try:
        title, verses, file_credits = read_lyrics_from_md(lyrics_file)

        # Prepare lyrics for display (flatten verses and add some spacing)
        lyrics = [title, ""]
        if artist_credit:
            lyrics.extend([artist_credit, ""])

        # Add verses with spacing in between
        for verse in verses:
            lyrics.extend(verse)
            lyrics.append("")  # Add empty line after each verse
        
        # Combine all credits for bottom line
        all_credits = file_credits if file_credits else []
        if artist_credit and artist_credit not in all_credits:
            all_credits.insert(0, artist_credit)
        credits_line = " | ".join(all_credits[:5]) if all_credits else ""  # Limit to first 5 credits
    except Exception as e:
        print(f"Error reading lyrics file: {e}")
        # Fallback to default lyrics if file can't be read
        lyrics = [
            "Lyrics Image",
            "",
            "Unable to read lyrics file",
            "",
            "Please check the file path",
            "and try again"
        ]
        credits_line = ""

    print(f"Lyrics to display: {lyrics}")
    print(f"Credits line: {credits_line}")

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
    font_size = 24 * scale  # Smaller font for dispersed layout
    title_font_size = 32 * scale  # Smaller for title/artist
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
            title_font = ImageFont.load_default()
            print("Using default font")
        except AttributeError as e:
            print(f"Failed to load default font: {e}")
            return  # Can't draw without a font

    # Set up three-column layout
    column_width = 320 * scale  # Scaled for high DPI
    gutter = 50 * scale  # Scaled for high DPI

    # Calculate column positions
    left_shift = 50 * scale  # Scaled for high DPI
    left_x = (width - (column_width * 3 + gutter * 2)) // 2 + left_shift
    middle_x = left_x + column_width + gutter
    right_x = middle_x + column_width + gutter

    # Calculate line height and margins
    bbox = font.getbbox("A")
    line_height = bbox[3] - bbox[1] + 35  # More spacing for dispersed layout
    top_margin = height // 10  # Adjusted top margin
    
    # Reserve space for credits line at bottom (adaptive height)
    bottom_reserve = 100 * scale if credits_line else 20 * scale
    available_height = height - top_margin - bottom_reserve
    max_lines_per_column = available_height // line_height

    # Set text colors
    text_color = (0, 0, 0)  # Black
    outline_color = (255, 255, 255)  # White outline for contrast

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
        max_y = height - bottom_reserve - line_height  # Don't draw in credits area
        for line in lines:
            # Stop if we've reached the bottom reserve area
            if y > max_y:
                break
                
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

    # Draw credits line at bottom if exists
    if credits_line:
        credit_font_size = 18 * scale
        try:
            credit_font = ImageFont.truetype(font.font.family if hasattr(font, 'font') else "/System/Library/Fonts/STHeiti Medium.ttc", credit_font_size)
        except:
            credit_font = font
        
        credit_width = credit_font.getlength(credits_line)
        credit_x = (width - credit_width) // 2
        credit_y = height - 60 * scale
        
        # Draw outline for credits
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                draw.text((credit_x + dx, credit_y + dy), credits_line, font=credit_font, fill=outline_color)
        
        # Draw credits text
        draw.text((credit_x, credit_y), credits_line, font=credit_font, fill=text_color)
    
    return credits_line  # Return for potential use


def draw_sunny_theme(draw, width, height, scale):
    """Draw soft, light pastel theme that complements lyrics elegantly."""
    # Draw soft gradient background (very light cream to pale blue)
    for y in range(0, height, 2):
        progress = y / height
        # Soft cream to pale blue gradient
        r = int(250 - 20 * progress)
        g = int(248 - 15 * progress)
        b = int(245 + 10 * progress)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        if y + 1 < height:
            draw.line([(0, y+1), (width, y+1)], fill=(r, g, b))

    # Draw soft sun glow (very subtle, positioned in corner)
    sun_center = (width - 150 * scale, 100 * scale)
    sun_radius = 80 * scale
    # Soft sun with gradient effect
    for r in range(sun_radius, 0, -5):
        alpha = int(255 * (1 - r / sun_radius) * 0.3)
        color = (255, 250, 230)
        draw.ellipse([sun_center[0]-r, sun_center[1]-r,
                      sun_center[0]+r, sun_center[1]+r],
                     fill=color)

    # Draw very soft, light mountain silhouettes
    mountain_colors = [(200, 210, 220), (220, 225, 230), (235, 238, 240)]
    for i, color in enumerate(mountain_colors):
        base_y = height - 100 * scale + i * 25 * scale
        points = [
            (0, height),
            (width * 0.15, base_y - 150 * scale),
            (width * 0.35, base_y - 100 * scale),
            (width * 0.55, base_y - 180 * scale),
            (width * 0.75, base_y - 120 * scale),
            (width, base_y - 140 * scale),
            (width, height)
        ]
        draw.polygon(points, fill=color)

    # Draw soft, light flowers scattered gently
    flower_colors = [
        (255, 230, 235),  # Soft pink
        (255, 245, 230),  # Soft peach
        (250, 250, 240),  # Soft cream
        (245, 235, 255),  # Soft lavender
        (230, 245, 250),  # Soft blue
        (255, 255, 255),  # White
    ]
    # Fewer, softer flowers
    for _ in range(40):
        x = random.randint(50 * scale, width - 50 * scale)
        y = random.randint(height - 150 * scale, height - 30 * scale)
        flower_size = random.randint(6, 14) * scale // 2
        color = random.choice(flower_colors)

        # Draw soft flower petals
        for i in range(5):
            angle = i * 72
            rad = math.radians(angle)
            petal_x = x + math.cos(rad) * flower_size * 0.7
            petal_y = y + math.sin(rad) * flower_size * 0.7
            draw.ellipse([petal_x - flower_size//2, petal_y - flower_size//2,
                         petal_x + flower_size//2, petal_y + flower_size//2],
                        fill=color)

        # Soft center
        draw.ellipse([x - flower_size//4, y - flower_size//4,
                     x + flower_size//4, y + flower_size//4],
                    fill=(255, 255, 250))


def draw_night_theme(draw, width, height, scale):
    """Draw night theme with stars, moon, and cherry blossom tree."""
    # Draw gradient background (darker at top, lighter at bottom)
    for y in range(0, height, 2):
        r = int(20 + 30 * (y / height))
        g = int(10 + 5 * (y / height))
        b = int(40 + 10 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        if y + 1 < height:
            draw.line([(0, y+1), (width, y+1)], fill=(r, g, b))

    # Draw stars
    for _ in range(300):
        x = random.randint(0, width)
        y = random.randint(0, height//2)
        size = random.randint(1, 4) * scale // 2
        brightness = random.randint(200, 255)
        draw.ellipse([x, y, x+size, y+size], fill=(brightness, brightness, brightness))

    # Draw crescent moon
    moon_center = (width - 200 * scale, 150 * scale)
    moon_radius = 60 * scale
    draw.ellipse([moon_center[0]-moon_radius, moon_center[1]-moon_radius,
                  moon_center[0]+moon_radius, moon_center[1]+moon_radius],
                 fill=(255, 240, 200), outline=None)

    # Draw cherry blossom tree
    tree_shift = 100 * scale
    trunk_bottom = (width//2 - tree_shift, height - 50 * scale)
    trunk_top = (width//2 - tree_shift, height//2)
    branch_length = 200 * scale

    def draw_branch(start, length, angle, width):
        if length < 5:
            return

        width = max(1, int(width))
        rad = math.radians(angle)
        end = (int(start[0] + math.cos(rad) * length),
               int(start[1] - math.sin(rad) * length))
        start = (int(start[0]), int(start[1]))

        draw.line([start, end], fill=(70, 35, 20), width=width)

        if length > 20:
            draw_branch(end, length * 0.7, angle + 25, width * 0.7)
            draw_branch(end, length * 0.7, angle - 25, width * 0.7)

            if random.random() > 0.3:
                draw_branch(end, length * 0.5, angle + 10, width * 0.6)
            if random.random() > 0.3:
                draw_branch(end, length * 0.5, angle - 10, width * 0.6)

        if length < 30:
            for _ in range(int(5 - length/10)):
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-5, 5)
                blossom_size = random.randint(5, 10)
                blossom_pos = (end[0] + offset_x, end[1] + offset_y)

                draw.ellipse([blossom_pos[0]-blossom_size//2, blossom_pos[1]-blossom_size//2,
                              blossom_pos[0]+blossom_size//2, blossom_pos[1]+blossom_size//2],
                             fill=(255, 200, 220), outline=(255, 230, 240))

    draw_branch(trunk_top, 100, 90, 15)

    # Add falling petals
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(3, 8) * scale // 2
        opacity = random.randint(100, 200)
        petal_color = (255, 200, 220, opacity)

        petal = Image.new('RGBA', (size*2, size*2), (0, 0, 0, 0))
        petal_draw = ImageDraw.Draw(petal)
        petal_draw.ellipse([0, 0, size*2, size*2], fill=petal_color)
        petal = petal.rotate(random.randint(0, 360), expand=1)


def create_lyric_image(lyrics_file, output_path, artist_credit=""):
    """Create a lyric image with appropriate theme based on lyrics content."""
    # Read lyrics to detect theme
    title, verses, credits = read_lyrics_from_md(lyrics_file)
    lyrics_flat = [title] + [line for verse in verses for line in verse]
    theme = detect_theme(lyrics_flat)
    
    print(f"Detected theme: {theme}")
    
    # Create a high resolution image (2x scale for better quality)
    scale = 2
    width, height = 1600 * scale, 900 * scale
    
    # Set base color based on theme
    if theme == "night":
        base_color = (20, 10, 40)
    else:
        base_color = (135, 206, 235)
    
    image = Image.new('RGB', (width, height), base_color)
    draw = ImageDraw.Draw(image)

    # Draw appropriate theme
    if theme == "night":
        draw_night_theme(draw, width, height, scale)
    else:
        draw_sunny_theme(draw, width, height, scale)

    # Add stronger blur for soft, elegant background effect
    image = image.filter(ImageFilter.GaussianBlur(radius=scale * 4))

    # Recreate the draw object after filtering
    draw = ImageDraw.Draw(image)

    # Add the lyrics to the image
    add_lyrics(draw, width, height, lyrics_file, artist_credit)

    # Save the image with high DPI
    image.save(output_path, dpi=(300, 300), quality=95, optimize=True)
    print(f"High resolution image saved as {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate lyric images with themed backgrounds')
    parser.add_argument('--input', '-i', required=True, help='Path to the lyrics markdown file')
    parser.add_argument('--output', '-o', help='Path for the output image (default: input_lyric_image.png)')
    parser.add_argument('--artist', '-a', default='', help='Artist credit to display (e.g., "词曲：张志远")')
    
    args = parser.parse_args()
    
    # Set default output path if not provided
    if not args.output:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}_lyric_image.png"
    
    # Create the lyric image
    create_lyric_image(args.input, args.output, args.artist)


if __name__ == "__main__":
    main()
