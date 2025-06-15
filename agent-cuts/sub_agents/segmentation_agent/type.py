from pydantic import BaseModel, Field

class SegmentationOutput(BaseModel):
    topic: str = Field(description="Topic of the segment")
    transcript: str = Field(description="Transcript of the segment")
    start_time: str = Field(description="Start time of the segment")
    end_time: str = Field(description="End time of the segment")

class SegmentationAgentOutput(BaseModel):
    segments: list[SegmentationOutput] = Field(description="List of segments")