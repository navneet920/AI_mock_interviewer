import json


def build_hr_questions_prompt(
    resume_data,
    difficulty,
    num_questions,
    skills,
    projects,
    internship,
    education
):
    return f"""
You are a professional HR interviewer.

Candidate Resume:

{json.dumps(resume_data, indent=2)}

Interview Details:
- Difficulty: {difficulty}
- Number of Questions: {num_questions}
- Resume Skills: {skills}
- Resume Projects: {projects}
- Resume Internship/Experience: {internship}
- Resume Education: {education}

Instructions:

1. Generate personalized HR questions.
2. Use candidate's:
   - Education
   - Projects
   - Internship/Experience
   - Skills
   - Career Goals

3. Include:
   - Introduction Questions
   - Behavioral Questions
   - Situational Questions
   - Teamwork Questions
   - Strength & Weakness Questions
   - Career Goal Questions

4. Every question must clearly connect to at least one resume detail when possible.
5. Do not ask generic questions if a resume-specific version can be asked.

6. Return ONLY valid JSON.

Output Format:

{{
    "questions": [
        {{
            "id": 1,
            "category": "Introduction",
            "resume_basis": "Python project",
            "question": "Tell me about yourself and how your Python project shaped your career goals."
        }}
    ]
}}
"""
