from pathlib import Path
import httpx
from tqdm import tqdm
import random

import pandas as pd
import json


API_URL="http://127.0.0.1:8000/api/generate"
ROOT_PATH = Path(__file__)
while True:
    if (ROOT_PATH/"evaluation").is_dir():
        ROOT_PATH = ROOT_PATH
        break
    else:
        ROOT_PATH = ROOT_PATH.parent
with open(ROOT_PATH/"evaluation/prompts/prompts.json") as f:
    PROMPTS=json.load(f)
WRITE_PATH = ROOT_PATH/"evaluation/results"

def parse_attempt(attempt:dict, prompt_id:int) -> dict:
    """
    
    """
    idx = attempt.get("attempt")
    outcome = attempt.get("outcome")
    error_type = attempt.get("error_type")
    errror_msg = attempt.get("error_message")
    inf_time = attempt.get("inference_time")

    return {
        "prompt_id":prompt_id,
        "attempt_num":idx,
        "outcome":outcome,
        "error_code":error_type,
        "error_msg":errror_msg,
        "inference_time":inf_time
    }

def parse_result(spec:dict, attempts:dict, prompt_id:int) -> dict:
    """
    
    """
    success_attempt=None
    for idx,attempt in enumerate(attempts, 1):
        if attempt["outcome"]=="success":
            success_attempt=idx

    vis_spec=spec.get("vis_spec", {})
    total_inf_time = sum([float(a["inference_time"]) for a in attempts])
    chosen_layout=vis_spec.get("layout_mode")
    answerable=spec.get("answerable")
    succeeded = any(a["outcome"] == "success" for a in attempts)


    return {
        "prompt_id":prompt_id,
        "succeeded":succeeded,
        "success_attempt":success_attempt,
        "total_time":total_inf_time,
        "chosen_layout":chosen_layout,
        "chosen_charts":None,
        "chosen_answerable": answerable,
        "vis_spec":vis_spec
    }   


def main(PROMPTS:list) -> None:
    """
    
    """
    attempts_table=[]
    results_table=[]
    with httpx.Client(timeout=300) as client:
        for prompt_data in tqdm(PROMPTS, desc="Processing evaluation prompts: "):
            prompt_id       =prompt_data["prompt_id"]
            prompt          =prompt_data["prompt"]
            prompt_category =prompt_data["prompt_category"]
            vague_language  =prompt_data["vague_language"]
            spelling_errors =prompt_data["spelling_errors"]
            answerable      =prompt_data["answerable"]
            complexity      =prompt_data["complexity"]
            expected_layout =prompt_data["expected_layout"]
            expected_charts =prompt_data["expected_charts"]

            try:
                body = client.post(API_URL, json={"query": prompt}).json()
            except Exception as e:
                body = {"spec": None, "attempts": [], "_error": repr(e)}
            
            spec=body.get("spec", {})
            attempts=body.get("attempts", [])

            if spec and attempts:
                results_table.append(parse_result(spec, attempts, prompt_id))
                for attempt in attempts:
                    parsed_attempt = parse_attempt(attempt, prompt_id)
                    attempts_table.append(parsed_attempt)


    results_df = pd.DataFrame(results_table)
    attempts_df = pd.DataFrame(attempts_table)

    results_df.to_csv(WRITE_PATH/"results.csv")
    attempts_df.to_csv(WRITE_PATH/"attempts.csv")
        

if __name__ == "__main__":
    # random.seed(1)
    main(random.sample(PROMPTS, 25))
