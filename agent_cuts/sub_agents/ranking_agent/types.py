from pydantic import BaseModel, Field

class SegmentSchema(BaseModel):
    topic: str = Field(description="Topic of the segment")
    transcript: str = Field(description="Transcript of the segment")
    start_time: str = Field(description="Start time of the segment")
    end_time: str = Field(description="End time of the segment")

class RankingOutput(BaseModel):
    segment: SegmentSchema = Field(description="Segment of the video")
    clarity_score: int = Field(description="Clarity score of the segment out of 10")
    engagement_score: int = Field(description="Engagement score of the segment out of 10")
    trending_score: int = Field(description="Trending score of the segment out of 10")
    overall_score: float = Field(description="Overall score of the segment out of 10")

class RankingAgentOutput(BaseModel):
    ranked_list: list[RankingOutput] = Field(description="List of segments ranked based on overall score")