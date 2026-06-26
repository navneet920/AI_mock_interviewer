import json
import os
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class PDFService:

    @staticmethod
    def generate_interview_report(interview_id: str, report_data: dict) -> str:
        os.makedirs("reports", exist_ok=True)

        file_path = os.path.join(
            "reports",
            f"{interview_id}_report.pdf"
        )

        pdf = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        y = height - 50

        def write_line(line: str = ""):
            nonlocal y
            if y < 50:
                pdf.showPage()
                y = height - 50
            pdf.drawString(50, y, line[:95])
            y -= 16

        pdf.setTitle("AI Mock Interview Report")
        pdf.setFont("Helvetica-Bold", 16)
        write_line("AI Mock Interview Report")
        pdf.setFont("Helvetica", 10)
        write_line(f"Generated At: {datetime.utcnow().isoformat()} UTC")
        write_line(f"Interview ID: {interview_id}")
        write_line()

        for line in json.dumps(report_data, indent=2).splitlines():
            write_line(line)

        pdf.save()

        return file_path
