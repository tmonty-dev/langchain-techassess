from pydantic import BaseModel

class Question(BaseModel):
    id: str
    text: str

class Topic(BaseModel):
    id: str
    name: str                    # e.g. "Hardware", "Skilled Staff", "Fitness Department"
    questions: list[Question]

class EngagementConfig(BaseModel):
    engagement_id: str
    organization_name: str
    categories: list[Topic]