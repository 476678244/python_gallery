#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate CUE file with proper Chinese encoding"""

def regenerate_cue():
    # Read tracklist
    with open('Tracklist.txt', 'r', encoding='utf-8') as f:
        tracks = [line.strip() for line in f if line.strip()]
    
    # Parse track names (remove leading numbers)
    track_names = []
    for track in tracks:
        # Remove leading number (e.g., "1欢迎进行曲" -> "欢迎进行曲")
        name = track.lstrip('0123456789')
        track_names.append(name)
    
    # Timing data from existing CUE (preserved)
    # Format: (index_00, index_01) - index_00 can be None for first track
    timings = [
        (None, "00:00:00"),  # Track 1
        ("01:39:20", "01:44:20"),  # Track 2
        ("03:57:22", "04:02:22"),  # Track 3
        ("04:53:06", "04:58:06"),  # Track 4
        ("05:36:04", "05:41:04"),  # Track 5
        ("06:51:28", "06:56:28"),  # Track 6
        ("07:58:11", "08:03:11"),  # Track 7
        ("09:47:68", "09:52:68"),  # Track 8
        ("11:45:10", "11:50:10"),  # Track 9
        ("14:13:03", "14:18:03"),  # Track 10
        ("17:46:65", "17:51:65"),  # Track 11
        ("20:07:38", "20:12:38"),  # Track 12
        ("22:39:65", "22:44:65"),  # Track 13
        ("24:06:29", "24:11:29"),  # Track 14
        ("26:45:52", "26:50:52"),  # Track 15
        ("29:44:69", "29:49:69"),  # Track 16
        ("31:29:61", "31:34:61"),  # Track 17
        ("34:48:19", "34:53:19"),  # Track 18
        ("36:10:22", "36:15:22"),  # Track 19
        ("38:08:18", "38:13:18"),  # Track 20
        ("41:44:59", "41:49:59"),  # Track 21
        ("43:58:12", "44:03:12"),  # Track 22
        ("46:10:60", "46:15:60"),  # Track 23
    ]
    
    # Generate CUE content
    cue_lines = [
        'REM DATE 2015',
        'REM DISCID 310B2A17',
        'REM COMMENT "ExactAudioCopy v1.2"',
        'PERFORMER "中国人民解放军军乐团"',
        'TITLE "纪念中国人民抗日战争暨世界反法西斯战争胜利70周年阅兵曲"',
        'REM COMPOSER ""',
        'FILE "中国人民解放军军乐团 - 纪念中国人民抗日战争暨世界反法西斯战争胜利70周年阅兵曲.flac" WAVE',
    ]
    
    for i, (name, (index_00, index_01)) in enumerate(zip(track_names, timings), 1):
        cue_lines.append(f'  TRACK {i:02d} AUDIO')
        cue_lines.append(f'    TITLE "{name}"')
        cue_lines.append(f'    PERFORMER "中国人民解放军军乐团"')
        cue_lines.append('    REM COMPOSER ""')
        
        if index_00:
            cue_lines.append(f'    INDEX 00 {index_00}')
        cue_lines.append(f'    INDEX 01 {index_01}')
    
    # Write CUE file with UTF-8 encoding
    cue_filename = '中国人民解放军军乐团 - 纪念中国人民抗日战争暨世界反法西斯战争胜利70周年阅兵曲.cue'
    with open(cue_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cue_lines) + '\n')
    
    print(f"Generated CUE file: {cue_filename}")
    print(f"Total tracks: {len(track_names)}")

if __name__ == '__main__':
    regenerate_cue()
