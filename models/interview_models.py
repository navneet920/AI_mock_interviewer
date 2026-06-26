from pydantic import BaseModel, validator
from typing import Literal, Optional


class RoundRequest(BaseModel):

    round_type: Literal["hr", "technical", "coding"]
    num_questions: Optional[int] = None

    @validator("num_questions")
    def validate_num_questions(cls, value):
        if value is None:
            return value

        if value < 1:
            raise ValueError("num_questions must be at least 1")

        return value


class AnswerRequest(BaseModel):

    answer: str


class SubmitRequest(BaseModel):

    interview_id: Optional[str] = None


class HumanReviewRequest(BaseModel):

    interview_id: Optional[str] = None
    status: Literal["approved", "needs_changes", "rejected"]
    reviewer_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
