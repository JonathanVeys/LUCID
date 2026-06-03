from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.llm import router as query_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(
    query_router
)

@app.get("/")
def root():
    return {"message": "GUIDE is running"}