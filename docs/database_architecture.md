# Database Architecture

## Purpose

This document defines a database architecture for the AI Mock Interviewer project. The current project stores interview state in the in-memory `INTERVIEW_SESSIONS` dictionary and stores resume/report files on disk. This architecture converts the runtime session dictionary into persistent relational tables so interviews survive server restarts and can support multiple users, reporting, audit trails, and future analytics.

## Current Persistence State

Current storage behavior:

- Runtime interview data is stored in memory in `INTERVIEW_SESSIONS`.
- The latest active interview is tracked by global `ACTIVE_INTERVIEW_ID`.
- Uploaded resumes are stored in the `uploads/` folder.
- Generated PDF reports are stored in the `reports/` folder.
- No database tables currently exist in the codebase.

Main limitation:

```text
If the FastAPI server restarts, all interview sessions, answers, feedbacks,
review status, and report metadata in memory are lost.
```

## Recommended Database Type

Recommended default for this project:

```text
PostgreSQL for production
SQLite for local development
```

Reasoning:

- The data model is relational: interviews, rounds, questions, answers, feedback, reports, and reviews.
- JSON columns are useful for flexible LLM outputs such as `resume_data`, `interview_plan`, `feedback`, and `final_report`.
- PostgreSQL supports strong relational constraints and efficient JSONB queries.
- SQLite can be used locally with the same ORM models if SQLAlchemy is introduced.

## High-Level Database Architecture

```text
User / Candidate
        |
        v
Interview Session
        |
        +--> Resume Document
        +--> Interview Plan
        +--> Interview Rounds
        |       |
        |       +--> Questions
        |               |
        |               +--> Answers
        |                       |
        |                       +--> Feedback
        |
        +--> Final Report
        |
        +--> Human Review
        |
        +--> Stored Files Metadata
```

## Entity Relationship Overview

```text
candidates 1 --- many interviews
interviews 1 --- 1 resume_documents
interviews 1 --- 1 interview_plans
interviews 1 --- many interview_rounds
interview_rounds 1 --- many questions
questions 1 --- 0..1 answers
answers 1 --- 0..1 feedbacks
interviews 1 --- 0..1 final_reports
interviews 1 --- 0..1 human_reviews
interviews 1 --- many file_assets
```

## Core Tables

### 1. candidates

Stores candidate/user profile data. If authentication is not added yet, this table can still represent the candidate extracted from a resume.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Candidate ID |
| name | VARCHAR | Candidate name from resume or user profile |
| email | VARCHAR / nullable | Candidate email if available later |
| phone | VARCHAR / nullable | Candidate phone if available later |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

Indexes:

- Unique index on `email` if authentication or candidate accounts are added.
- Index on `name` for search.

### 2. interviews

Main interview session table. This replaces the top-level session dictionary currently stored in `INTERVIEW_SESSIONS`.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Same role as current `interview_id` |
| candidate_id | UUID / FK nullable | References `candidates.id` |
| selected_round | VARCHAR nullable | Current selected round: `hr`, `technical`, `coding` |
| status | VARCHAR | `created`, `in_progress`, `submitted`, `review_pending`, `reviewed`, `completed` |
| interview_completed | BOOLEAN | Current completion flag |
| human_review_required | BOOLEAN | Whether human review is needed |
| human_review_status | VARCHAR | `not_started`, `pending`, `approved`, `needs_changes`, `rejected`, `not_required` |
| calculated_overall_score | DECIMAL nullable | Average from answer feedbacks |
| created_at | TIMESTAMP | Created on resume upload |
| submitted_at | TIMESTAMP nullable | Set on interview submit |
| completed_at | TIMESTAMP nullable | Set when final flow is done |
| updated_at | TIMESTAMP | Last update time |

Recommended constraints:

- `selected_round` should be nullable or one of `hr`, `technical`, `coding`.
- `status` should use enum-like validation.
- `human_review_status` should use enum-like validation.

### 3. resume_documents

