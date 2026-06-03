from fastapi import APIRouter
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

router = APIRouter(prefix="/api")

@router.post("/query")
async def handle_query(query:QueryRequest) -> dict:
    return {
        "query":query.query,
        "status":"received"
    }