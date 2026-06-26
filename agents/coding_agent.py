import json

from prompts.coding_prompt import (
    build_coding_evaluation_prompt,
    build_coding_questions_prompt,
)


def _join_resume_items(items):
    if not items:
        return ""

    if isinstance(items, list):
        values = []

        for item in items:
            if isinstance(item, dict):
                values.append(", ".join(str(value) for value in item.values() if value))
            else:
                values.append(str(item))

        return "; ".join(value for value in values if value)

    return str(items)


class CodingAgent:

    def __init__(self, llm):
        self.llm = llm

    def generate_questions(
            self,
            resume_data: dict,
            interview_plan: dict
    ):

        num_questions = (
            interview_plan
            .get("question_distribution", {})
            .get("coding", 3)
        )

        difficulty = interview_plan.get(
            "difficulty",
            "Medium"
        )
        skills = _join_resume_items(resume_data.get("skills", []))
        projects = _join_resume_items(resume_data.get("projects", []))
        internship = _join_resume_items(
            resume_data.get("internship", [])
            or resume_data.get("experience", [])
        )

        prompt = build_coding_questions_prompt(
            resume_data,
            interview_plan,
            difficulty,
            num_questions,
            skills,
            projects,
            internship
        )

        response = self.llm.invoke(prompt)

        content = response.content.strip()

        content = content.replace("```json", "")
        content = content.replace("```", "")

        try:
            return json.loads(content)

        except Exception as e:
            skill_text = skills or "the programming skills listed in the uploaded resume"
            project_text = projects or "one of the uploaded resume projects"
            internship_text = internship or "the candidate's practical experience"
            fallback_questions = [
                f"Write a function for {project_text} that removes duplicate records from a list.",
                f"Write a function using {skill_text} to count item frequency in project data.",
                f"Write a function for {project_text} that validates and cleans missing values.",
                f"Write a function using {skill_text} to merge two sorted result lists.",
                f"Write a function for {project_text} that finds the top N records by score.",
                f"Write a function using {skill_text} to group records by category.",
                f"Write a function for {project_text} that checks whether input text is valid.",
                f"Write a function using {skill_text} to parse rows from a CSV-like string.",
                f"Write a function for {project_text} that calculates summary statistics.",
                f"Write a function using {skill_text} to compare two dictionaries of metrics.",
                f"Write a function for {project_text} that chunks data into batches.",
                f"Write a function using {skill_text} to find common elements between two datasets.",
                f"Write a function for {project_text} that ranks records after applying a filter.",
                f"Write a function using {skill_text} to normalize text before processing.",
                f"Write a function for {project_text} that detects invalid values.",
                f"Write a function inspired by {internship_text} that logs failed records.",
                f"Write a function using {skill_text} to rotate or reorder a list of tasks.",
                f"Write a function for {project_text} that creates a simple in-memory cache.",
                f"Write a function using {skill_text} to flatten nested project data.",
                f"Write a function for {project_text} that returns both result and error details."
            ]

            return {
                "questions": [
                    {
                        "id": index,
                        "category": "Resume Based Coding",
                        "difficulty": difficulty,
                        "resume_basis": "Uploaded resume",
                        "question": question,
                        "expected_skills": [skill_text]
                    }
                    for index, question in enumerate(
                        fallback_questions[:num_questions],
                        start=1
                    )
                ],
                "error": str(e),
                "raw_output": content
            }

    def evaluate_solution(
            self,
            question: str,
            candidate_solution: str
    ):

        prompt = build_coding_evaluation_prompt(question, candidate_solution)

        response = self.llm.invoke(prompt)

        content = response.content.strip()

        content = content.replace("```json", "")
        content = content.replace("```", "")

        try:
            return json.loads(content)

        except Exception:

            return {
                "score": 0,
                "feedback": "Evaluation failed."
            }