Stores resume upload metadata, extracted text, and parsed resume JSON.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Resume document ID |
| interview_id | UUID / FK unique | References `interviews.id` |
| original_filename | VARCHAR | Original uploaded filename |
| stored_file_path | TEXT | Path under `uploads/` |
| file_extension | VARCHAR | `pdf` or `docx` |
| resume_text | TEXT | Clean extracted resume text |
| resume_data | JSON / JSONB | Structured output from `ResumeAgent` |
| extraction_status | JSON / JSONB | Extracted/missing fields summary |
| created_at | TIMESTAMP | Upload time |
| updated_at | TIMESTAMP | Last update time |

Recommended indexes:

- Index on `interview_id`.
- Optional JSONB GIN index on `resume_data` for PostgreSQL analytics.

### 4. interview_plans

Stores LLM-generated interview plan.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Plan ID |
| interview_id | UUID / FK unique | References `interviews.id` |
| candidate_level | VARCHAR | Example: `Fresher` |
| difficulty | VARCHAR | Example: `Medium` |
| question_distribution | JSON / JSONB | Example: `{ "hr": 3, "technical": 5, "coding": 2 }` |
| focus_areas | JSON / JSONB | List of focus areas |
| interview_flow | JSON / JSONB | Planned round order |
| raw_plan | JSON / JSONB | Full original plan from LLM |
| created_at | TIMESTAMP | Plan creation time |
| updated_at | TIMESTAMP | Last update time |

### 5. interview_rounds

Stores round-level state. This replaces `session["rounds"][round_type]`.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Round ID |
| interview_id | UUID / FK | References `interviews.id` |
| round_type | VARCHAR | `hr`, `technical`, or `coding` |
| status | VARCHAR | `not_started`, `in_progress`, `completed` |
| current_question_index | INTEGER | Current progress index |
| num_questions | INTEGER | Total planned/generated questions |
| started_at | TIMESTAMP nullable | Set when selected |
| completed_at | TIMESTAMP nullable | Set when final answer is submitted |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

Recommended constraints:

- Unique constraint on `(interview_id, round_type)`.
- `round_type` must be one of `hr`, `technical`, `coding`.

### 6. questions

Stores every generated question.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Question ID |
| interview_id | UUID / FK | References `interviews.id` |
| round_id | UUID / FK | References `interview_rounds.id` |
| round_type | VARCHAR | Denormalized for easier queries |
| question_number | INTEGER | 1-based order inside round |
| category | VARCHAR nullable | LLM/fallback category |
| difficulty | VARCHAR nullable | Question difficulty |
| resume_basis | TEXT nullable | Resume context used |
| question_text | TEXT | Actual question |
| expected_skills | JSON / JSONB nullable | Coding/technical skill list if available |
| source | VARCHAR | `llm` or `fallback` |
| raw_question | JSON / JSONB | Full original generated question object |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

Recommended constraints:

- Unique constraint on `(round_id, question_number)`.
- Index on `(interview_id, round_type)`.

### 7. answers

Stores candidate answers.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Answer ID |
| interview_id | UUID / FK | References `interviews.id` |
| round_id | UUID / FK | References `interview_rounds.id` |
| question_id | UUID / FK unique | References `questions.id` |
| round_type | VARCHAR | `hr`, `technical`, or `coding` |
| answer_text | TEXT | Candidate answer or submitted code |
| content_type | VARCHAR nullable | `json`, `text`, `form`, etc. |
| submitted_at | TIMESTAMP | Answer submission time |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

Recommended constraints:

- One answer per question using unique `question_id`.
- Index on `(interview_id, round_type)`.

### 8. feedbacks

