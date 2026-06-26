from api.interview_context import router

# Import endpoint modules so they register their routes on the shared router.
from api import upload_resume_route  # noqa: F401
from api import select_round_route  # noqa: F401
from api import submit_answer_route  # noqa: F401
from api import submit_interview_route  # noqa: F401
from api import human_review_route  # noqa: F401
from api import download_report_route  # noqa: F401
from api import get_session_status_route  # noqa: F401
