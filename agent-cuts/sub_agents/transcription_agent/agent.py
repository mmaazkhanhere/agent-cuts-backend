import os

from .prompt import TRANSCRIPTION_AGENT_PROMPT

from typing import Dict, Any
from dotenv import load_dotenv

from google.adk.agents import Agent

load_dotenv()

async def transcribe_video_tool(video_path: str) -> Dict[str, Any]:
    """Tool function for ADK agent - returns simplified transcript"""
    print(f"[*] Tool called with video_path: {video_path}")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return {"error": "GROQ_API_KEY not found in environment variables"}
    
    #engine = TranscriptionEngine(groq_api_key)
    # Get full transcription result
    #full_result = await engine.transcribe_video(video_path, sentence_level=True)
    
    # Simplify the output
    #simplified = create_simplified_transcript(full_result)
    
    #print(f"[+] Tool returning: {simplified.get('status', 'unknown')} with {len(simplified.get('segments', []))} segments")
    #return simplified


transcription_agent = Agent(
    name="transcription_agent",
    model="gemini-2.0-flash",
    description="Transcription agent that converts video files to text with sentence-level timestamps",
    instruction=TRANSCRIPTION_AGENT_PROMPT,
    tools=[transcribe_video_tool],
    output_key="transcription_output"
)