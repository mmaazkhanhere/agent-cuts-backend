from pydantic import BaseModel, Field
from typing import List

from agent_cuts.sub_agents.ranking_agent.types import RankingAgentOutput

class CopyWriteInput(BaseModel):
    segments: List[RankingAgentOutput] = Field(description="List of segments to be copied")


class Metrics(BaseModel):
    clarity_score: int = Field(description="Clarity score of the segment out of 10")
    engagement_score: int = Field(description="Engagement score of the segment out of 10")
    trending_score: int = Field(description="Trending score of the segment out of 10")
    overall_score: float = Field(description="Overall score of the segment out of 10")

class CopyWriteOutput(BaseModel):
    title: str = Field(description="Title of the video segment")
    description: str = Field(description="Short description of the video segment")
    tags: List[str] = Field(description="List of tags for the video segment")
    metrics: Metrics = Field(description="Metrics of the video segment")


class CopywriterAgentOutput(BaseModel):
    video_segments: List[CopyWriteOutput] = Field(description="Output of the copywriter agent")