Stores LLM-generated feedback for each answer.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Feedback ID |
| interview_id | UUID / FK | References `interviews.id` |
| answer_id | UUID / FK unique | References `answers.id` |
| round_type | VARCHAR | `hr`, `technical`, or `coding` |
| overall_score | DECIMAL | Main score |
| communication | DECIMAL nullable | Communication score |
| technical_accuracy | DECIMAL nullable | Technical accuracy score |
| problem_solving | DECIMAL nullable | Problem-solving score |
| confidence | DECIMAL nullable | Confidence score |
| completeness | DECIMAL nullable | Completeness score |
| strengths | JSON / JSONB | List of strengths |
| weaknesses | JSON / JSONB | List of weaknesses |
| improvement_suggestions | JSON / JSONB | List of suggestions |
| feedback_text | TEXT | Human-readable feedback |
| raw_feedback | JSON / JSONB | Full original feedback object |
| created_at | TIMESTAMP | Feedback creation time |
| updated_at | TIMESTAMP | Last update time |

Recommended indexes:

- Index on `(interview_id, round_type)`.
- Index on `overall_score` for analytics.

### 9. final_reports

Stores generated final report JSON and summary scores.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Report ID |
| interview_id | UUID / FK unique | References `interviews.id` |
| overall_score | DECIMAL | Score from report agent or calculated score |
| calculated_overall_score | DECIMAL | Average from feedback rows |
| hr_score | DECIMAL nullable | HR score |
| technical_score | DECIMAL nullable | Technical score |
| coding_score | DECIMAL nullable | Coding score |
| strengths | JSON / JSONB | Overall strengths |
| weaknesses | JSON / JSONB | Overall weaknesses |
| summary | TEXT | Final summary |
| recommendation | VARCHAR nullable | Example: `Hire`, `Hold`, `Reject` |
| detailed_feedback | JSON / JSONB | Full detailed feedback list |
| raw_report | JSON / JSONB | Full final report object |
| pdf_file_path | TEXT nullable | Generated PDF path under `reports/` |
| created_at | TIMESTAMP | Report creation time |
| updated_at | TIMESTAMP | Last update time |

Recommended indexes:

- Index on `overall_score`.
- Index on `recommendation`.

### 10. human_reviews

Stores human-in-the-loop review details.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | Human review ID |
| interview_id | UUID / FK unique | References `interviews.id` |
| status | VARCHAR | `approved`, `needs_changes`, or `rejected` |
| reviewer_notes | TEXT | Notes entered by reviewer |
| reviewed_by | VARCHAR | Reviewer identifier/name |
| reviewed_at | TIMESTAMP | Review timestamp |
| created_at | TIMESTAMP | Record creation time |
| updated_at | TIMESTAMP | Last update time |

Recommended indexes:

- Index on `status`.
- Index on `reviewed_by` if reviewer accounts are added.

### 11. file_assets

Stores metadata for uploaded and generated files.

| Column | Type | Notes |
| --- | --- | --- |
| id | UUID / PK | File asset ID |
| interview_id | UUID / FK nullable | References `interviews.id` |
| asset_type | VARCHAR | `resume_upload`, `report_pdf`, `audio_recording`, etc. |
| original_filename | VARCHAR nullable | Original file name |
| stored_file_path | TEXT | Local path or cloud object key |
| mime_type | VARCHAR nullable | File MIME type |
| file_size_bytes | BIGINT nullable | Size if tracked |
| checksum | VARCHAR nullable | Optional integrity hash |
| created_at | TIMESTAMP | Record creation time |

Recommended indexes:

- Index on `(interview_id, asset_type)`.

## Suggested SQLAlchemy Model Layout

If SQLAlchemy is added, recommended project structure:

```text
models/
  interview_models.py          existing Pydantic request models
  db_models.py                 SQLAlchemy ORM models

database/
  __init__.py
  connection.py                engine/session creation
  repositories.py              database access layer
  migrations/                  Alembic migrations
```

Recommended repository classes:

```text
InterviewRepository
ResumeRepository
RoundRepository
QuestionRepository
AnswerRepository
FeedbackRepository
ReportRepository
HumanReviewRepository
FileAssetRepository
```

## Data Flow With Database

### Resume Upload Flow

