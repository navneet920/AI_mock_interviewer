import json

from prompts.planner_prompt import build_planner_prompt


class PlannerAgent:

    def __init__(self, llm):
        self.llm = llm

    def create_interview_plan(self, resume_data: dict):

        prompt = build_planner_prompt(resume_data)

        response = self.llm.invoke(prompt)

        try:
            return json.loads(response.content)

        except Exception as e:

            print("Planner Error:", e)

            return {
                "candidate_level": "Fresher",
                "difficulty": "Medium",
                "question_distribution": {
                    "hr": 3,
                    "technical": 5,
                    "coding": 2
                },
                "focus_areas": [],
                "interview_flow": [
                    "HR",
                    "Technical",
                    "Coding"
                ]
            }

    def create_plan(self, resume_data: dict):
        return self.create_interview_plan(resume_data)
# if __name__=="__main__":
#     from services.llm_service import LLMService
#     from agents.planner_agent import PlannerAgent
#
#     llm = LLMService.get_llm()
#
#     planner = PlannerAgent(llm)
#
#     resume_json = {
#         "name": "Navneet Kumar",
#         "skills": [
#             "Python",
#             "SQL",
#             "Machine Learning",
#             "Deep Learning",
#             "Power BI"
#         ],
#         "projects": [
#             "Quora Duplicate Question Detection",
#             "Real Estate Intelligence System",
#             "Cattle Breed Classification"
#         ],
#         "experience": [
#             "Data Science Intern"
#         ]
#     }
#
#     result = planner.create_interview_plan(
#         resume_json
#     )
#
#     print(result)
