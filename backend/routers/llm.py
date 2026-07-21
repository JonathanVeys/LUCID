from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pydantic_core import ErrorDetails
from dotenv import load_dotenv
from openai import OpenAI
import os
from pathlib import Path
from sqlalchemy import create_engine
import time
import json

from backend.services.inject import inject_spec
from backend.schema.introspect import load_schema, format_schema_for_prompt, format_vocab_for_prompt
from backend.validation.validate import evaluate_response
from backend.validation.component_validation.parse_model_response import parse_model_response


load_dotenv()

class QueryRequest(BaseModel):
    query: str


PARENT_PATH = Path(__file__).parent.parent
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    db_schema = load_schema(engine)

router = APIRouter(prefix="/api")

_template = (PARENT_PATH / "prompts/system_prompt.txt").read_text(encoding="utf-8")
SYSTEM_PROMPT = (
    _template
    .replace("{DATABASE_SCHEMA}", format_schema_for_prompt(engine))  
    .replace("{COLUMN_INFO}", format_vocab_for_prompt(engine))
)

client = OpenAI(
    api_key=os.environ["ELM_API_KEY"]
)


def build_initial_prompt(prompt: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

def build_healing_prompt(errors: list[str]|list[ErrorDetails]|str) -> str:
    """Format validation/parse errors into a re-prompt for the model.

    The model's previous (faulty) reply is already in the conversation as the
    preceding assistant message, so this only needs to state what was wrong and
    what to do — it does not need to repeat the faulty spec back.
    """
    bullets = "\n".join(f"- {e}" for e in errors)
    return (
        "Your previous response did not pass validation. "
        "Fix the following problems and return the corrected specification "
        "as raw JSON only — no markdown, no code fences, no commentary:\n"
        f"{bullets}"
    )

def inference(query, temperature:float=1, model="gpt-4-turbo"):
    """
    API endpoint for prompting the model.
    Input:  query.query (str) — the model query
    Output: dict with the model's response text
    Raises: HTTPException on upstream or internal failure
    """
    try:
        res = client.chat.completions.create(
            messages=query, 
            model=model,
            temperature=temperature
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail="Upstream model error")

    if not res.choices:
        raise HTTPException(status_code=502, detail="Empty response from model")

    choice = res.choices[0]
    content = choice.message.content
    if not content:
        raise HTTPException(status_code=502, detail="Model returned no content")

    return content




def generate_validated_spec(query:str, db_schema=db_schema, MAX_RETRY=3) -> tuple[dict, list[dict]]:
    '''
    
    '''
    print(f"INFO: generate_validated_spec started | query={query!r}")

    messages = build_initial_prompt(query)
    attempts = []
    last_errors = []

    for attempt in range(MAX_RETRY+1):
        start_time = time.perf_counter()
        print(f"INFO: Inference attempt {attempt}" if attempt>0 else f"INFO: Initial inference")
        content = inference(messages)
        spec, err = parse_model_response(content)

        if spec and not err:
            ok, err = evaluate_response(spec, db_schema)
            if ok:
                if spec.get("answerable"):
                    spec, err = inject_spec(spec, engine)

                if not err and spec:
                    end_time = time.perf_counter()
                    execution_time = end_time - start_time

                    attempts.append({"attempt": attempt, "outcome": "success", "error_type": None, "error_message": None, "inference_time":execution_time})
                    print(f"INFO: Inference attempt {attempt}" if attempt>0 else f"INFO: Initial inference - Validation and injection passed successfully")
                    return spec, attempts  
            
        last_errors=err

        end_time = time.perf_counter()
        execution_time = end_time - start_time
        attempts.append({
            "attempt": attempt,
            "outcome": "fail",
            "error_type": last_errors[0].type,
            "error_message": str(err),
            "inference_time":execution_time
        })

        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": build_healing_prompt(str(err[0]))}) 

        print(f"WARNING: attempt {attempt} failed | Type: {last_errors[0].type} | Details: {last_errors[0].details} | Location: {last_errors[0].location}")

    return {"answerable":False, "reason":last_errors}, attempts



@router.post("/generate")
async def handle_query(query: QueryRequest) -> dict:
    """
    API endpoint for prompting the model.
    Input:  query.query (str) — the model query
    Output: dict with the model's response text
    Raises: HTTPException on upstream or internal failure
    """
    spec, attempts = generate_validated_spec(query.query)
    # try:
    #     print(json.dumps(spec, indent=2))
    # except TypeError as e:
    #     print(f"Could not print spec")
    return {"spec": spec, "attempts":attempts}

     
