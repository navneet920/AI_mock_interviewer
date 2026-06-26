from typing import TypedDict, List, Dict, Any


class InterviewState(TypedDict):

    # Resume Information
    resume_text: str
    resume_data: Dict[str, Any]

    # Interview Plan
    interview_plan: Dict[str, Any]

    # Generated Questions
    hr_questions: List[Dict]
    technical_questions: List[Dict]
    coding_questions: List[Dict]

    # Current Interview
    current_question: str
    current_question_type: str

    # Candidate Responses
    answers: List[Dict]

    # Feedback
    hr_feedbacks: List[Dict]
    technical_feedbacks: List[Dict]
    coding_feedbacks: List[Dict]

    # Final Report
    final_report: Dict[str, Any]

    # Interview Status
    interview_completed: bool