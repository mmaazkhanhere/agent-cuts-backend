import os
import subprocess
import subprocess
from typing import Dict, Any

import subprocess
import os

def add_audio_to_segments(original_video: str, segment_details: list[Dict[str, Any]]) -> None:
    """Adds properly aligned audio to segments using FFmpeg"""
    for segment in segment_details:
        input_path = segment["output_path"]
        start = segment["start_time"]
        end = segment["end_time"]
        
        # Create temp output path
        base, ext = os.path.splitext(input_path)
        temp_output = f"{base}_with_audio{ext}"
        
        # Build FFmpeg command to:
        # 1. Extract exact audio segment from original video
        # 2. Merge with video segment
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start),  # Start time for audio extraction
            "-to", str(end),    # End time for audio extraction
            "-i", original_video,
            "-i", input_path,
            "-c:v", "copy",     # Copy video stream
            "-c:a", "aac",       # Encode audio to AAC for compatibility
            "-map", "0:a",       # Use audio from first input
            "-map", "1:v",       # Use video from second input
            "-shortest",
            temp_output
        ]
        
        try:
            # Run FFmpeg command
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Replace original segment with new version
            os.replace(temp_output, input_path)
            print(f"Added audio to: {os.path.basename(input_path)}")
        except Exception as e:
            print(f"Error adding audio to segment: {str(e)}")
            # Remove temp file if exists
            if os.path.exists(temp_output):
                os.remove(temp_output)