```text
POST /interview/upload-resume
        |
        v
Save resume file to uploads/ or object storage
        |
        v
Create candidate row if needed
        |
        v
Create interviews row with status = created
        |
        v
Create resume_documents row with resume_text and resume_data
        |
        v
Create interview_plans row
        |
        v
Return interview_id and available rounds
```

### Select Round Flow

```text
POST /interview/select-round
        |
        v
Load interview by interview_id
        |
        v
Create or fetch interview_rounds row
        |
        v
Generate questions if none exist
        |
        v
Insert questions rows
        |
        v
Update interviews.selected_round
        |
        v
Return current unanswered question
```

### Submit Answer Flow

```text
POST /interview/answer
        |
        v
Load selected round and current question
        |
        v
Insert answers row
        |
        v
Increment interview_rounds.current_question_index
        |
        v
Mark round completed if all questions are answered
        |
        v
Return next question or next action
```

### Submit Interview Flow

```text
POST /interview/submit
        |
        v
Verify all rounds are completed
        |
        v
Load all answers with questions
        |
        v
Generate feedback for each answer
        |
        v
Insert feedbacks rows
        |
        v
Generate final report
        |
        v
Insert final_reports row
        |
        v
Generate PDF and save file path
        |
        v
Update interviews status and review flags
        |
        v
Return final report and download URL
```

### Human Review Flow

```text
POST /interview/human-review
        |
        v
Load submitted interview
        |
        v
Insert or update human_reviews row
        |
        v
Update interviews.human_review_status
        |
        v
Update final_reports.raw_report with review data
        |
        v
Regenerate PDF
        |
        v
Return updated report and download URL
```

## Mapping Current Session Fields to Tables

| Current Session Field | Database Location |
| --- | --- |
| `interview_id` | `interviews.id` |
| `resume_file_path` | `resume_documents.stored_file_path`, `file_assets.stored_file_path` |
| `resume_text` | `resume_documents.resume_text` |
| `resume_data` | `resume_documents.resume_data` |
| `interview_plan` | `interview_plans.raw_plan` |
| `selected_round` | `interviews.selected_round` |
| `rounds` | `interview_rounds`, `questions`, `answers` |
| `questions` | `questions` |
| `current_question_index` | `interview_rounds.current_question_index` |
| `answers` | `answers` |
| `feedbacks` | `feedbacks` |
| `final_report` | `final_reports.raw_report` |
| `report_path` | `final_reports.pdf_file_path`, `file_assets.stored_file_path` |
| `human_review_required` | `interviews.human_review_required` |
| `human_review_status` | `interviews.human_review_status` |
| `human_review` | `human_reviews` |
| `interview_completed` | `interviews.interview_completed` |

## Example PostgreSQL DDL

