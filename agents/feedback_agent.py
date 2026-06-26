import json

from prompts.feedback_prompt import build_feedback_prompt


class FeedbackAgent:

    def __init__(self, llm):
        self.llm = llm

    def evaluate_answer(
            self,
            question: str,
            answer: str,
            question_type: str
    ):

        prompt = build_feedback_prompt(question, answer, question_type)

        response = self.llm.invoke(prompt)

        content = response.content.strip()

        content = content.replace("```json", "")
        content = content.replace("```", "")

        try:
            return json.loads(content)

        except Exception as e:

            return {
                "overall_score": 0,
                "communication": 0,
                "technical_accuracy": 0,
                "problem_solving": 0,
                "confidence": 0,
                "completeness": 0,
                "strengths": [],
                "weaknesses": [],
                "feedback": "Evaluation failed",
                "improvement_suggestions": [],
                "error": str(e)
            }