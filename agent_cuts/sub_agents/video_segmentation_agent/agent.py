import os
from dotenv import load_dotenv
from moviepy import VideoFileClip

from google.adk.agents import Agent

from .prompt import VIDEO_SEGMENTATION_AGENT_PROMPT
from .utils import add_audio_to_segments

load_dotenv()

def video_segmentation_tool(json_data, output_dir="segments"):
    """
    Agent tool that splits video into segments based on JSON data containing start/end times
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


video_segmentation_agent = Agent(
    name="video_segmentation_agent",
    model="gemini-2.0-flash",
    description="Video segmentation agent that segments video based on start and endtime specified in the json input",
    instruction=VIDEO_SEGMENTATION_AGENT_PROMPT,
    tools=[video_segmentation_tool],
)

