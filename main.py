from fastapi import FastAPI

from api.interview_routes import router


app = FastAPI(
    title="AI Mock Interviewer"
)

app.include_router(router)


@app.get("/")
def home():

    return {
        "message":
            "AI Mock Interviewer Running"
    }