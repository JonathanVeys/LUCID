from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pydantic_core import ErrorDetails
from dotenv import load_dotenv
from openai import OpenAI
import os
from pathlib import Path
from sqlalchemy import create_engine

from backend.services.inject import inject_data
from backend.schema.introspect import load_schema
from backend.validation.validate import validate
from backend.validation.component_validation.parse_json import parse_model_json

load_dotenv()


class QueryRequest(BaseModel):
    query: str


DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    db_schema = load_schema(engine)


PARENT_PATH = Path(__file__).parent.parent
SYSTEM_PROMPT = (PARENT_PATH / "prompts/system_prompt.txt").read_text()


router = APIRouter(prefix="/api")


client = OpenAI(
    api_key=os.environ["ELM_API_KEY"]
)


def build_initial_prompt(prompt: str) -> list[dict]:
    augmented_prompt = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    return augmented_prompt

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

def inference(query):
    """
    API endpoint for prompting the model.
    Input:  query.query (str) — the model query
    Output: dict with the model's response text
    Raises: HTTPException on upstream or internal failure
    """
    try:
        res = client.chat.completions.create(
            messages=query, 
            model="gpt-4-turbo",
            temperature=0
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



def generate_validated_spec(query: str, schema=db_schema, max_retry: int = 3):
    print(f"INFO: generate_validated_spec started | query={query!r} | max_retry={max_retry}")
    messages = build_initial_prompt(query)        # the conversation, starts with system + user
    last_errors = None
    for attempt in range(max_retry):
        print(f"INFO: attempt {attempt + 1}/{max_retry} | calling model")
        content = inference(messages)               # iteration 1 = initial; later = retry
        print(f"INFO: attempt {attempt + 1}/{max_retry} | model returned {len(content)} chars")
        raw, errors = parse_model_json(content)
        if not errors:
            print(f"INFO: attempt {attempt + 1}/{max_retry} | JSON parsed OK")
            if raw:
                if "answerable" not in raw.keys():
                    errors = ["Response must include the 'answerable' field."]
                elif not raw["answerable"]:
                    return raw, None
                else: 
                    spec, errors = validate(raw["vis_spec"], schema)
                    if not errors:
                        print(f"INFO: attempt {attempt + 1}/{max_retry} | validation passed — returning spec")
                        return {"answerable":True, "vis_spec":spec.model_dump()}, None #type:ignore
                    print(f"INFO: attempt {attempt + 1}/{max_retry} | validation failed with {len(errors)} error(s)")
        else:
            print(f"INFO: attempt {attempt + 1}/{max_retry} | JSON parse failed")
        # any failure (parse OR validate) lands here
        print(f"WARNING: attempt {attempt + 1}/{max_retry} | errors fed back to model: {errors}")
        last_errors = errors
        if errors:
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": build_healing_prompt(errors)})
    print(f"WARNING: pipeline exhausted after {max_retry} attempts — returning errors: {last_errors}")
    return None, last_errors                          # exhausted


def generate_dashboard_spec(query:QueryRequest, schema=db_schema, max_retry: int = 3):
    '''
    
    '''
    spec, errors = generate_validated_spec(query.query)

    if errors:
        return None, errors
    else:
        spec = inject_data(spec, engine)
        return spec, None

@router.post("/generate")
async def handle_query(query: QueryRequest) -> dict:
    """
    API endpoint for prompting the model.
    Input:  query.query (str) — the model query
    Output: dict with the model's response text
    Raises: HTTPException on upstream or internal failure
    """
    spec, errors = generate_dashboard_spec(query)

    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    if not spec:
        raise ValueError("Spec was empty")  
    return {"spec": spec}

     

