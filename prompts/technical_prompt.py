import json


def build_technical_questions_prompt(
    resume_data,
    interview_plan,
    difficulty,
    num_questions,
    skills,
    projects,
    internship,
    focus_area_text
):
    return f"""
You are a Senior Technical Interviewer.

Candidate Resume:

{json.dumps(resume_data, indent=2)}

Interview Plan:

{json.dumps(interview_plan, indent=2)}

Resume-Grounded Focus:
- Skills: {skills}
- Projects: {projects}
- Internship/Experience: {internship}
- Planned Focus Areas: {focus_area_text}

Instructions:

1. Generate ONLY technical interview questions.

2. Questions MUST be based on:
   - Candidate skills
   - Candidate projects
   - Internship experience
   - Focus areas

3. Cover relevant concepts from the uploaded resume.
4. Every question must mention or clearly test at least one resume skill, project, internship, or focus area.
5. Avoid generic questions when a resume-specific question can be asked.

6. Mix:
   - Conceptual Questions
   - Scenario Based Questions
   - Project Based Questions

7. Difficulty:
   {difficulty}

8. Number of Questions:
   {num_questions}

9. Return ONLY valid JSON.

Output Format:

{{
    "questions": [
        {{
            "id": 1,
            "category": "Python",
            "difficulty": "Medium",
            "resume_basis": "Python skill from uploaded resume",
            "question": "In your Python project, how would you structure reusable logic and why?"
        }}
    ]
}}
"""


def build_technical_evaluation_prompt(question, answer):
    return f"""
You are an expert Technical Interview Evaluator.

Question:
{question}

Candidate Answer:
{answer}

Evaluate on:

1. Technical Accuracy
2. Completeness
3. Clarity
4. Confidence

Return ONLY JSON.

Format:

{{
    "score": 8,
    "feedback": "Good understanding of concepts.",
    "strengths": [
        "Strong technical explanation"
    ],
    "improvements": [
        "Add real-world examples"
    ]
}}
"""
