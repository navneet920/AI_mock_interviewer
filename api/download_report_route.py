import os

from fastapi import HTTPException
from fastapi.responses import FileResponse

from api.interview_context import router, _get_session


@router.get("/report/{interview_id}")
async def download_report(interview_id: str):
    session = _get_session(interview_id)
    report_path = session.get("report_path")

    if not report_path or not os.path.exists(report_path):
        raise HTTPException(
            status_code=404,
            detail="Report not found. Submit the interview first."
        )

    return FileResponse(
        report_path,
        media_type="application/pdf",
        filename=f"{interview_id}_interview_report.pdf"
    )
