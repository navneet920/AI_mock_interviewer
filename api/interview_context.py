from typing import Any, Dict, List
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from agents.coding_agent import CodingAgent
from agents.feedback_agent import FeedbackAgent
from agents.hr_agent import HRAgent
from agents.planner_agent import PlannerAgent
from agents.report_agent import ReportAgent
from agents.resume_agent import ResumeAgent
from agents.technical_agent import TechnicalAgent
from services.llm_service import LLMService

router = APIRouter(
    prefix="/interview",
    tags=["Interview"]
)

llm = LLMService.get_llm()

resume_agent = ResumeAgent(llm)
planner_agent = PlannerAgent(llm)
hr_agent = HRAgent(llm)
technical_agent = TechnicalAgent(llm)
coding_agent = CodingAgent(llm)
feedback_agent = FeedbackAgent(llm)
report_agent = ReportAgent(llm)

INTERVIEW_SESSIONS: Dict[str, Dict[str, Any]] = {}
ACTIVE_INTERVIEW_ID: str | None = None
VALID_ROUNDS = {"hr", "technical", "coding"}
ROUND_ORDER = ["hr", "technical", "coding"]


def _get_session(interview_id: str) -> Dict[str, Any]:
    session = INTERVIEW_SESSIONS.get(interview_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )

    return session


def _get_active_session() -> Dict[str, Any]:
    if not ACTIVE_INTERVIEW_ID:
        raise HTTPException(
            status_code=400,
            detail="Upload a resume before starting the interview"
        )

    return _get_session(ACTIVE_INTERVIEW_ID)


def _get_requested_session(interview_id: str | None = None) -> Dict[str, Any]:
    if interview_id:
        return _get_session(interview_id)

    return _get_active_session()


def _extract_questions(result: Any) -> List[Dict[str, Any]]:
    if isinstance(result, dict):
        questions = result.get("questions", [])
    else:
        questions = result

    if not isinstance(questions, list):
        return []

    normalized = []

    for index, question in enumerate(questions, start=1):
        if isinstance(question, dict):
            item = question.copy()
        else:
            item = {
                "question": str(question)
            }

        item.setdefault("id", index)
        normalized.append(item)

    return normalized


def _resume_text(resume_data: Dict[str, Any], *keys: str) -> str:
    values = []

    for key in keys:
        item = resume_data.get(key)

        if isinstance(item, list):
            for entry in item:
                if isinstance(entry, dict):
                    values.append(", ".join(str(value) for value in entry.values() if value))
                elif entry:
                    values.append(str(entry))
        elif item:
            values.append(str(item))

    return "; ".join(value for value in values if value)


