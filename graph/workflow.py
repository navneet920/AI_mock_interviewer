from langgraph.graph import (
    StateGraph,
    START,
    END
)

from state.interview_state import (
    InterviewState
)

from graph.nodes import (
    resume_node,
    planner_node,
    hr_node,
    technical_node,
    coding_node,
    collect_questions_node,
    feedback_node,
    score_node,
    human_review_node,
    report_node
)


# =====================================
# Build Graph
# =====================================

def build_graph():

    workflow = StateGraph(
        InterviewState
    )

    # =====================================
    # Register Nodes
    # =====================================

    workflow.add_node(
        "resume_node",
        resume_node
    )

    workflow.add_node(
        "planner_node",
        planner_node
    )

    workflow.add_node(
        "hr_node",
        hr_node
    )

    workflow.add_node(
        "technical_node",
        technical_node
    )

    workflow.add_node(
        "coding_node",
        coding_node
    )

    workflow.add_node(
        "collect_questions_node",
        collect_questions_node
    )

    workflow.add_node(
        "feedback_node",
        feedback_node
    )

    workflow.add_node(
        "score_node",
        score_node
    )

    workflow.add_node(
        "human_review_node",
        human_review_node
    )

    workflow.add_node(
        "report_node",
        report_node
    )

    # =====================================
    # Workflow Edges
    # =====================================

    workflow.add_edge(
        START,
        "resume_node"
    )

    workflow.add_edge(
        "resume_node",
        "planner_node"
    )

    workflow.add_edge(
        "planner_node",
        "hr_node"
    )

    workflow.add_edge(
        "hr_node",
        "technical_node"
    )

    workflow.add_edge(
        "technical_node",
        "coding_node"
    )

    workflow.add_edge(
        "coding_node",
        "collect_questions_node"
    )

    workflow.add_edge(
        "collect_questions_node",
        "feedback_node"
    )

    workflow.add_edge(
        "feedback_node",
        "score_node"
    )

    workflow.add_edge(
        "score_node",
        "human_review_node"
    )

    workflow.add_edge(
        "human_review_node",
        "report_node"
    )

    workflow.add_edge(
        "report_node",
        END
    )

    return workflow.compile()