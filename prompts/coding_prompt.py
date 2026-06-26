import json


def build_coding_questions_prompt(
    resume_data,
    interview_plan,
    difficulty,
    num_questions,
    skills,
    projects,
    internship
):
    return f"""
You are a Senior Coding Interviewer.

Candidate Resume:

{json.dumps(resume_data, indent=2)}

Interview Plan:

{json.dumps(interview_plan, indent=2)}

Resume-Grounded Coding Context:
- Skills: {skills}
- Projects: {projects}
- Internship/Experience: {internship}

Instructions:

1. Generate coding questions based on:
   - Programming Languages
   - Skills
   - Projects
   - Internship Experience

2. Generate practical coding challenges that match the uploaded resume.

3. If candidate has:
   - Python -> Python coding problems
   - SQL -> SQL queries
   - Machine Learning -> ML case studies
   - Deep Learning -> DL scenarios
   - Data Science -> Data preprocessing challenges

4. Every coding question must be connected to a resume skill, project, or experience.
5. Prefer practical tasks similar to the candidate's uploaded resume projects.

6. Difficulty:
   {difficulty}

7. Number of Questions:
   {num_questions}

8. Return ONLY valid JSON.

Output Format:

{{
    "questions":[
        {{
            "id":1,
            "category":"Python",
            "difficulty":"Medium",
            "resume_basis":"Python skill from uploaded resume",
            "question":"Write a Python function similar to your resume project needs that finds duplicate records in a list.",
            "expected_skills":["Python","Data Structures"]
        }}
    ]
}}
"""


def build_coding_evaluation_prompt(question, candidate_solution):
    return f"""
You are an Expert Coding Interview Evaluator.

Coding Question:

{question}

Candidate Solution:

{candidate_solution}

Evaluate:

1. Correctness
2. Code Quality
3. Time Complexity
4. Space Complexity
5. Best Practices

Return ONLY valid JSON.

Format:

{{
    "score": 8,
    "feedback": "Good solution.",
    "strengths": [
        "Correct logic"
    ],
    "improvements": [
        "Optimize time complexity"
    ]
}}
"""
