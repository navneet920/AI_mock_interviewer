import json

from prompts.technical_prompt import (
    build_technical_evaluation_prompt,
    build_technical_questions_prompt,
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


class TechnicalAgent:

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
            .get("technical", 5)
        )

        difficulty = interview_plan.get(
            "difficulty",
            "Medium"
        )

        focus_areas = interview_plan.get(
            "focus_areas",
            []
        )
        skills = _join_resume_items(resume_data.get("skills", []))
        projects = _join_resume_items(resume_data.get("projects", []))
        internship = _join_resume_items(
            resume_data.get("internship", [])
            or resume_data.get("experience", [])
        )
        focus_area_text = _join_resume_items(focus_areas)

        prompt = build_technical_questions_prompt(
            resume_data,
            interview_plan,
            difficulty,
            num_questions,
            skills,
            projects,
            internship,
            focus_area_text
        )

        response = self.llm.invoke(prompt)

        content = response.content.strip()

        # Remove markdown if model returns it
        content = content.replace("```json", "")
        content = content.replace("```", "")

        try:
            return json.loads(content)

        except Exception as e:
            skill_text = skills or "the main skills listed in the uploaded resume"
            project_text = projects or "one of the projects in the uploaded resume"
            internship_text = internship or "the candidate's practical experience"
            fallback_questions = [
                f"Explain the most important concept you used from {skill_text}.",
                f"Describe the architecture of {project_text}.",
                f"How would you debug a production issue related to {project_text}?",
                f"What technical tradeoff did you make while working with {skill_text}?",
                f"How would you make code from {project_text} more maintainable?",
                f"How would you optimize a slow feature in {project_text}?",
                f"How did you validate correctness while using {skill_text}?",
                f"Explain an API, model, or database decision from {project_text}.",
                f"What reliability or security concerns apply to {project_text}?",
                f"How would you choose between two approaches while using {skill_text}?",
                f"Explain how you handled errors in {project_text}.",
                f"How would you improve scalability in {project_text}?",
                f"What testing strategy would you use for work related to {skill_text}?",
                f"How do you review code quality in projects like {project_text}?",
                f"What technical challenge did you solve during {internship_text}?",
                f"How would you monitor application health for {project_text}?",
                f"Which data structure, algorithm, or design pattern fits {project_text}, and why?",
                f"How do you document decisions while working with {skill_text}?",
                f"What would you refactor in {project_text}?",
                f"How do you plan to deepen your knowledge of {skill_text}?"
            ]

            return {
                "questions": [
                    {
                        "id": index,
                        "category": "Resume Based",
                        "difficulty": difficulty,
                        "resume_basis": "Uploaded resume",
                        "question": question
                    }
                    for index, question in enumerate(
                        fallback_questions[:num_questions],
                        start=1
                    )
                ],
                "error": str(e),
                "raw_output": content
            }

    def evaluate_answer(
            self,
            question: str,
            answer: str
    ):

        prompt = build_technical_evaluation_prompt(question, answer)

        response = self.llm.invoke(prompt)

        content = response.content.strip()

        content = content.replace("```json", "")
        content = content.replace("```", "")

        try:
            return json.loads(content)

        except Exception:

            return {
                "score": 0,
                "feedback": "Unable to evaluate answer."
            }
