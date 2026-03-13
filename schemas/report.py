from pydantic import BaseModel, Field
from typing import Literal

# --- Building blocks of tech assessment execution and deliverable ---

## Main pieces of deliverble

### many-to-one with 'Topic'
class QuestionResponse(BaseModel):
    question_id: str
    question_text: str
    answer: str = Field(description="Synthesized bullet-point answer from source docs")
    source_chunks: list[str] = Field(description="Verbatim excerpts used to form answer")

### one-to-one with 'Topic'
class Risk(BaseModel):
    description: str
    supporting_quote: str        # verbatim, with source label
    source_document: str

### many-to-one with 'Topic'
class Recommendation(BaseModel):
    title: str
    description: str
    timeline: Literal["Y1", "Y2", "Y3"]
    priority: Literal["Low", "Medium", "High"]
    cost_estimate: str           # e.g. "$5,000 - $10,000" or "TBD"
    cost_type: Literal["Labor", "Hardware", "Software", "One-Time", "Ongoing", "Mixed"]
    next_steps: list[str]
    benefits: list[str]
    addresses_risks: list[str]   



# --- Final report schema ---
### Leading recommendation slide, most essential recommendations across all topics
class RoadmapItem(BaseModel):
    recommendation_title: str
    Topic: str
    cost_estimate: str
    cost_type: str
    q1: bool
    q2: bool
    q3: bool
    q4: bool

### Data associated with each topic, current state assessment + recommendations
class TopicReport(BaseModel):
    Topic_id: str
    Topic_name: str
    question_responses: list[QuestionResponse]
    risks: list[Risk]
    recommendations: list[Recommendation]

### Aggregate of RoadmapItem + all TopicReports
class AssessmentReport(BaseModel):
    engagement_id: str
    organization_name: str
    year_one_roadmap: list[RoadmapItem]
    categories: list[TopicReport]