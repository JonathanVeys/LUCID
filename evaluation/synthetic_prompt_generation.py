import json
from pathlib import Path
from pydantic import ValidationError, BaseModel
import pandas as pd
from tqdm import tqdm

from evaluation.table_schema import PromptTableSchema, PromptCategory
from evaluation.prompt_descriptions import CATEGORY_DEFS
from backend.routers.llm import inference, db_schema
from backend.validation.component_validation.parse_json import parse_model_json


N_PROMPTS = 25
N_VAGUE = 5
N_SPELLING = 5
N_UNANSWERABLE = 2
OUTPUT_SCHEMA = json.dumps(PromptTableSchema.model_json_schema(), indent=2)
PARENT_PATH = Path(__file__).parent
USER_COLUMNS = [
    "reported_date", "incident_date", "location_country", "location_region",
    "crime_type", "victim_count", "victim_nationality",
    "perpetrator_nationality", "summary", "confidence",
]

INCIDENTS = db_schema.tables["incidents"]
DB_SCHEMA = "\n".join(
    f"- {c.name} ({c.type})"
    for c in INCIDENTS.columns
    if c.name in USER_COLUMNS
)

class PromptBatch(BaseModel):
    prompts: list[PromptTableSchema]  

def render_category(category: PromptCategory) -> str:
    d = CATEGORY_DEFS[category]
    examples = "\n".join(f"- {e}" for e in d.examples)
    return (
        f"Task category: {category.value}\n"
        f"Description: {d.description}\n"
        f"Pro forma: {d.pro_forma}\n"
        f"Examples:\n{examples} \n"
    )

all_rows = []
TEMPLATE = (PARENT_PATH / "prompts/synthetic_prompt_generation_prompt.txt").read_text(encoding="utf-8")   # read once, never mutated
for category in tqdm(PromptCategory, desc="Generating prompts"):
    category_info = render_category(category)
    prompt = (
        TEMPLATE
        .replace("{N}", str(N_PROMPTS))  
        .replace("{N_VAGUE}", str(N_VAGUE))
        .replace("{N_SPELLING}", str(N_SPELLING))
        .replace("{N_UNANSWERABLE}", str(N_UNANSWERABLE))
        .replace("{OUTPUT_SCHEMA}", str(json.dumps(PromptBatch.model_json_schema(), indent=2)))
        .replace("{SCHEMA}", str(DB_SCHEMA))
        .replace("{CATEGORY_BLOCK}", category_info)
    )
    messages = [{"role": "system", "content": prompt}]
    raw_string = inference(messages)
    try:
        batch = PromptBatch.model_validate_json(raw_string)
    except ValidationError as e:
        print(e.errors()) 

    all_rows.extend(p.model_dump(mode="json") for p in batch.prompts)


df = pd.DataFrame(all_rows)
df.insert(0, "prompt_id", range(len(df)))
df["expected_charts"] = df["expected_charts"].apply(json.dumps)  # list column
df.to_csv("evaluation/prompts/synthetic_prompts.csv", index=False)



