from pathlib import Path
import pandas as pd
from tqdm import tqdm

from backend.routers.llm import generate_validated_spec

PARENT_PATH = Path(__file__)
while True:
    if (PARENT_PATH/"evaluation").is_dir():
        ROOT_PATH = PARENT_PATH
        break
    else:
        PARENT_PATH = PARENT_PATH.parent


SYNTEHTIC_PROMPTS_PATH = ROOT_PATH/"evaluation/prompts/synthetic_prompts.csv"
PROMPTS = pd.read_csv(SYNTEHTIC_PROMPTS_PATH)

attempt_rows = []
result_rows = []

counter = 0
for idx, row in tqdm(PROMPTS.iterrows(), total=len(PROMPTS), desc="Processing prompts"):
    if row["complexity"] not in [4,5]:
        continue
    counter += 1
    if counter == 15:
        break

    prompt_id = row["prompt_id"]
    try:
        spec, errors, attempts = generate_validated_spec(row["prompt"], debug=False)
    except Exception as e:
        result_rows.append({"prompt_id": prompt_id, "succeeded": False,
                            "success_attempt": None, "crashed": True, "crash_msg": str(e)})
        continue

    for a in attempts:
        a["prompt_id"] = prompt_id
    attempt_rows.extend(attempts)

    # the results row — this is what quality scoring joins against
    succeeded = spec is not None
    charts = spec.get("vis_spec", {}).get("charts", []) if succeeded and spec.get("answerable") else []
    result_rows.append({
        "prompt_id": prompt_id,
        "succeeded": succeeded,
        "success_attempt": next((a["attempt"] for a in attempts if a["outcome"] == "success"), None),
        "n_attempts": len(attempts),
        "chosen_answerable": spec.get("answerable") if succeeded else None,
        "chosen_layout": spec.get("vis_spec", {}).get("layout_mode") if (succeeded and spec.get("answerable")) else None,
        "chosen_charts": [c["vega_lite"].get("mark") for c in charts],
        "n_charts": len(charts),
        "vis_spec": spec,     # keep the clean spec for judge scoring + examples
    })
print(pd.DataFrame(attempt_rows))
print(pd.DataFrame(result_rows))

    