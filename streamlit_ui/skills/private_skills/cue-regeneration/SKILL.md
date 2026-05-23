---
name: cue-regeneration
description: Regenerate CUE files with proper UTF-8 encoding for Chinese audio files. Fixes encoding issues in existing CUE files by reading track names from a reference tracklist and preserving timing information.
category: audio
tags:
  - cue
  - audio
  - encoding
  - chinese
  - metadata
  - flac
aliases:
  - regenerate-cue
  - fix-cue-encoding
  - cue-utf8
argument_hint: "[tracklist_file]"
user_invocable: true
auto_trigger: false
---

# CUE File Regeneration

## Overview
This skill regenerates CUE files with proper UTF-8 encoding for Chinese audio files. It fixes encoding issues in existing CUE files by reading track names from a reference tracklist file while preserving the original timing information (INDEX 00/01).

## Features
- Fixes UTF-8 encoding issues in CUE files
- Preserves original timing information (INDEX 00/01)
- Reads track names from reference tracklist
- Supports Chinese characters in track titles
- Maintains proper CUE file structure
- Automatic track numbering

## Requirements
- Python 3.8+
- No external dependencies (uses only standard library)

## Usage

### Execution Steps

To regenerate a CUE file from a tracklist:

**Step 1: Run the regeneration script**
```bash:execute
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python $SKILL_PATH/scripts/regenerate_cue.py
```

### Variable Substitution

- `$SKILL_PATH` - Path to the skill directory

### Input Format

The skill expects a `Tracklist.txt` file in the current working directory with the following format:
- One track per line
- Track names can optionally start with a number (e.g., "1欢迎进行曲" or "欢迎进行曲")
- UTF-8 encoding

Example:
```
1欢迎进行曲
2典礼序曲
3中华人民共和国国歌
4检阅号角
5中国人民解放军军歌
```

### How It Works

1. **Reads tracklist**: Parses `Tracklist.txt` to extract track names
2. **Preserves timing**: Uses hardcoded timing data from the original CUE file
3. **Generates CUE**: Creates a new CUE file with proper UTF-8 encoding
4. **Output**: Saves as `中国人民解放军军乐团 - 纪念中国人民抗日战争暨世界反法西斯战争胜利70周年阅兵曲.cue`

### Customization

To use this skill for different albums:

1. **Update track names**: Modify the `track_names` list in the script
2. **Update timings**: Modify the `timings` list with correct INDEX 00/01 values
3. **Update metadata**: Change PERFORMER, TITLE, and FILE references in the script
4. **Update output filename**: Change the `cue_filename` variable

### Timing Format

The timing data uses the format `MM:SS:FF` (minutes:seconds:frames):
- `INDEX 00`: Pre-gap start time (optional for first track)
- `INDEX 01`: Actual track start time

Example:
```python
timings = [
    (None, "00:00:00"),  # Track 1 - no pre-gap
    ("01:39:20", "01:44:20"),  # Track 2 - pre-gap at 1:39:20, start at 1:44:20
]
```

### Extracting Timings from Existing CUE

If you need to extract timings from an existing CUE file:

```bash
# Use ffprobe to get track durations
ffprobe -v quiet -print_format json -show_format -show_streams "audio.flac"
```

Or manually extract from the existing CUE file's INDEX lines.

## Output

The skill generates a CUE file with:
- Proper UTF-8 encoding for Chinese characters
- All 23 tracks with correct titles
- Preserved timing information
- Standard CUE file format (PERFORMER, TITLE, FILE, TRACK, INDEX)

## Notes

- The script is currently configured for a specific album
- To use for other albums, modify the hardcoded values in the script
- The output CUE file should be placed in the same directory as the audio file
- Ensure the FILE reference in the CUE matches your actual audio filename
- CD audio uses 75 frames per second for the FF value in timing

## Examples

**Basic usage (with default configuration):**
```bash
cd /path/to/cue/directory
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw && python "$SKILL_PATH/scripts/regenerate_cue.py"
```

**For a different album:**
1. Copy the script and modify the hardcoded values
2. Update track_names, timings, metadata, and output filename
3. Run the modified script
