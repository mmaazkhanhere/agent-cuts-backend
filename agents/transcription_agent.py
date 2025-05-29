"""
Clean transcription agent following proper ADK patterns
"""
import os
import asyncio
from typing import List, Dict, Any
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

# Import utilities
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.audio_processing import AudioProcessor, AudioChunk
from utils.groq_client import GroqTranscriptionClient, TranscriptionResult
from utils.sentence_processor import create_sentence_level_transcription

load_dotenv()

# Get the Groq API key from environment variables
groq_api_key = os.getenv("GROQ_API_KEY")


async def transcribe_video_file(video_path: str) -> Dict[str, Any]:
    """Main transcription function - this is the tool the agent uses"""
    try:
        print(f"Starting transcription of: {video_path}")
        
        # Initialize processors
        audio_processor = AudioProcessor()
        groq_client = GroqTranscriptionClient(groq_api_key)
        
        # Step 1: Extract audio
        print("Extracting audio...")
        audio_path = audio_processor.extract_audio_from_video(video_path)
        
        # Step 2: Chunk audio
        print("Chunking audio...")
        chunks = audio_processor.chunk_audio_intelligently(audio_path)
        print(f"Created {len(chunks)} chunks")
        
        # Step 3: Transcribe chunks in parallel
        print("Starting transcription...")
        tasks = []
        for chunk in chunks:
            task = groq_client.transcribe_audio_file(
                chunk.file_path, chunk.chunk_id, chunk.start_time, chunk.end_time
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Step 4: Aggregate results
        transcription_output = _aggregate_results(results)
        
        # Step 5: Create sentence-level breakdown
        print("Creating sentence-level timestamps...")
        transcription_output = create_sentence_level_transcription(transcription_output)
        
        # Step 6: Cleanup
        temp_files = [audio_path] + [chunk.file_path for chunk in chunks]
        audio_processor.cleanup_temp_files(temp_files)
        
        print("Transcription completed!")
        return transcription_output
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Transcription failed: {str(e)}",
            "full_text": "",
            "segments": []
        }


def _aggregate_results(results: List[TranscriptionResult]) -> Dict[str, Any]:
    """Aggregate transcription results"""
    valid_results = [r for r in results if isinstance(r, TranscriptionResult) and not r.text.startswith("[ERROR")]
    valid_results.sort(key=lambda x: x.chunk_id)
    
    # Combine text
    full_text = " ".join([r.text for r in valid_results])
    
    # Create segments
    segments = []
    for result in valid_results:
        segments.append({
            "chunk_id": result.chunk_id,
            "text": result.text,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "confidence": result.confidence
        })
    
    # Calculate metrics
    avg_confidence = sum([r.confidence for r in valid_results]) / len(valid_results) if valid_results else 0.0
    
    return {
        "status": "success",
        "full_text": full_text,
        "segments": segments,
        "metadata": {
            "total_chunks": len(results),
            "successful_chunks": len(valid_results),
            "avg_confidence": avg_confidence,
            "total_words": len(full_text.split()) if full_text else 0
        }
    }


# Create the ADK Agent
transcription_agent = Agent(
    name="transcription_agent",
    model="gemini-2.0-flash",
    description="A transcription agent that converts video files to text using Groq Whisper API.",
    instruction=(
        "You are a transcription agent that processes video files. "
        "Use the 'transcribe_video_file' tool to convert video content to text. "
        "Always provide the video file path and handle errors gracefully."
    ),
    tools=[transcribe_video_file],
)

# Initialize session service and runner
session_service = InMemorySessionService()
APP_NAME = "transcription_app"
USER_ID = "default_user"  
SESSION_ID = "default_session"

runner = Runner(
    agent=transcription_agent,
    app_name=APP_NAME,
    session_service=session_service
)


async def run_transcription_agent(video_path: str) -> str:
    """Run the transcription agent with a video file"""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return "Error: GROQ_API_KEY not found in environment variables"
    
    prompt = f"Please transcribe the video file at path: {video_path}"
    
    new_message_content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )

    final_response = "No response received."
    try:
        # Ensure session exists
        if not await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID):
            await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

        for event in runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=new_message_content
        ):
            if event.is_final_response():
                for part in event.content.parts:
                    if part.text:
                        final_response = part.text
                        break
                break
    except Exception as e:
        print(f"Error during agent run: {e}")
        final_response = f"An error occurred: {e}"

    return final_response
