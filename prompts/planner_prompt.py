import json


def build_planner_prompt(resume_data):
    return f"""
You are an expert Interview Planner.

Analyze the candidate resume and create an interview plan.

Resume Data:
{json.dumps(resume_data, indent=2)}

Return ONLY valid JSON.
"""
