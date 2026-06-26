from fastapi import HTTPException, Request

import api.interview_context as context
from api.interview_context import (
    feedback_agent,
    report_agent,
    router,
    _average_score,
    _completed_rounds,
    _extract_interview_id,
    _get_session,
    _pending_rounds,
)
from models.interview_models import SubmitRequest
from services.pdf_service import PDFService


@router.post(
    "/submit",
    openapi_extra={
        "requestBody": {
            "required": False,
            "content": {
                "application/json": {
                    "schema": SubmitRequest.schema(),
                    "example": {
                        "interview_id": "paste_interview_id_here"
                    }
                }
            }
        }
    }
)
async def submit_interview(request: Request):
    interview_id = await _extract_interview_id(request) or context.ACTIVE_INTERVIEW_ID

    if not interview_id:
        raise HTTPException(
            status_code=400,
            detail="Upload a resume before submitting the interview"
        )

    session = _get_session(interview_id)

    rounds = session.get("rounds", {})

    if not rounds:
        raise HTTPException(
            status_code=400,
            detail="No interview round has been started"
        )

    pending_rounds = _pending_rounds(session)

    if pending_rounds:
        raise HTTPException(
            status_code=400,
            detail=f"Complete all rounds before submitting. Pending rounds: {', '.join(pending_rounds)}"
        )

    if session.get("interview_completed"):
        return {
            "message": "Interview already submitted",
            "interview_id": interview_id,
            "final_report": session["final_report"],
            "download_url": f"/interview/report/{interview_id}"
        }

    feedbacks = []

    for item in session["answers"]:
        feedback = feedback_agent.evaluate_answer(
            question=item["question"],
            answer=item["answer"],
            question_type=item["type"]
        )
        feedbacks.append(
            {
                **item,
                "feedback": feedback
            }
        )

    hr_feedbacks = [
        item
        for item in feedbacks
        if item["type"] == "hr"
    ]
    technical_feedbacks = [
        item
        for item in feedbacks
        if item["type"] == "technical"
    ]
    coding_feedbacks = [
        item
        for item in feedbacks
        if item["type"] == "coding"
    ]

    final_report = report_agent.generate_report(
        resume_data=session["resume_data"],
        hr_feedbacks=[item["feedback"] for item in hr_feedbacks],
        technical_feedbacks=[item["feedback"] for item in technical_feedbacks],
        coding_feedbacks=[item["feedback"] for item in coding_feedbacks]
    )

    round_scores = {
        "hr": _average_score([item["feedback"] for item in hr_feedbacks]),
        "technical": _average_score([item["feedback"] for item in technical_feedbacks]),
        "coding": _average_score([item["feedback"] for item in coding_feedbacks])
    }
    overall_score = _average_score([item["feedback"] for item in feedbacks])
    human_review_required = overall_score < 5
    human_review_status = (
        "pending"
        if human_review_required
        else "not_required"
    )

    final_report.update(
        {
            "completed_rounds": _completed_rounds(session),
            "round_scores": round_scores,
            "overall_score": final_report.get("overall_score", overall_score),
            "calculated_overall_score": overall_score,
            "total_questions": len(session["answers"]),
            "answered_questions": len(session["answers"]),
            "human_review_required": human_review_required,
            "human_review_status": human_review_status,
            "human_review_message": (
                "Human review recommended before using this result for decisions."
                if human_review_required
                else "Review the feedback, weak areas, and suggestions before downloading the report."
            ),
            "detailed_feedback": feedbacks
        }
    )

    report_path = PDFService.generate_interview_report(
        interview_id,
        final_report
    )

    session["feedbacks"] = feedbacks
    session["final_report"] = final_report
    session["report_path"] = report_path
    session["human_review_required"] = human_review_required
    session["human_review_status"] = human_review_status
    session["human_review"] = None
    session["interview_completed"] = True

    return {
        "message": "Interview submitted successfully",
        "interview_id": interview_id,
        "final_report": final_report,
        "download_url": f"/interview/report/{interview_id}",
        "human_in_the_loop": {
            "required": human_review_required,
            "status": human_review_status,
            "review_url": (
                "/interview/human-review"
                if human_review_required
                else None
            )
        },
        "next_action": (
            "human_review"
            if human_review_required
            else "download_report"
        )
    }
