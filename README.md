# Current Workflow Architecture

## Project Purpose

This project is a FastAPI-based AI mock interviewer. It lets a candidate upload a resume, generates a resume-aware interview plan, asks HR, technical, and coding questions, collects answers, evaluates responses with an LLM, generates a final report, optionally supports human review, and serves the generated PDF report.

## High-Level Architecture

```text
Client / API Consumer
        |
        v
FastAPI app (main.py)
        |
        v
/interview router (api/interview_routes.py)
        |
        v
Route modules registered on shared APIRouter
        |
        +--> Upload resume
        +--> Select round
        +--> Submit answer
        +--> Submit interview
        +--> Human review
        +--> Download report
        +--> Session status
        |
        v
Shared interview context and in-memory session store
        |
        v
Agents + Services + Prompts
        |
        v
Generated report PDF in reports/
```

## Runtime Entry Point

- `main.py` creates the FastAPI application with title `AI Mock Interviewer`.
- The app includes the shared interview router from `api/interview_routes.py`.
- The root endpoint `/` returns a simple health/status message.

## API Routing Architecture

`api/interview_routes.py` imports the shared router from `api/interview_context.py` and imports endpoint modules for side-effect registration. Every route module uses the same router prefix:

```text
/interview
```

Registered endpoints:

| Method | Path | Module | Responsibility |
| --- | --- | --- | --- |
| POST | `/interview/upload-resume` | `api/upload_resume_route.py` | Upload resume, parse content, analyze resume, create interview plan, create session |
| POST | `/interview/select-round` | `api/select_round_route.py` | Select HR, technical, or coding round and generate questions |
| POST | `/interview/answer` | `api/submit_answer_route.py` | Submit answer for the current question and move to the next question |
| POST | `/interview/submit` | `api/submit_interview_route.py` | Evaluate all answers, generate final report, generate PDF |
| POST | `/interview/human-review` | `api/human_review_route.py` | Save human review result and regenerate report PDF |
| GET | `/interview/report/{interview_id}` | `api/download_report_route.py` | Download generated PDF report |
| GET | `/interview/session/{interview_id}` | `api/get_session_status_route.py` | Return current interview progress and review status |

## Shared Context

`api/interview_context.py` is the central runtime coordination layer.

It owns:

- Shared `APIRouter` with prefix `/interview`.
- Shared LLM instance from `LLMService.get_llm()`.
- Shared agent instances:
  - `ResumeAgent`
  - `PlannerAgent`
  - `HRAgent`
  - `TechnicalAgent`
  - `CodingAgent`
  - `FeedbackAgent`
  - `ReportAgent`
- In-memory session store:
  - `INTERVIEW_SESSIONS: Dict[str, Dict[str, Any]]`
  - `ACTIVE_INTERVIEW_ID: str | None`
- Round constants:
  - `VALID_ROUNDS = {"hr", "technical", "coding"}`
  - `ROUND_ORDER = ["hr", "technical", "coding"]`

## Current User Workflow

```text
1. User uploads resume
   POST /interview/upload-resume
        |
        v
2. Resume is saved to uploads/
        |
        v
3. ResumeService parses PDF/DOCX text
        |
        v
4. ResumeAgent converts resume text into structured resume_data
        |
        v
5. PlannerAgent creates interview_plan
        |
        v
6. New interview session is stored in INTERVIEW_SESSIONS
        |
        v
7. User selects a round
   POST /interview/select-round
        |
        v
8. Round-specific agent generates questions
        |
        v
9. User submits answers one by one
   POST /interview/answer
        |
        v
10. After all HR, technical, and coding rounds are complete,
    user submits interview
    POST /interview/submit
        |
        v
11. FeedbackAgent evaluates every answer
        |
        v
12. ReportAgent creates final report JSON
        |
        v
13. PDFService writes report PDF to reports/
        |
        v
14. If score is low, human review may be required
        |
        v
15. User downloads report
    GET /interview/report/{interview_id}
```

## Detailed Workflow Steps

### 1. Resume Upload

File: `api/upload_resume_route.py`

Flow:

1. Accepts `UploadFile` from the request.
2. Allows only `pdf` and `docx` extensions.
3. Creates `uploads/` if it does not exist.
4. Saves the file using a UUID-based filename.
5. Calls `ResumeService.parse_resume(file_path)`.
6. Calls `resume_agent.analyze_resume(resume_text)`.
7. Calls `planner_agent.create_interview_plan(resume_data)`.
8. Creates a new `interview_id`.
9. Stores the full session in `INTERVIEW_SESSIONS`.
10. Updates `ACTIVE_INTERVIEW_ID`.
11. Returns resume data, interview plan, extraction status, and available rounds.

