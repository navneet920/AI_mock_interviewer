import json


def build_report_prompt(resume_data, hr_feedbacks, technical_feedbacks, coding_feedbacks):
    return f"""
You are a Senior Hiring Manager.

Candidate Resume:

{json.dumps(resume_data, indent=2)}

HR Feedback:

{json.dumps(hr_feedbacks, indent=2)}

Technical Feedback:

{json.dumps(technical_feedbacks, indent=2)}

Coding Feedback:

{json.dumps(coding_feedbacks, indent=2)}

Your task:

1. Analyze all interview rounds.
2. Calculate overall performance.
3. Identify strengths.
4. Identify weaknesses.
5. Give hiring recommendation.

Recommendation must be one of:

- Strong Hire
- Hire
- Hold
- Reject

Return ONLY valid JSON.

Output Format:

{{
    "overall_score": 8.5,

    "hr_score": 8.0,

    "technical_score": 8.7,

    "coding_score": 8.8,
    "strengths": [
        "Strong Python skills"
    ],

    "weaknesses": [
        "Needs SQL optimization knowledge"
    ],

    "summary":
        "Candidate demonstrated good technical knowledge.",

    "recommendation":
        "Hire"
}}
"""
