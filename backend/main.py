from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.llm import router as query_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://lucid-frontend-udqf.onrender.com",  # the site you open in the browser
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    query_router
)

@app.get("/health")
def root():
    return {"status": "ok"}