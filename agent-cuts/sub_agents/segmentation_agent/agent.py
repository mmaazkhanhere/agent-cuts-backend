import os
from dotenv import load_dotenv

from google.adk.agents import Agent

from .prompt import SEGMENTATION_AGENT_PROMPT
from .type import SegmentationAgentOutput

load_dotenv()

segmentation_agent = Agent(
    name="segmentation_agent",
    model="gemini-2.0-flash",
    description="Segmentation agent that segments transcript into topics",
    instruction=SEGMENTATION_AGENT_PROMPT,
    output_schema=SegmentationAgentOutput
)