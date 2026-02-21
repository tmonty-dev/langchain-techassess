from pydantic import BaseModel, Field
from typing import Literal

# --- Building blocks ---

class QuestionResponse(BaseModel):
    question_id: str
    question_text: str
    answer: str = Field(description="Synthesized bullet-point answer from source docs")
    source_chunks: list[str] = Field(description="Verbatim excerpts used to form answer")

class Risk(BaseModel):
    description: str
    supporting_quote: str        # verbatim, with source label
    source_document: str

class Recommendation(BaseModel):
    title: str
    description: str
    timeline: Literal["Y1", "Y2", "Y3"]
    priority: Literal["Low", "Medium", "High"]
    cost_estimate: str           # e.g. "$5,000 - $10,000" or "TBD"
    cost_type: Literal["Labor", "Hardware", "Software", "One-Time", "Ongoing", "Mixed"]
    next_steps: list[str]
    benefits: list[str]
    addresses_risks: list[str]   # risk descriptions this rec resolves

# --- Per Topic output (maps to current state + rec slides) ---
class TopicReport(BaseModel):
    Topic_id: str
    Topic_name: str
    question_responses: list[QuestionResponse]
    risks: list[Risk]
    recommendations: list[Recommendation]

# --- Year 1 roadmap (aggregated from Y1 recs across all categories) ---
class RoadmapItem(BaseModel):
    recommendation_title: str
    Topic: str
    cost_estimate: str
    cost_type: str
    q1: bool
    q2: bool
    q3: bool
    q4: bool

# --- Final report schema ---
class AssessmentReport(BaseModel):
    engagement_id: str
    organization_name: str
    year_one_roadmap: list[RoadmapItem]
    categories: list[TopicReport]