Session fields initialized here:

```text
interview_id
resume_file_path
resume_text
resume_data
interview_plan
selected_round
rounds
questions
current_question_index
answers
feedbacks
final_report
report_path
human_review_required
human_review_status
human_review
interview_completed
```

### 2. Resume Parsing

File: `services/resume_service.py`

Responsibilities:

- Parse PDF resumes using `fitz`.
- Parse DOCX resumes using `python-docx`.
- Clean extracted text using `clean_resume_text`.
- Return plain cleaned resume text to the upload route.

### 3. Resume Analysis

File: `agents/resume_agent.py`

Responsibilities:

- Builds a resume extraction prompt using `prompts/resume_prompt.py`.
- Calls the configured LLM.
- Extracts JSON from the LLM response.
- Normalizes resume fields.
- Uses rule-based fallback extraction if LLM parsing fails.

Expected `resume_data` shape:

```json
{
  "name": "",
  "summary": "",
  "skills": [],
  "education": [],
  "projects": [],
  "internship": [],
  "certifications": [],
  "achievements": []
}
```

### 4. Interview Planning

File: `agents/planner_agent.py`

Responsibilities:

- Builds a planner prompt using `prompts/planner_prompt.py`.
- Calls the LLM to create interview strategy.
- Falls back to a default fresher/medium plan if parsing fails.

Typical `interview_plan` shape:

```json
{
  "candidate_level": "Fresher",
  "difficulty": "Medium",
  "question_distribution": {
    "hr": 3,
    "technical": 5,
    "coding": 2
  },
  "focus_areas": [],
  "interview_flow": ["HR", "Technical", "Coding"]
}
```

### 5. Round Selection

File: `api/select_round_route.py`

Flow:

1. Accepts `RoundRequest` with `round_type` and optional `num_questions`.
2. Validates round type against `hr`, `technical`, and `coding`.
3. Loads the active session.
4. Prevents selecting a different round while another round is incomplete.
5. Prevents repeating an already completed round.
6. Reuses existing round questions if the selected round already started.
7. Uses the planned question count or request override.
8. Calls the matching agent:
   - HR: `HRAgent.generate_questions()`
   - Technical: `TechnicalAgent.generate_questions()`
   - Coding: `CodingAgent.generate_questions()`
9. Normalizes generated questions.
10. Fills missing questions with resume-based fallback questions.
11. Stores round state under `session["rounds"][round_type]`.
12. Returns current question payload.

Round state shape:

```json
{
  "questions": [],
  "current_question_index": 0,
  "answers": [],
  "completed": false,
  "num_questions": 0
}
```

### 6. Question Generation Agents

Files:

- `agents/hr_agent.py`
- `agents/technical_agent.py`
- `agents/coding_agent.py`

Responsibilities:

- Build round-specific prompts.
- Use resume data, projects, skills, experience, education, focus areas, and difficulty.
- Request JSON questions from the LLM.
- Return fallback resume-based questions if JSON parsing fails.

Question shape:

```json
{
  "id": 1,
  "category": "Resume Based",
  "difficulty": "Medium",
  "resume_basis": "Uploaded resume",
  "question": "Question text"
}
```

### 7. Answer Submission

File: `api/submit_answer_route.py`

Flow:

1. Extracts answer text from JSON, form data, plain text, or query param.
2. Loads active session.
3. Rejects submission if interview is already completed.
4. Ensures a round is selected and questions exist.
5. Gets current question from current round state.
6. Creates an answer item with round, question, answer, type, category, and question number.
7. Appends the answer to both round-level and session-level answer lists.
8. Increments `current_question_index`.
9. Marks round completed if all questions are answered.
10. Returns either the next question or completion instructions.

Answer item shape:

```json
{
  "round": "technical",
  "question_id": 1,
  "question_number": 1,
  "question": "Question text",
  "answer": "Candidate answer",
  "type": "technical",
  "category": "Resume Based"
}
```

### 8. Interview Submission

File: `api/submit_interview_route.py`

Flow:

1. Reads `interview_id` from request or active session.
2. Loads the session.
3. Validates that at least one round has started.
4. Requires all HR, technical, and coding rounds to be completed.
5. If already completed, returns existing report data.
6. Evaluates each answer using `FeedbackAgent.evaluate_answer()`.
7. Splits feedback into HR, technical, and coding groups.
8. Calls `ReportAgent.generate_report()`.
9. Calculates round scores and overall score.
10. Marks human review required if overall score is below 5.
11. Adds detailed feedback and review metadata to final report.
12. Calls `PDFService.generate_interview_report()`.
13. Updates session with feedbacks, final report, report path, review status, and completion flag.
14. Returns final report, download URL, and next action.