```sql
CREATE TABLE candidates (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interviews (
    id UUID PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id),
    selected_round VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'created',
    interview_completed BOOLEAN NOT NULL DEFAULT FALSE,
    human_review_required BOOLEAN NOT NULL DEFAULT FALSE,
    human_review_status VARCHAR(50) NOT NULL DEFAULT 'not_started',
    calculated_overall_score NUMERIC(5, 2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE resume_documents (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL UNIQUE REFERENCES interviews(id) ON DELETE CASCADE,
    original_filename VARCHAR(255),
    stored_file_path TEXT NOT NULL,
    file_extension VARCHAR(20) NOT NULL,
    resume_text TEXT,
    resume_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    extraction_status JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interview_plans (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL UNIQUE REFERENCES interviews(id) ON DELETE CASCADE,
    candidate_level VARCHAR(100),
    difficulty VARCHAR(100),
    question_distribution JSONB NOT NULL DEFAULT '{}'::jsonb,
    focus_areas JSONB NOT NULL DEFAULT '[]'::jsonb,
    interview_flow JSONB NOT NULL DEFAULT '[]'::jsonb,
    raw_plan JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interview_rounds (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    round_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'not_started',
    current_question_index INTEGER NOT NULL DEFAULT 0,
    num_questions INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_interview_round UNIQUE (interview_id, round_type)
);

CREATE TABLE questions (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    round_id UUID NOT NULL REFERENCES interview_rounds(id) ON DELETE CASCADE,
    round_type VARCHAR(50) NOT NULL,
    question_number INTEGER NOT NULL,
    category VARCHAR(255),
    difficulty VARCHAR(100),
    resume_basis TEXT,
    question_text TEXT NOT NULL,
    expected_skills JSONB,
    source VARCHAR(50) NOT NULL DEFAULT 'llm',
    raw_question JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_round_question_number UNIQUE (round_id, question_number)
);

CREATE TABLE answers (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    round_id UUID NOT NULL REFERENCES interview_rounds(id) ON DELETE CASCADE,
    question_id UUID NOT NULL UNIQUE REFERENCES questions(id) ON DELETE CASCADE,
    round_type VARCHAR(50) NOT NULL,
    answer_text TEXT NOT NULL,
    content_type VARCHAR(100),
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feedbacks (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    answer_id UUID NOT NULL UNIQUE REFERENCES answers(id) ON DELETE CASCADE,
    round_type VARCHAR(50) NOT NULL,
    overall_score NUMERIC(5, 2) NOT NULL DEFAULT 0,
    communication NUMERIC(5, 2),
    technical_accuracy NUMERIC(5, 2),
    problem_solving NUMERIC(5, 2),
    confidence NUMERIC(5, 2),
    completeness NUMERIC(5, 2),
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    weaknesses JSONB NOT NULL DEFAULT '[]'::jsonb,
    improvement_suggestions JSONB NOT NULL DEFAULT '[]'::jsonb,
    feedback_text TEXT,
    raw_feedback JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE final_reports (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL UNIQUE REFERENCES interviews(id) ON DELETE CASCADE,
    overall_score NUMERIC(5, 2) NOT NULL DEFAULT 0,
    calculated_overall_score NUMERIC(5, 2),
    hr_score NUMERIC(5, 2),
    technical_score NUMERIC(5, 2),
    coding_score NUMERIC(5, 2),
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    weaknesses JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT,
    recommendation VARCHAR(100),
    detailed_feedback JSONB NOT NULL DEFAULT '[]'::jsonb,
    raw_report JSONB NOT NULL DEFAULT '{}'::jsonb,
    pdf_file_path TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE human_reviews (
    id UUID PRIMARY KEY,
    interview_id UUID NOT NULL UNIQUE REFERENCES interviews(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    reviewer_notes TEXT,
    reviewed_by VARCHAR(255) NOT NULL DEFAULT 'human_reviewer',
    reviewed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE file_assets (
    id UUID PRIMARY KEY,
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    asset_type VARCHAR(100) NOT NULL,
    original_filename VARCHAR(255),
    stored_file_path TEXT NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT,
    checksum VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Recommended Indexes

```sql
CREATE INDEX idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX idx_interviews_status ON interviews(status);
CREATE INDEX idx_interviews_human_review_status ON interviews(human_review_status);
CREATE INDEX idx_resume_documents_interview_id ON resume_documents(interview_id);
CREATE INDEX idx_interview_rounds_interview_id ON interview_rounds(interview_id);
CREATE INDEX idx_questions_interview_round ON questions(interview_id, round_type);
CREATE INDEX idx_answers_interview_round ON answers(interview_id, round_type);
CREATE INDEX idx_feedbacks_interview_round ON feedbacks(interview_id, round_type);
CREATE INDEX idx_feedbacks_overall_score ON feedbacks(overall_score);
CREATE INDEX idx_final_reports_overall_score ON final_reports(overall_score);
CREATE INDEX idx_human_reviews_status ON human_reviews(status);
CREATE INDEX idx_file_assets_interview_type ON file_assets(interview_id, asset_type);
```

For PostgreSQL JSONB search:

```sql
CREATE INDEX idx_resume_documents_resume_data_gin ON resume_documents USING GIN (resume_data);
CREATE INDEX idx_interview_plans_raw_plan_gin ON interview_plans USING GIN (raw_plan);
CREATE INDEX idx_final_reports_raw_report_gin ON final_reports USING GIN (raw_report);
```

## Data Integrity Rules

Recommended rules:

1. An interview can have only one resume document.
2. An interview can have only one interview plan.
3. An interview can have at most one round per round type.
4. A round can have many questions.
5. A question can have at most one answer.
6. An answer can have at most one feedback record.
7. An interview can have only one final report.
8. An interview can have only one current human review record.
9. Report download should use `final_reports.pdf_file_path` or `file_assets`.
10. The API should require explicit `interview_id` instead of relying on global active session state.

## Transaction Boundaries

Recommended transaction usage:

- Resume upload transaction:
  - Create interview.
  - Create resume document.
  - Create interview plan.
  - Create resume file asset.
- Select round transaction:
  - Create/update round.
  - Insert generated questions.
  - Update selected round.
- Submit answer transaction:
  - Insert answer.
  - Update round progress.
  - Mark round completed if needed.
- Submit interview transaction:
  - Insert feedback rows.
  - Insert/update final report.
  - Update interview status/review flags.
  - Insert report file asset.
- Human review transaction:
  - Insert/update human review.
  - Update interview review status.
  - Update final report and report file path.

## Migration Plan From Current Code

### Phase 1: Add Database Foundation

1. Add database dependency such as SQLAlchemy and Alembic.
2. Add database connection config to `.env`.
3. Create ORM models matching the tables above.
4. Create initial migration.
5. Keep current API behavior unchanged.

### Phase 2: Add Repository Layer

1. Implement repositories for interviews, resumes, rounds, questions, answers, feedbacks, reports, and reviews.
2. Convert session dictionary operations into repository calls.
3. Keep response payloads compatible with current API.

### Phase 3: Replace In-Memory Sessions

1. Remove `INTERVIEW_SESSIONS` as source of truth.
2. Remove `ACTIVE_INTERVIEW_ID` or keep it only for development convenience.
3. Require `interview_id` in round selection and answer submission.
4. Load current state from database for every request.

### Phase 4: File Storage Improvements

1. Store uploaded resume metadata in `file_assets`.
2. Store generated report metadata in `file_assets`.
3. Add cleanup jobs for orphaned files.
4. Optionally move files to S3, Azure Blob Storage, or another object store.

### Phase 5: Analytics and Admin

1. Add candidate search.
2. Add interview dashboard queries.
3. Add score distribution reports.
4. Add reviewer queue for `human_review_status = pending`.

## Recommended API Changes After Database Migration

Current routes rely on active session for some operations. Database-backed routes should prefer explicit IDs.

Suggested request changes:

| Current Endpoint | Recommended Change |
| --- | --- |
| `POST /interview/select-round` | Include `interview_id` in request body |
| `POST /interview/answer` | Include `interview_id` or use `/interview/{interview_id}/answer` |
| `POST /interview/submit` | Require `interview_id` |
| `POST /interview/human-review` | Require `interview_id` |
| `GET /interview/session/{interview_id}` | Keep as-is |
| `GET /interview/report/{interview_id}` | Keep as-is |

## Future Authentication-Aware Design

If user accounts are added, add these tables:

```text
users
roles
user_roles
candidate_profiles
reviewer_profiles
```

Then update:

- `interviews.candidate_id` should reference candidate profile.
- `human_reviews.reviewed_by` should reference a reviewer user ID.
- All interview fetches should filter by owner or role.

## Final Recommended Database Architecture

Use a relational database where `interviews` is the central aggregate root. Keep flexible LLM outputs in JSON/JSONB columns, but normalize operational workflow data into separate tables for rounds, questions, answers, feedback, reports, and reviews.

This gives the project:

- Persistent interview sessions.
- Reliable multi-user support.
- Better report/history retrieval.
- Auditable human review data.
- Easier analytics for scores, rounds, skills, and outcomes.
- A clean migration path from the current in-memory workflow.