def _fallback_question(
    round_type: str,
    index: int,
    resume_data: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    resume_data = resume_data or {}
    skills = _resume_text(resume_data, "skills") or "the skills from the uploaded resume"
    projects = _resume_text(resume_data, "projects") or "a project from the uploaded resume"
    experience = (
        _resume_text(resume_data, "internship", "experience")
        or "the experience from the uploaded resume"
    )
    fallback_questions = {
        "hr": [
            f"Tell me about yourself and connect your answer with {skills}.",
            f"Why are you interested in this role based on {projects}?",
            f"Describe a challenging situation you handled while working on {projects}.",
            f"How do you work with teammates when using {skills} on a project?",
            f"What are your key strengths from {skills}, and one area you are improving?",
            f"Where do you see your career going after your work on {projects}?",
            f"Tell me about feedback you received during {experience}.",
            f"How do you manage deadlines for work related to {skills}?",
            f"What motivates you about the work shown in your uploaded resume?",
            f"Why should we consider you based on {projects}?",
            f"Describe a time you showed ownership during {experience}.",
            f"How do you handle disagreement while collaborating on {projects}?",
            f"What did you learn from {projects}?",
            f"How do you stay organized when working with {skills}?",
            f"What work environment helps you perform well with {skills}?",
            f"Tell me about a time you adapted to change during {projects}.",
            f"How do you handle mistakes while working with {skills}?",
            f"What are your expectations from your next role after {experience}?",
            f"How do you communicate progress while working on {projects}?",
            f"What would you like to improve beyond {skills}?"
        ],
        "technical": [
            f"Explain one important technical concept from {skills}.",
            f"Describe the architecture of {projects}.",
            f"How would you debug a production issue related to {projects}?",
            f"Explain a tradeoff you made while using {skills}.",
            f"How would you make code for {projects} maintainable?",
            f"Describe how you would optimize a slow feature in {projects}.",
            f"How do you validate a solution built with {skills}?",
            f"Explain an API, model, or database design decision from {projects}.",
            f"What security or reliability concerns apply to {projects}?",
            f"How do you choose between two technical approaches when using {skills}?",
            f"Explain how you handled errors in {projects}.",
            f"How would you improve scalability in {projects}?",
            f"Describe your testing strategy for work based on {skills}.",
            f"How do you review code quality in projects like {projects}?",
            f"Explain a technical challenge from {experience}.",
            f"How would you monitor application health for {projects}?",
            f"Describe a data structure or algorithm suitable for {projects}.",
            f"How do you document technical decisions while using {skills}?",
            f"What would you refactor in {projects}?",
            f"How do you keep improving your knowledge of {skills}?"
        ],
        "coding": [
            f"Write a function for {projects} that finds duplicate records.",
            f"Write a function using {skills} to reverse words in project text.",
            f"Write a function for {projects} that validates input strings.",
            f"Write a function using {skills} to count frequency in project data.",
            f"Write a function for {projects} that merges two sorted result lists.",
            f"Write a function using {skills} to find the second highest score.",
            f"Write a function for {projects} that removes duplicates while preserving order.",
            f"Write a function using {skills} to validate balanced brackets in input.",
            f"Write a function for {projects} that groups records by category.",
            f"Write a function using {skills} to flatten nested project data.",
            f"Write a function for {projects} that finds missing IDs in a range.",
            f"Write a function using {skills} to rotate a task list by k positions.",
            f"Write a function for {projects} that compares two metric dictionaries.",
            f"Write a function using {skills} to implement a simple cache.",
            f"Write a function for {projects} that sorts records by multiple fields.",
            f"Write a function using {skills} to find the longest token in project text.",
            f"Write a function for {projects} that calculates running averages.",
            f"Write a function using {skills} to parse a CSV-like string.",
            f"Write a function for {projects} that finds common items between datasets.",
            f"Write a function using {skills} to chunk data into fixed-size groups."
        ]
    }
    questions = fallback_questions[round_type]
    question = questions[(index - 1) % len(questions)]

    return {
        "id": index,
        "category": "Resume Based Fallback",
        "resume_basis": "Uploaded resume",
        "question": question
    }


def _ensure_question_count(
    questions: List[Dict[str, Any]],
    round_type: str,
    requested_count: int,
    resume_data: Dict[str, Any] | None = None
) -> List[Dict[str, Any]]:
    normalized = questions[:requested_count]
    existing_texts = {
        str(question.get("question", "")).strip().lower()
        for question in normalized
    }

    while len(normalized) < requested_count:
        fallback = _fallback_question(round_type, len(normalized) + 1, resume_data)
        fallback_text = fallback["question"].strip().lower()

        if fallback_text in existing_texts:
            fallback["question"] = (
                f"{fallback['question']} Explain with a different example."
            )

        existing_texts.add(fallback["question"].strip().lower())
        normalized.append(fallback)

    for index, question in enumerate(normalized, start=1):
        question["id"] = index

    return normalized


def _get_round_state(session: Dict[str, Any], round_type: str) -> Dict[str, Any]:
    rounds = session.setdefault("rounds", {})
    return rounds.setdefault(
        round_type,
        {
            "questions": [],
            "current_question_index": 0,
            "answers": [],
            "completed": False,
            "num_questions": 0
        }
    )


def _completed_rounds(session: Dict[str, Any]) -> List[str]:
    rounds = session.get("rounds", {})
    return [
        round_type
        for round_type in ROUND_ORDER
        if rounds.get(round_type, {}).get("completed")
    ]


def _pending_rounds(session: Dict[str, Any]) -> List[str]:
    completed = set(_completed_rounds(session))
    return [
        round_type
        for round_type in ROUND_ORDER
        if round_type not in completed
    ]


def _planned_question_count(session: Dict[str, Any], round_type: str) -> int:
    question_distribution = (
        session
        .get("interview_plan", {})
        .get("question_distribution", {})
    )
    planned_count = question_distribution.get(round_type, 1)

    try:
        planned_count = int(planned_count)
    except (TypeError, ValueError):
        planned_count = 1

    return max(planned_count, 1)


def _current_question_payload(session: Dict[str, Any]) -> Dict[str, Any]:
    selected_round = session["selected_round"]
    round_state = _get_round_state(session, selected_round)
    current_index = round_state["current_question_index"]
    questions = round_state["questions"]

    if current_index >= len(questions):
        round_state["completed"] = True

    base_payload = {
        "interview_id": session["interview_id"],
        "selected_round": selected_round,
        "available_rounds": _pending_rounds(session),
        "completed_rounds": _completed_rounds(session),
        "pending_rounds": _pending_rounds(session),
        "all_rounds_completed": len(_completed_rounds(session)) == len(ROUND_ORDER)
    }

    if current_index >= len(questions):
        if base_payload["all_rounds_completed"]:
            message = "All rounds are completed. Submit the interview to generate feedback and report."
            next_action = "submit_interview"
        else:
            message = "Round completed. Choose another interview round."
            next_action = "select_next_round"

        return {
            **base_payload,
            "completed": True,
            "message": message,
            "next_action": next_action,
            "human_in_the_loop": {
                "required": False,
                "status": "waiting_for_rounds"
            }
        }

    return {
        **base_payload,
        "completed": False,
        "question_number": current_index + 1,
        "total_questions": len(questions),
        "question": questions[current_index],
        "human_in_the_loop": {
            "required": False,
            "status": "interview_in_progress"
        },
        "next_action": "submit_answer"
    }


def _average_score(feedbacks: List[Dict[str, Any]]) -> float:
    if not feedbacks:
        return 0.0

    scores = [
        float(feedback.get("overall_score", 0) or 0)
        for feedback in feedbacks
    ]

    return round(sum(scores) / len(scores), 2)


def _resume_extraction_status(resume_data: Dict[str, Any]) -> Dict[str, Any]:
    fields = [
        "name",
        "summary",
        "skills",
        "education",
        "projects",
        "internship",
        "certifications",
        "achievements"
    ]
    extracted_fields = [
        field
        for field in fields
        if resume_data.get(field)
    ]

    return {
        "success": bool(extracted_fields),
        "extracted_fields": extracted_fields,
        "missing_fields": [
            field
            for field in fields
            if field not in extracted_fields
        ]
    }


async def _extract_answer_text(request: Request) -> str:
    content_type = request.headers.get("content-type", "").lower()
    answer = None

    if "application/json" in content_type:
        raw_body = await request.body()

        if not raw_body:
            answer = request.query_params.get("answer")
        else:
            raw_text = raw_body.decode("utf-8", errors="replace").strip()

            try:
                payload = await request.json()
            except Exception:
                payload = raw_text

            if isinstance(payload, dict):
                for key in ("answer", "code", "response", "text"):
                    if payload.get(key) is not None:
                        answer = payload.get(key)
                        break
            else:
                answer = payload

    elif (
        "multipart/form-data" in content_type
        or "application/x-www-form-urlencoded" in content_type
    ):
        try:
            form = await request.form()
        except Exception:
            raw_body = await request.body()
            parsed = parse_qs(raw_body.decode("utf-8", errors="replace"))
            form = {
                key: values[0]
                for key, values in parsed.items()
                if values
            }

        for key in ("answer", "code", "response", "text"):
            if form.get(key) is not None:
                answer = form.get(key)
                break
    else:
        raw_body = await request.body()
        answer = raw_body.decode("utf-8", errors="replace")

        if not str(answer).strip():
            answer = request.query_params.get("answer")

    if answer is None or not str(answer).strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "Answer cannot be empty. Send JSON like "
                "{\"answer\": \"your answer\"}, form field answer, or text/plain."
            )
        )

    return str(answer)


async def _extract_interview_id(request: Request) -> str | None:
    content_type = request.headers.get("content-type", "").lower()
    interview_id = request.query_params.get("interview_id")

    if interview_id:
        return interview_id

    if "application/json" in content_type:
        raw_body = await request.body()

        if not raw_body:
            return None

        try:
            payload = await request.json()
        except Exception:
            return raw_body.decode("utf-8", errors="replace").strip() or None

        if isinstance(payload, dict):
            return payload.get("interview_id")

        if isinstance(payload, str):
            return payload.strip() or None

        return None

    if (
        "multipart/form-data" in content_type
        or "application/x-www-form-urlencoded" in content_type
    ):
        try:
            form = await request.form()
        except Exception:
            return None

        return form.get("interview_id")

    raw_body = await request.body()
    return raw_body.decode("utf-8", errors="replace").strip() or None
