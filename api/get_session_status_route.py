from api.interview_context import (
    router,
    _completed_rounds,
    _get_session,
    _pending_rounds,
)


@router.get("/session/{interview_id}")
async def get_session_status(interview_id: str):
    session = _get_session(interview_id)

    return {
        "interview_id": interview_id,
        "selected_round": session.get("selected_round"),
        "completed_rounds": _completed_rounds(session),
        "pending_rounds": _pending_rounds(session),
        "rounds": {
            round_type: {
                "completed": data.get("completed", False),
                "current_question_index": data.get("current_question_index", 0),
                "total_questions": len(data.get("questions", [])),
                "answered_questions": len(data.get("answers", []))
            }
            for round_type, data in session.get("rounds", {}).items()
        },
        "current_question_index": session.get("current_question_index", 0),
        "total_questions": sum(
            len(data.get("questions", []))
            for data in session.get("rounds", {}).values()
        ),
        "answered_questions": len(session.get("answers", [])),
        "human_in_the_loop": {
            "required": session.get("human_review_required", False),
            "status": session.get("human_review_status", "not_started"),
            "review": session.get("human_review")
        },
        "interview_completed": session.get("interview_completed", False),
        "download_url": (
            f"/interview/report/{interview_id}"
            if session.get("interview_completed")
            else None
        )
    }
