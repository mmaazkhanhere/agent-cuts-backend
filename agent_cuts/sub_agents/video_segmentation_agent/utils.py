import os
import subprocess

def add_audio_to_segments(original_video, segments_dir):
    """Adds audio to segments using FFmpeg to work around MoviePy issues"""
    temp_dir = os.path.join(segments_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Process each segment
    for filename in os.listdir(segments_dir):
        if filename.endswith(".mp4") and filename.startswith("seg_"):
            input_path = os.path.join(segments_dir, filename)
            output_path = os.path.join(temp_dir, filename)
            
            # Extract audio from original video
            cmd = [
                "ffmpeg",
                "-y",
                "-i", original_video,
                "-i", input_path,
                "-c", "copy",  # Stream copy (no re-encoding)
                "-map", "0:a",  # Use audio from first input
                "-map", "1:v",  # Use video from second input
                "-shortest",
                output_path
            ]
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # Replace original with audio version
                os.replace(output_path, input_path)
                print(f"Added audio to: {filename}")
            except Exception as e:
                print(f"Error adding audio to {filename}: {str(e)}")
    
    # Clean up temp directory
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass