
def build_feedback_prompt(question, answer, question_type):
    return f"""
You are an expert interview evaluator.

Question Type:
{question_type}

Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer on:

1. Communication Skills (0-10)
2. Technical Accuracy (0-10)
3. Problem Solving (0-10)
4. Confidence (0-10)
5. Completeness (0-10)

Calculate Overall Score.

Return ONLY valid JSON.

Output Format:

{{
    "overall_score": 8.5,
    "communication": 8,
    "technical_accuracy": 9,
    "problem_solving": 8,
    "confidence": 8,
    "completeness": 9,

    "strengths": [
        "Good technical understanding"
    ],

    "weaknesses": [
        "Need more examples"
    ],

    "feedback": "Strong answer with good explanation.",

    "improvement_suggestions": [
        "Add practical examples",
        "Explain edge cases"
    ]
}}
"""
