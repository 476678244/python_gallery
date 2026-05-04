---
name: lyric-image-generation
description: Generate beautiful lyric images with themed backgrounds based on song lyrics. Automatically analyzes lyrics to create matching visual themes (sunny, mountains, rivers, flowers, etc.) and displays lyrics in a clean three-column layout.
category: creative
tags:
  - lyrics
  - image-generation
  - music
  - creative
  - visualization
  - art
  - design
aliases:
  - generate-lyric-image
  - lyric-image
  - lyrics-to-image
  - song-image
  - create-lyric-art
argument_hint: "[lyrics_file]"
user_invocable: true
auto_trigger: false
---

# Lyric Image Generation

## Overview
This skill generates beautiful lyric images with themed backgrounds based on song lyrics content. It automatically analyzes the lyrics to create matching visual themes and displays the lyrics in a clean, readable format.

## Features
- Automatic theme detection based on lyrics content
- Three-column lyric layout for better readability
- High-resolution output (3200x1800 at 300 DPI)
- Support for Chinese and English lyrics
- Multiple visual themes (sunny, mountains, rivers, flowers, etc.)
- Customizable font sizes and spacing

## Requirements
- Python 3.8+
- Pillow (PIL) library

## Installation
```bash
pip install Pillow
```

## Usage

### Execution Steps

To generate a lyric image from a markdown file:

**Step 1: Generate the lyric image**
```bash:execute
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python $SKILL_PATH/scripts/generate_lyric_image.py --input $INPUT_FILE --output $OUTPUT_FILE
```

### Variable Substitution

- `$INPUT_FILE` - Path to the lyrics markdown file (provided as argument)
- `$OUTPUT_FILE` - Path for the output image (default: $INPUT_FILE_lyric_image.png)
- `$SKILL_PATH` - Path to the skill directory

### Input Format

The lyrics file should be a markdown file with the following format:
- First line: Song title
- Remaining lines: Lyrics (verses separated by empty lines)

Example:
```markdown
我们是祖国的花朵

阳光下尽情唱着歌
看我们幸福的生活
像花儿五彩的颜色

我们是祖国的花朵
请你要好好爱护我
像热爱山川的辽阔
和美丽的江河
```

### Supported Themes

The skill automatically detects themes based on keywords in the lyrics:

- **Sunny/Day**: Keywords like "阳光" (sunshine), "清晨" (morning), "阳光" (sun)
  - Bright sun with rays
  - Light blue to warm yellow gradient sky
  - Colorful flowers

- **Nature/Mountains**: Keywords like "山川" (mountains), "江河" (rivers)
  - Mountain silhouettes
  - Flowing river
  - Green landscape

- **Flowers**: Keywords like "花朵" (flowers), "花儿" (flowers)
  - Colorful flower petals
  - Pink/red/yellow/purple flowers
  - Garden scene

- **Night/Evening**: Keywords like "傍晚" (evening), "夜晚" (night)
  - Dark blue/purple gradient
  - Stars and moon
  - Cherry blossom tree

### Customization Options

You can customize the image by modifying the script parameters:
- Font size: Adjust `font_size` and `title_font_size` variables
- Line spacing: Adjust `line_height` padding
- Colors: Modify color tuples in the theme sections
- Layout: Adjust column width and gutter spacing

### Examples

**Basic usage:**
```bash
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python "$SKILL_PATH/scripts/generate_lyric_image.py" --input "/path/to/lyrics.md" --output "/path/to/output.png"
```

**With custom output path:**
```bash
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python "$SKILL_PATH/scripts/generate_lyric_image.py" --input "祖国的花朵.md" --output "祖国的花朵_art.png"
```

## Output

The skill generates a high-resolution PNG image (3200x1800 pixels at 300 DPI) with:
- Themed background matching the lyrics content
- Lyrics displayed in three columns
- Black text with white outline for readability
- Professional quality suitable for printing or sharing

## Notes
- The skill automatically detects the best font for Chinese text
- Output images are optimized for quality (95% quality, optimized)
- The three-column layout ensures lyrics are evenly distributed
- Text color and spacing are optimized for readability against the background
