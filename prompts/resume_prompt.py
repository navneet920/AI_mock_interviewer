
def build_resume_prompt(resume_text):
    return f"""
You are an expert Resume Parsing System.

Extract information from the resume and return ONLY one valid JSON object.

Strict rules:
- Return raw JSON only. Do not use markdown, code fences, comments, or explanations.
- The response must start with {{ and end with }}.
- Use double quotes for every JSON key and string value.
- If information is missing, return an empty string "" or an empty array [].
- Keep arrays as arrays of concise strings.
- Do not invent information that is not present in the resume.

Required JSON schema:
{{
    "name": "",
    "summary": "",
    "skills": [],
    "education": [],
    "projects": [],
    "internship": [],
    "certifications": [],
    "achievements": []
}}

Resume text:
{resume_text}
"""
