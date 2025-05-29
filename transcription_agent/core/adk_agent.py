"""
Google ADK Agent wrapper for transcription
"""
import os
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

from .engine import TranscriptionEngine

load_dotenv()


async def transcribe_video_tool(video_path: str, groq_api_key: str) -> Dict[str, Any]:
    """Tool function for ADK agent - no default parameters allowed"""
    engine = TranscriptionEngine(groq_api_key)
    return await engine.transcribe_video(video_path, sentence_level=True)


# Create ADK Agent
transcription_agent = Agent(
    name="transcription_agent",
    model="gemini-2.0-flash",
    description="Transcription agent that converts video files to text with sentence-level timestamps",
    instruction=(
        "You are a transcription agent that processes video files using Groq Whisper API. "
        "Use the 'transcribe_video_tool' function to convert videos to text with precise timestamps. "
        "Always provide detailed progress updates and handle errors gracefully."
    ),
    tools=[transcribe_video_tool],
)

# Session management
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
    """Run the ADK transcription agent"""
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
