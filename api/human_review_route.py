from fastapi import HTTPException

import api.interview_context as context
from api.interview_context import router, _get_session
from models.interview_models import HumanReviewRequest
from services.pdf_service import PDFService


@router.post("/human-review")
async def human_review(request: HumanReviewRequest):
    interview_id = request.interview_id or context.ACTIVE_INTERVIEW_ID

    if not interview_id:
        raise HTTPException(
            status_code=400,
            detail="Upload and submit an interview before human review"
        )

    session = _get_session(interview_id)

    if not session.get("interview_completed") or not session.get("final_report"):
        raise HTTPException(
            status_code=400,
            detail="Submit the interview before human review"
        )

    review = {
        "status": request.status,
        "reviewer_notes": request.reviewer_notes or "",
        "reviewed_by": request.reviewed_by or "human_reviewer"
    }

    session["human_review"] = review
    session["human_review_status"] = request.status
    session["final_report"]["human_review_status"] = request.status
    session["final_report"]["human_review"] = review

    report_path = PDFService.generate_interview_report(
        interview_id,
        session["final_report"]
    )
    session["report_path"] = report_path

    return {
        "message": "Human review saved",
        "interview_id": interview_id,
        "human_review": review,
        "final_report": session["final_report"],
        "download_url": f"/interview/report/{interview_id}",
        "next_action": "download_report"
    }
