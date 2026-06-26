from fastapi import HTTPException

from api.interview_context import (
    VALID_ROUNDS,
    coding_agent,
    hr_agent,
    router,
    technical_agent,
    _current_question_payload,
    _ensure_question_count,
    _extract_questions,
    _get_active_session,
    _get_round_state,
    _planned_question_count,
)
from models.interview_models import RoundRequest


@router.post("/select-round")
async def select_round(request: RoundRequest):
    round_type = request.round_type.lower()

    if round_type not in VALID_ROUNDS:
        raise HTTPException(
            status_code=400,
            detail="Invalid round. Choose hr, technical, or coding."
        )

    session = _get_active_session()

    if session.get("interview_completed"):
        raise HTTPException(
            status_code=400,
            detail="Interview already completed"
        )

    selected_round = session.get("selected_round")

    if selected_round:
        active_round = _get_round_state(session, selected_round)

        if (
            selected_round != round_type
            and active_round.get("questions")
            and not active_round.get("completed")
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Complete the {selected_round} round before choosing another round"
            )

    existing_round = session.setdefault("rounds", {}).get(round_type)

    if existing_round and existing_round.get("completed"):
        raise HTTPException(
            status_code=400,
            detail=f"{round_type} round is already completed. Choose another pending round."
        )

    if existing_round and existing_round.get("questions"):
        session["selected_round"] = round_type
        session["questions"] = existing_round["questions"]
        session["current_question_index"] = existing_round["current_question_index"]
        return _current_question_payload(session)

    resume_data = session["resume_data"]
    requested_count = request.num_questions or _planned_question_count(session, round_type)
    interview_plan = session["interview_plan"].copy()
    question_distribution = dict(interview_plan.get(
        "question_distribution",
        {}
    ))
    question_distribution[round_type] = requested_count
    interview_plan["question_distribution"] = question_distribution
    session["interview_plan"] = interview_plan

    if round_type == "hr":
        result = hr_agent.generate_questions(resume_data, interview_plan)
    elif round_type == "technical":
        result = technical_agent.generate_questions(resume_data, interview_plan)
    else:
        result = coding_agent.generate_questions(resume_data, interview_plan)

    questions = _ensure_question_count(
        _extract_questions(result),
        round_type,
        requested_count,
        resume_data
    )

    if not questions:
        raise HTTPException(
            status_code=500,
            detail="Question generation failed"
        )

    session["rounds"][round_type] = {
        "questions": questions,
        "current_question_index": 0,
        "answers": [],
        "completed": False,
        "num_questions": len(questions)
    }
    session["selected_round"] = round_type
    session["questions"] = questions
    session["current_question_index"] = 0
    session["final_report"] = None
    session["report_path"] = None
    session["human_review_required"] = False
    session["human_review_status"] = "not_started"
    session["human_review"] = None
    session["interview_completed"] = False

    payload = _current_question_payload(session)
    payload["message"] = "Round selected. Answer the current question to receive the next one."

    return payload
