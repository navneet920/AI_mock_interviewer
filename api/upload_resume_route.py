import os
import uuid

from fastapi import File, HTTPException, UploadFile

from api.interview_context import (
    INTERVIEW_SESSIONS,
    planner_agent,
    resume_agent,
    router,
    _resume_extraction_status,
)
from services.resume_service import ResumeService


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    filename = file.filename or ""
    extension = filename.rsplit(".", 1)[-1].lower()

    if extension not in {"pdf", "docx"}:
        raise HTTPException(
            status_code=400,
            detail="Only PDF or DOCX allowed"
        )

    os.makedirs("uploads", exist_ok=True)

    file_path = os.path.join(
        "uploads",
        f"{uuid.uuid4()}.{extension}"
    )

    with open(file_path, "wb") as f:
        f.write(await file.read())

    resume_text = ResumeService.parse_resume(file_path)

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from resume"
        )

    resume_data = resume_agent.analyze_resume(resume_text)
    interview_plan = planner_agent.create_interview_plan(resume_data)
    interview_id = str(uuid.uuid4())

    INTERVIEW_SESSIONS[interview_id] = {
        "interview_id": interview_id,
        "resume_file_path": file_path,
        "resume_text": resume_text,
        "resume_data": resume_data,
        "interview_plan": interview_plan,
        "selected_round": None,
        "rounds": {},
        "questions": [],
        "current_question_index": 0,
        "answers": [],
        "feedbacks": [],
        "final_report": None,
        "report_path": None,
        "human_review_required": False,
        "human_review_status": "not_started",
        "human_review": None,
        "interview_completed": False
    }
    import api.interview_context as context
    context.ACTIVE_INTERVIEW_ID = interview_id

    return {
        "message": "Resume uploaded and analyzed successfully",
        "interview_id": interview_id,
        "extraction_status": _resume_extraction_status(resume_data),
        "resume_data": resume_data,
        "interview_plan": interview_plan,
        "available_rounds": ["hr", "technical", "coding"]
    }
