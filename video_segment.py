import os
import json
import subprocess
from moviepy import VideoFileClip

def split_video_segments(json_data, output_dir="segments"):
    """
    Splits a video into segments based on JSON data containing start/end times.
    Includes Windows audio processing fix.
    """
    os.makedirs(output_dir, exist_ok=True)
    video_path = json_data["video_path"]
    
    # Use absolute path to avoid permission issues
    if not os.path.isabs(video_path):
        video_path = os.path.abspath(video_path)
    
    # Load video without audio first to avoid processing issues
    video = VideoFileClip(video_path, audio=False)
    
    segments = json_data["ranked_segments"]["ranked_list"]
    for i, segment in enumerate(segments):
        start = float(segment["start_time"])
        end = float(segment["end_time"])
        
        # Handle segments that might exceed video duration
        if end > video.duration:
            end = video.duration
        if start > video.duration:
            print(f"Skipping segment {i+1} (starts after video ends)")
            continue
            
        clip = video.subclipped(start, end)
        
        topic = segment["topic"].replace(" ", "_").replace("/", "-")[:30]
        output_path = os.path.join(output_dir, f"seg_{i+1:02d}_{topic}.mp4")
        
        # Write without audio first (fixes the AttributeError)
        clip.write_videofile(
            output_path,
            codec="libx264",
            audio=False,  # Disable audio to avoid the error
            logger=None,
            threads=4  # Helps with processing speed
        )
        
        print(f"Created video segment: {output_path}")
        clip.close()
    
    video.close()
    
    # Now add audio separately using FFmpeg
    add_audio_to_segments(video_path, output_dir)

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

if __name__ == "__main__":
    with open(r"output\ranking_response.json", "r") as f:
        data = json.load(f)
    
    split_video_segments(data)