### 9. Feedback Generation

File: `agents/feedback_agent.py`

Responsibilities:

- Builds feedback prompt using `prompts/feedback_prompt.py`.
- Calls the LLM for each submitted answer.
- Returns structured scoring and feedback.
- Falls back to zero-score structured feedback on parsing failure.

Expected feedback shape:

```json
{
  "overall_score": 0,
  "communication": 0,
  "technical_accuracy": 0,
  "problem_solving": 0,
  "confidence": 0,
  "completeness": 0,
  "strengths": [],
  "weaknesses": [],
  "feedback": "",
  "improvement_suggestions": []
}
```

### 10. Report Generation

Files:

- `agents/report_agent.py`
- `services/pdf_service.py`

Responsibilities:

- `ReportAgent` creates final interview summary JSON using resume data and feedback groups.
- `PDFService` writes the final JSON report to a PDF file under `reports/`.
- The generated file path is saved in the session as `report_path`.

### 11. Human Review

File: `api/human_review_route.py`

Flow:

1. Accepts status, optional reviewer notes, optional reviewer name, and optional interview ID.
2. Loads session.
3. Requires the interview to be submitted and final report to exist.
4. Saves review data into the session.
5. Updates final report with review status and review details.
6. Regenerates the PDF report.
7. Returns updated final report and download URL.

Review shape:

```json
{
  "status": "approved",
  "reviewer_notes": "",
  "reviewed_by": "human_reviewer"
}
```

### 12. Report Download

File: `api/download_report_route.py`

Flow:

1. Loads session by `interview_id`.
2. Reads `report_path` from session.
3. Confirms the PDF exists on disk.
4. Returns the file as `FileResponse`.

### 13. Session Status

File: `api/get_session_status_route.py`

Returns:

- Selected round.
- Completed rounds.
- Pending rounds.
- Per-round progress.
- Total question count.
- Answered question count.
- Human review status.
- Interview completion status.
- Download URL if completed.

## LangGraph Workflow

File: `graph/workflow.py`

The project also contains a LangGraph workflow definition, but the active HTTP workflow is currently implemented directly inside FastAPI route handlers and shared session context.

Graph nodes:

```text
START
  -> resume_node
  -> planner_node
  -> hr_node
  -> technical_node
  -> coding_node
  -> collect_questions_node
  -> feedback_node
  -> score_node
  -> human_review_node
  -> report_node
  -> END
```

State schema file: `state/interview_state.py`

The graph represents a complete linear interview pipeline, while current API routes support an interactive step-by-step interview flow.

## Current State Management

The project currently uses in-memory state:

```text
INTERVIEW_SESSIONS = {
  interview_id: session_dict
}
```

Important behavior:

- State is lost when the server restarts.
- Only one `ACTIVE_INTERVIEW_ID` is tracked globally.
- Multiple sessions can exist in `INTERVIEW_SESSIONS`, but active-session routes default to the latest uploaded resume.
- Generated files persist on disk in `uploads/` and `reports/`.

## Main Components

| Layer | Files | Responsibility |
| --- | --- | --- |
| API app | `main.py` | Creates FastAPI app and mounts router |
| API router | `api/interview_routes.py`, `api/interview_context.py` | Registers routes and shared context |
| Endpoint modules | `api/*_route.py` | Handle HTTP requests and session changes |
| Models | `models/interview_models.py` | Pydantic request validation |
| Agents | `agents/*.py` | LLM-based resume, planning, question, feedback, and report generation |
| Prompts | `prompts/*.py` | Prompt builders for agents |
| Services | `services/*.py` | Resume parsing, PDF generation, LLM access, speech helpers |
| Graph | `graph/*.py`, `state/interview_state.py` | LangGraph-based pipeline definition |
| Storage folders | `uploads/`, `reports/` | Uploaded resumes and generated PDF reports |

## Current Architecture Notes

- The application is currently session-dictionary driven, not database driven.
- `INTERVIEW_SESSIONS` is the source of truth during runtime.
- Uploaded resumes and generated reports are persisted as files.
- LLM outputs are normalized and fallback logic exists for question generation and resume parsing.
- The API requires all three rounds to be completed before final submission.
- Human review is triggered automatically when calculated overall score is below 5.

## Recommended Next Architecture Improvements

1. Replace global in-memory sessions with a database-backed session repository.
2. Store every interview, round, question, answer, feedback, and review in persistent tables.
3. Replace `ACTIVE_INTERVIEW_ID` with explicit `interview_id` in each route.
4. Add authentication or user ownership before storing production interviews.
5. Move file paths, upload folder, report folder, and score threshold into config.
6. Add tests for route flow, fallback question generation, report generation, and session transitions.
