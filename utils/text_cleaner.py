import re


def clean_resume_text(text: str) -> str:
    """Normalize extracted resume text without removing useful resume content."""
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
