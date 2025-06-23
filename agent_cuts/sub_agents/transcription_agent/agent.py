from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm
import os

from google.adk.agents import Agent

from .prompt import AUDIO_TRANSCRIPTION_PROMPT
from .tools.transcribe_video_tool import transcribe_video_tool

load_dotenv()



transcription_agent = Agent(
    name="transcription_agent",
    model=LiteLlm(model="groq/deepseek-r1-distill-llama-70b"),
    description="Audio transcription agent that converts audio files to text with sentence-level timestamps",
    instruction=AUDIO_TRANSCRIPTION_PROMPT,
    tools=[transcribe_video_tool],
    output_key="transcription_output"
)

