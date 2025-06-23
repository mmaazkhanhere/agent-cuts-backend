from dotenv import load_dotenv

from google.adk.agents import Agent,LlmAgent

from .prompt import SEGMENTATION_AGENT_PROMPT
from .type import SegmentationAgentOutput
from agent_cuts.sub_agents.transcription_agent.types import TranscriptAgentOutput
from google.adk.models.lite_llm import LiteLlm

load_dotenv()

segmentation_agent = LlmAgent(
    name="segmentation_agent",
    model="gemini-2.0-flash",
    description="Segmentation agent that segments transcript into topics",
    instruction=SEGMENTATION_AGENT_PROMPT,
    output_key="segmentation_output",
)