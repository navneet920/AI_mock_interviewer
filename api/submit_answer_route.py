from fastapi import HTTPException, Request

from api.interview_context import (
    router,
    _current_question_payload,
    _extract_answer_text,
    _get_active_session,
    _get_round_state,
)
from models.interview_models import AnswerRequest


@router.post(
    "/answer",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": AnswerRequest.schema(),
                    "example": {
                        "answer": (
                            "For HR/technical rounds, write your natural "
                            "language answer here. For coding rounds, paste "
                            "your code here."
                        )
                    }
                },
                "text/plain": {
                    "schema": {
                        "type": "string",
                        "description": "Plain answer text or source code"
                    },
                    "example": "def solve(items):\n    return list(dict.fromkeys(items))"
                }
            }
        }
    }
)
async def submit_answer(request: Request):
    answer = await _extract_answer_text(request)
    session = _get_active_session()

    if session.get("interview_completed"):
        raise HTTPException(
            status_code=400,
            detail="Interview already completed"
        )

    questions = session.get("questions", [])
    selected_round = session.get("selected_round")

    if not selected_round or not questions:
        raise HTTPException(
            status_code=400,
            detail="Select an interview round before submitting answers"
        )

    round_state = _get_round_state(session, selected_round)
    questions = round_state.get("questions", [])
    current_index = round_state.get("current_question_index", 0)

    if current_index >= len(questions):
        return _current_question_payload(session)

    question = questions[current_index]
    question_text = question.get("question", "")
    question_type = selected_round

    answer_item = {
        "round": question_type,
        "question_id": question.get("id", current_index + 1),
        "question_number": current_index + 1,
        "question": question_text,
        "answer": answer,
        "type": question_type,
        "category": question.get("category", "")
    }

    round_state["answers"].append(answer_item)
    session["answers"].append(answer_item)

    round_state["current_question_index"] = current_index + 1
    round_state["completed"] = round_state["current_question_index"] >= len(questions)
    session["current_question_index"] = round_state["current_question_index"]

    return _current_question_payload(session)
