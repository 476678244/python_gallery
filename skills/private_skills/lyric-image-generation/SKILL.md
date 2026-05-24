---
name: lyric-image-generation
description: Generate elegant lyric images with soft pastel backgrounds that complement the lyrics. Features automatic metadata extraction, three-column dispersed layout, and dreamy blurred backgrounds.
category: creative
tags:
  - lyrics
  - image-generation
  - music
  - creative
  - visualization
  - art
  - design
  - pastel
  - elegant
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
This skill generates elegant lyric images with soft, dreamy pastel backgrounds that beautifully complement the lyrics without overpowering them. It automatically extracts song metadata (lyricists, composers, producers) and displays them separately at the bottom, while the lyrics are presented in a clean, dispersed three-column layout with adaptive height to ensure perfect visual harmony.

## Features
- **Elegant Pastel Backgrounds**: Soft cream-to-blue gradients with dreamy blur effects that complement lyrics
- **Automatic Metadata Extraction**: Intelligently separates song credits (作词, 作曲, 编曲, 制作, etc.) from lyrics
- **Separated Credits Display**: Metadata shown in a single elegant line at the bottom, completely separate from lyrics
- **Adaptive Layout**: Lyrics area height automatically adjusts based on font size to avoid overlapping with credits
- **Dispersed Typography**: Smaller fonts with increased line spacing for elegant, breathable layout
- **Three-Column Layout**: Evenly distributed lyrics across three columns for optimal readability
- **High-Resolution Output**: 3200x1800 pixels at 300 DPI, perfect for printing or sharing
- **Chinese & English Support**: Automatic font detection with excellent Chinese text rendering

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

### Visual Design

The skill creates a sophisticated, minimalist aesthetic:

- **Soft Pastel Palette**: Cream (#FAF8F5) to pale blue gradient background
- **Dreamy Blur Effect**: Strong Gaussian blur (8px) creates an elegant, ethereal atmosphere
- **Subtle Sun Glow**: Soft, diffused light source in the corner (not harsh bright sun)
- **Light Mountain Silhouettes**: Near-transparent gray layers that blend into the background
- **Delicate Floral Accents**: 40 soft pastel flowers (pink, peach, cream, lavender) scattered gently
- **No Harsh Elements**: No bold colors, no strong contrasts, no distracting visual noise

### Metadata Recognition

The skill automatically identifies and extracts these credit types:
- **作词** (Lyricist), **作曲** (Composer), **编曲** (Arranger)
- **制作** (Production), **监制** (Executive Producer)
- **录音** (Recording), **混音** (Mixing), **母带** (Mastering)
- **出品** (Produced by), **发行** (Distributed by)

### Input Format

The lyrics file should be a markdown file with the following format:
- **First line**: Song title
- **Following lines**: Lyrics verses (verses can be separated by empty lines)
- **Metadata lines**: Automatically detected and extracted (lines containing 作词, 作曲, etc.)

The skill intelligently separates actual lyrics from production credits.

### Customization Options

You can customize the image by modifying the script parameters:
- **Font sizes**: `font_size` (default: 24px), `title_font_size` (default: 32px)
- **Line spacing**: Adjust `line_height` padding (default: font height + 35px)
- **Background blur**: Modify `GaussianBlur(radius)` (default: 8px for dreamy effect)
- **Credits position**: Adjust `bottom_reserve` and `credit_y` variables
- **Colors**: Modify color tuples in the theme sections (default: soft pastels)

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

The skill generates a high-resolution PNG image (3200x1800 pixels at 300 DPI) featuring:

- **Elegant Pastel Background**: Soft, blurred, dreamy atmosphere that frames the lyrics
- **Dispersed Three-Column Lyrics**: Smaller fonts with generous spacing for visual elegance
- **Separated Credits Line**: Metadata displayed in one refined line at the bottom
- **Black Text with White Outline**: Ensures excellent readability against the soft background
- **Professional Quality**: 300 DPI, optimized for both digital sharing and printing

## Notes
- **Font Detection**: Automatically finds the best Chinese font (PingFang, STHeiti, SimHei, Microsoft YaHei)
- **Smart Layout**: Lyrics area height is calculated dynamically based on font metrics to prevent overlap with credits
- **Quality Optimization**: Output saved at 95% quality with optimization enabled
- **Theme Detection**: Automatically selects visual theme based on lyrics keywords (nature, sunny, flowers, night)
- **Background Philosophy**: Designed to complement, not compete with, the lyrics content
