from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pydantic_core import ErrorDetails
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from pathlib import Path
from sqlalchemy import create_engine

from backend.services.inject import inject_data
from backend.schema.introspect import load_schema, format_schema_for_prompt, format_vocab_for_prompt
from backend.validation.validate import validate
from backend.validation.component_validation.parse_json import parse_model_json


import time
import functools

def timing_val(func):
    """Decorator that measures execution time and returns the function's value."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        # Execute the original function and store its output
        result = func(*args, **kwargs)
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        print(f"Function '{func.__name__}' took {execution_time:.6f} seconds to execute.")
        
        # Return the original value so the program can continue as expected
        return result
    return wrapper




load_dotenv()

class QueryRequest(BaseModel):
    query: str


PARENT_PATH = Path(__file__).parent.parent
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    db_schema = load_schema(engine)


router = APIRouter(prefix="/api")

#On backend boot, inject database information into system prompt

_template = (PARENT_PATH / "prompts/system_prompt_final.txt").read_text(encoding="utf-8")
SYSTEM_PROMPT = (
    _template
    .replace("DATABASE_SCHEMA", format_schema_for_prompt(engine))  
    .replace("COLUMN_INFO", format_vocab_for_prompt(engine))
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

def inference(query, temperature:float=1):
    """
    API endpoint for prompting the model.
    Input:  query.query (str) — the model query
    Output: dict with the model's response text
    Raises: HTTPException on upstream or internal failure
    """
    client = OpenAI(
        api_key=os.environ["ELM_API_KEY"]
    )

    try:
        res = client.chat.completions.create(
            messages=query, 
            model="gpt-4-turbo",
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





def evaluate_response(spec, schema=db_schema, debug:bool=False):
    '''
    A function for evaluating a visualisation specification against a predefined schema
    '''
    raw, errors = parse_model_json(spec)
    if errors:  #Check for json syntax errors
        return None, errors
    if not raw:  #Ensure that the model has returned some raw spec
        return None, ["Visualisation specification was empty or unparsable output."]
    if "answerable" not in raw.keys():  #Check if the answerable field is present
        return None, ["Response must include 'answerable' field"]
    if not raw["answerable"]:   #Check if the model has flagged the response as unanswerable
        return raw, None
    if "vis_spec" not in raw.keys(): #Check that the model contains a vis_spec
        return None, ["Response must include 'vis_spec' field"]
    spec, errors = validate(raw["vis_spec"], schema)    #Return syntax and semantic errors from the vis_spec
    if errors:
        return None, errors
    else:
        return raw, None

def generate_validated_spec(query:str, schema=db_schema, MAX_RETRY:int=3):
    '''
    A function for converting a query to a validated visualisation specification
    '''
    print(f"INFO: generate_validated_spec started | query={query!r}")
    messages = build_initial_prompt(query)
    last_errors = None

    for attempt in range(MAX_RETRY + 1):
        print(f"INFO: Inference attempt {attempt}" if attempt>0 else f"INFO: Initial inference")
        content = inference(messages)
        result, errors = evaluate_response(content, schema)

        if not errors and result:
            try:
                inject_data(result, engine)
                print("INFO: validation + injection passed — returning spec")
                return result, None                     
            except Exception as e:
                errors = f"The generated SQL failed to execute: {e}"  

        last_errors = errors
        print(f"WARNING: attempt {attempt} failed: {last_errors}")
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": build_healing_prompt(errors)}) 

    return None, last_errors
    
@timing_val
def generate_dashboard_spec(query:QueryRequest, schema=db_schema, MAX_RETRY: int = 3):
    '''
    A function that takes a validat 
    '''
    spec, errors = generate_validated_spec(query.query, MAX_RETRY=MAX_RETRY)

    if errors:
        return None, errors
    # if "vis_spec" in spec.keys():  #type: ignore
        # spec = inject_data(spec, engine)         #type: ignore
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

     
