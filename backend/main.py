from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.llm import router as query_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lucid-6kv9.onrender.com"],  # your static site URL
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    query_router
)

@app.get("/")
def root():
    return {"message": "LUCID is running"}