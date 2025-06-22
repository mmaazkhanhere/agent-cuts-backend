import os
from dotenv import load_dotenv

from google.adk.agents import Agent

from .prompt import COPYWRITER_AGENT_PROMPT
from .types import CopyWriteInput, CopywriterAgentOutput

load_dotenv()

copywrite_agent = Agent(
    name="copywriter_agent",
    model="gemini-2.5-flash",
    description="An agent that generates title, short description, and tags for a given segment",
    input_schema=CopyWriteInput,
    instruction=COPYWRITER_AGENT_PROMPT,
    output_key="copywriter_output",
    output_schema=CopywriterAgentOutput
)