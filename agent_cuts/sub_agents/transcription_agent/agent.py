from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .prompt import AUDIO_TRANSCRIPTION_PROMPT
from .tools.transcribe_video_tool import transcribe_video_tool

load_dotenv()



transcription_agent = Agent(
    name="transcription_agent",
    model=LiteLlm("groq/qwen-qwq-32b"),
    description="Audio transcription agent that converts audio files to text with sentence-level timestamps",
    instruction=AUDIO_TRANSCRIPTION_PROMPT,
    tools=[transcribe_video_tool],
    output_key="transcription_output"
)

# formatter_agent = Agent(
#     name="formatter",
#     model="gemini-2.0-flash",
#     description="Formatter agent that formats the output of an agent into a given format",
#     instruction=TRANSCRIPTION_FORMATTER_PROMPT,
#     output_schema=TranscriptAgentOutput,
#     output_key="transcript",
#     disallow_transfer_to_parent=True,
#     disallow_transfer_to_peers=True
# )