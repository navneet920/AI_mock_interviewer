from state.interview_state import InterviewState

from agents.resume_agent import ResumeAgent
from agents.planner_agent import PlannerAgent
from agents.hr_agent import HRAgent
from agents.technical_agent import TechnicalAgent
from agents.coding_agent import CodingAgent
from agents.feedback_agent import FeedbackAgent
from agents.report_agent import ReportAgent

from services.llm_service import LLMService


# --------------------------------------------------
# Initialize LLM
# --------------------------------------------------

llm = LLMService.get_llm()

# --------------------------------------------------
# Initialize Agents
# --------------------------------------------------

resume_agent = ResumeAgent(llm)

planner_agent = PlannerAgent(llm)

hr_agent = HRAgent(llm)

technical_agent = TechnicalAgent(llm)

coding_agent = CodingAgent(llm)

feedback_agent = FeedbackAgent(llm)

report_agent = ReportAgent(llm)


# ==================================================
# Resume Node
# ==================================================

def resume_node(state: InterviewState):

    resume_text = state["resume_text"]

    resume_data = resume_agent.extract_resume_data(
        resume_text
    )

    state["resume_data"] = resume_data

    return state


# ==================================================
# Planner Node
# ==================================================

def planner_node(state: InterviewState):

    interview_plan = planner_agent.create_plan(
        state["resume_data"]
    )

    state["interview_plan"] = interview_plan

    return state


# ==================================================
# HR Question Generation Node
# ==================================================

def hr_node(state: InterviewState):

    result = hr_agent.generate_questions(
        state["resume_data"],
        state["interview_plan"]
    )

    state["hr_questions"] = result.get(
        "questions",
        []
    )

    return state


# ==================================================
# Technical Question Generation Node
# ==================================================

def technical_node(state: InterviewState):

    result = technical_agent.generate_questions(
        state["resume_data"],
        state["interview_plan"]
    )

    state["technical_questions"] = result.get(
        "questions",
        []
    )

    return state


# ==================================================
# Coding Question Generation Node
# ==================================================

def coding_node(state: InterviewState):

    result = coding_agent.generate_questions(
        state["resume_data"],
        state["interview_plan"]
    )

    state["coding_questions"] = result.get(
        "questions",
        []
    )

    return state


# ==================================================
# Collect All Questions
# ==================================================

def collect_questions_node(state: InterviewState):

    all_questions = []

    all_questions.extend(
        state.get("hr_questions", [])
    )

    all_questions.extend(
        state.get("technical_questions", [])
    )

    all_questions.extend(
        state.get("coding_questions", [])
    )

    state["all_questions"] = all_questions

    return state


# ==================================================
# Feedback Node
# ==================================================

def feedback_node(state: InterviewState):

    answers = state.get("answers", [])

    hr_feedbacks = []
    technical_feedbacks = []
    coding_feedbacks = []

    for item in answers:

        question = item.get("question", "")
        answer = item.get("answer", "")
        question_type = item.get("type", "")

        feedback = feedback_agent.evaluate_answer(
            question=question,
            answer=answer,
            question_type=question_type
        )

        if question_type == "hr":
            hr_feedbacks.append(feedback)

        elif question_type == "technical":
            technical_feedbacks.append(feedback)

        elif question_type == "coding":
            coding_feedbacks.append(feedback)

    state["hr_feedbacks"] = hr_feedbacks

    state["technical_feedbacks"] = technical_feedbacks

    state["coding_feedbacks"] = coding_feedbacks

    return state


# ==================================================
# Score Calculation Node
# ==================================================

def score_node(state: InterviewState):

    def avg(feedbacks):

        if not feedbacks:
            return 0.0

        scores = [
            f.get("overall_score", 0)
            for f in feedbacks
        ]

        return round(
            sum(scores) / len(scores),
            2
        )

    hr_score = avg(
        state.get("hr_feedbacks", [])
    )

    technical_score = avg(
        state.get("technical_feedbacks", [])
    )

    coding_score = avg(
        state.get("coding_feedbacks", [])
    )

    overall_score = round(
        (
            hr_score +
            technical_score +
            coding_score
        ) / 3,
        2
    )

    state["hr_score"] = hr_score

    state["technical_score"] = technical_score

    state["coding_score"] = coding_score

    state["overall_score"] = overall_score

    return state


# ==================================================
# Human Review Node
# ==================================================

def human_review_node(state: InterviewState):

    overall_score = state.get(
        "overall_score",
        0
    )

    if overall_score < 5:

        state[
            "human_review_required"
        ] = True

    else:

        state[
            "human_review_required"
        ] = False

    return state


# ==================================================
# Report Generation Node
# ==================================================

def report_node(state: InterviewState):

    report = report_agent.generate_report(
        resume_data=state["resume_data"],
        hr_feedbacks=state["hr_feedbacks"],
        technical_feedbacks=state[
            "technical_feedbacks"
        ],
        coding_feedbacks=state[
            "coding_feedbacks"
        ]
    )

    state["final_report"] = report

    state["interview_completed"] = True

    return state


# ==================================================
# End Node
# ==================================================

def end_node(state: InterviewState):

    print(
        "Interview Completed Successfully"
    )

    return state