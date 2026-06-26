import json

from prompts.hr_prompt import build_hr_questions_prompt


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


class HRAgent:

    def __init__(self, llm):
        self.llm = llm

    def generate_questions(
        self,
        resume_data: dict,
        interview_plan: dict
    ):

        num_questions = interview_plan.get(
            "question_distribution", {}
        ).get("hr", 5)

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
        education = _join_resume_items(resume_data.get("education", []))

        prompt = build_hr_questions_prompt(
            resume_data,
            difficulty,
            num_questions,
            skills,
            projects,
            internship,
            education
        )

        response = self.llm.invoke(prompt)
        content = response.content.strip()
        content = content.replace("```json", "")
        content = content.replace("```", "")

        try:
            return json.loads(content)

        except Exception:
            project_text = projects or "one of your projects"
            skill_text = skills or "your listed skills"
            internship_text = internship or "your academic or practical experience"
            education_text = education or "your education"
            questions = [
                f"Tell me about yourself and connect your answer with {skill_text}.",
                f"Why are you interested in this role based on your work with {project_text}?",
                f"Describe a challenge you faced in {project_text} and what you learned.",
                f"How did {internship_text} prepare you for teamwork and ownership?",
                f"What are your key strengths from {skill_text}, and what area are you improving?",
                f"How does {education_text} support your career goals?",
                f"Tell me about feedback you received while working on {project_text}.",
                f"How do you manage deadlines when working with {skill_text}?",
                f"What motivates you most about the work shown in your resume?",
                f"Why should we consider you for this role based on {project_text}?",
                f"Describe a time you showed ownership during {internship_text}.",
                f"How do you handle disagreement while collaborating on technical or project work?",
                f"What did you learn from {project_text} that improved your professional maturity?",
                f"How do you stay organized when handling tasks related to {skill_text}?",
                f"What kind of work environment helps you perform well with {skill_text}?",
                f"Tell me about a time you adapted to change during {project_text}.",
                f"How do you handle mistakes while working on {skill_text} tasks?",
                f"What are your expectations from your next role after {internship_text}?",
                f"How do you communicate progress while working on {project_text}?",
                f"What would you like to improve in your professional skills beyond {skill_text}?"
            ]

            return {
                "questions": [
                    {
                        "id": index,
                        "category": "Introduction",
                        "resume_basis": "Uploaded resume",
                        "question": question
                    }
                    for index, question in enumerate(
                        questions[:num_questions],
                        start=1
                    )
                ]
            }
