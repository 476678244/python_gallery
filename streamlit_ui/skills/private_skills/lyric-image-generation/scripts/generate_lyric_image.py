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
    """Read lyrics from markdown file and extract title and verses."""
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
    """Add lyrics to the image with three-column layout."""
    # Calculate scale factor (assuming 2x scale for high DPI)
    scale = 2 if width > 2000 else 1
    
    # Read lyrics from the markdown file
    try:
        title, verses = read_lyrics_from_md(lyrics_file)

        # Prepare lyrics for display (flatten verses and add some spacing)
        lyrics = [title, "", artist_credit, ""] if artist_credit else [title, ""]

        # Add verses with spacing in between
        for verse in verses:
            lyrics.extend(verse)
            lyrics.append("")  # Add empty line after each verse
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
    font_size = 32 * scale  # Larger font
    title_font_size = 40 * scale  # Larger for title/artist
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
    line_height = bbox[3] - bbox[1] + 20  # Increased spacing
    top_margin = height // 8  # Start even higher up
    max_lines_per_column = (height - top_margin * 2) // line_height

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


def draw_sunny_theme(draw, width, height, scale):
    """Draw sunny day theme with sun, mountains, river, and flowers."""
    # Draw gradient background (sunny sky - light blue to warm yellow)
    for y in range(0, height, 2):
        progress = y / height
        r = int(135 + 100 * progress)
        g = int(206 + 30 * progress)
        b = int(235 - 80 * progress)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        if y + 1 < height:
            draw.line([(0, y+1), (width, y+1)], fill=(r, g, b))

    # Draw bright sun (positioned higher to avoid overlapping lyrics)
    sun_center = (width - 200 * scale, 120 * scale)
    sun_radius = 60 * scale
    draw.ellipse([sun_center[0]-sun_radius, sun_center[1]-sun_radius,
                  sun_center[0]+sun_radius, sun_center[1]+sun_radius],
                 fill=(255, 255, 200), outline=(255, 220, 100), width=3*scale)

    # Draw sun rays
    for i in range(12):
        angle = i * 30
        rad = math.radians(angle)
        ray_length = 30 * scale
        start_x = sun_center[0] + math.cos(rad) * (sun_radius + 10)
        start_y = sun_center[1] + math.sin(rad) * (sun_radius + 10)
        end_x = sun_center[0] + math.cos(rad) * (sun_radius + ray_length)
        end_y = sun_center[1] + math.sin(rad) * (sun_radius + ray_length)
        draw.line([(start_x, start_y), (end_x, end_y)], fill=(255, 220, 100), width=4*scale)

    # Draw mountains in the background
    mountain_colors = [(100, 120, 150), (80, 100, 130), (60, 80, 110)]
    for i, color in enumerate(mountain_colors):
        base_y = height - 150 * scale + i * 30 * scale
        points = [
            (0, height),
            (width * 0.2, base_y - 200 * scale),
            (width * 0.4, base_y - 150 * scale),
            (width * 0.6, base_y - 220 * scale),
            (width * 0.8, base_y - 180 * scale),
            (width, base_y - 160 * scale),
            (width, height)
        ]
        draw.polygon(points, fill=color)

    # Draw river flowing through the landscape
    river_path = []
    for x in range(0, width + 1, 20 * scale):
        y = height - 100 * scale + math.sin(x / (200 * scale)) * 30 * scale
        river_path.append((x, y))
    river_path.append((width, height))
    river_path.append((0, height))
    draw.polygon(river_path, fill=(100, 180, 220))

    # Draw colorful flowers on the ground
    flower_colors = [
        (255, 100, 100),  # Red
        (255, 200, 100),  # Orange
        (255, 255, 100),  # Yellow
        (255, 150, 200),  # Pink
        (200, 100, 255),  # Purple
        (100, 200, 255),  # Light blue
    ]
    for _ in range(80):
        x = random.randint(50 * scale, width - 50 * scale)
        y = random.randint(height - 200 * scale, height - 50 * scale)
        flower_size = random.randint(8, 20) * scale // 2
        color = random.choice(flower_colors)

        # Draw flower petals
        for i in range(5):
            angle = i * 72
            rad = math.radians(angle)
            petal_x = x + math.cos(rad) * flower_size
            petal_y = y + math.sin(rad) * flower_size
            draw.ellipse([petal_x - flower_size//2, petal_y - flower_size//2,
                         petal_x + flower_size//2, petal_y + flower_size//2],
                        fill=color)

        # Draw flower center
        draw.ellipse([x - flower_size//3, y - flower_size//3,
                     x + flower_size//3, y + flower_size//3],
                    fill=(255, 255, 200))


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
    title, verses = read_lyrics_from_md(lyrics_file)
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

    # Add some blur to create depth
    image = image.filter(ImageFilter.GaussianBlur(radius=scale * 0.7))

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
