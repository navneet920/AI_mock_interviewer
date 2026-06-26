import json

from prompts.report_prompt import build_report_prompt


class ReportAgent:

    def __init__(self, llm):
        self.llm = llm

    def generate_report(
            self,
            resume_data: dict,
            hr_feedbacks: list,
            technical_feedbacks: list,
            coding_feedbacks: list
    ):

        prompt = build_report_prompt(
            resume_data,
            hr_feedbacks,
            technical_feedbacks,
            coding_feedbacks
        )

        response = self.llm.invoke(prompt)

        content = response.content.strip()

        content = content.replace("```json", "")
        content = content.replace("```", "")

        try:
            return json.loads(content)

        except Exception:

            return {
                "overall_score": 0,
                "hr_score": 0,
                "technical_score": 0,
                "coding_score": 0,
                "strengths": [],
                "weaknesses": [],
                "summary": "Report generation failed",
                "recommendation": "Hold"
            }