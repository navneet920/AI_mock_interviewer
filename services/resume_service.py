import fitz
from docx import Document

from utils.text_cleaner import clean_resume_text


class ResumeService:

    @staticmethod
    def parse_pdf(file_path: str):

        text = ""

        try:

            with fitz.open(file_path) as pdf:

                for page in pdf:

                    extracted = page.get_text()

                    if extracted:
                        text += extracted + "\n"

            return clean_resume_text(text)

        except Exception as e:

            print(f"PDF Parsing Error: {e}")

            return ""

    @staticmethod
    def parse_docx(file_path: str):

        try:

            doc = Document(file_path)

            text = "\n".join(
                para.text
                for para in doc.paragraphs
                if para.text.strip()
            )

            return clean_resume_text(text)

        except Exception as e:

            print(f"DOCX Parsing Error: {e}")

            return ""

    @staticmethod
    def parse_resume(file_path: str):

        if file_path.endswith(".pdf"):
            return ResumeService.parse_pdf(file_path)

        elif file_path.endswith(".docx"):
            return ResumeService.parse_docx(file_path)

        else:
            raise ValueError(
                "Only PDF and DOCX files are supported."
            )


if __name__ == "__main__":

    resume_text = ResumeService.parse_resume(
        r"C:\Users\Navneet\PycharmProjects\AI_mock_interviewer\uploads\Resume.pdf"
    )

    print("\n===== RESUME TEXT =====\n")
    print(resume_text)
