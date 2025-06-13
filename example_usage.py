"""
Example usage of the main video processing pipeline
"""

import asyncio
import logging
from main_agent import run_video_processor

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def process_example_video():
    """Example function showing how to use the video processor"""
    
    # Replace with your actual video path
    video_path = "./video/test.mp4"
    output_dir = "./output"
    
    print("Starting video processing pipeline...")
    print(f"Video: {video_path}")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    try:
        # Run the complete pipeline
        result = await run_video_processor(video_path, output_dir)
        
        print("\nProcessing complete!")
        print(result)
        
    except Exception as e:
        print(f"\nError: {e}")
        logging.error("Failed to process video", exc_info=True)


if __name__ == "__main__":
    # Make sure you have these environment variables set:
    # - GOOGLE_API_KEY
    # - GROQ_API_KEY
    
    asyncio.run(process_example_video())
