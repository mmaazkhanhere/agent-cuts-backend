from pydantic import BaseModel, Field

from agent_cuts.sub_agents.ranking_agent.types import RankingOutput

class VideoSegmenterAgentInput(BaseModel):
    ranked_list: list[RankingOutput] = Field(description="List of segments ranked based on overall score")
    video_path: str = Field(description="Path to the video file")

class VideoSegmenterAgentOutput(BaseModel):
    video_segments: list[str] = Field(description="List of video segments")