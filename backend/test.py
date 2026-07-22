"""
Run a list of prompts against /generate and write two CSVs.

    python run_prompts.py --url http://127.0.0.1:8000/api/generate
"""

import argparse
import csv
import json
import time
import uuid

import httpx

PROMPTS = [
    "How many trafficking incidents were reported in the United States in 2025?",
    # "Which country reports the most sex trafficking?",
    # "What is the most commonly reported crime type?",
    # "What was the rate of human trafficking in Cambodia last year?",
    # "Which countries report the most pig butchering scams?",
    # "Show me where forced labour is reported around the world",
    # "Map reported trafficking incidents across Southeast Asia",
    # "Compare pig butchering and scam compounds by country and crime type",
    # "How has reporting of scam compounds changed over time?",
    # "What are the most commonly reported crime types?",
    # "Which victim nationalities appear most often in reports?",
    # "How does reported trafficking break down by confidence level?",
    # "Show me the trend in reported incidents across 2016 to 2018",
    # "Give me an overview of trafficking in Southeast Asia",
    # "Tell me everything you can about reported labour exploitation",
    # "Give me a really detailed overview of everything in this dataset",
    # "What can you tell me about who is affected and where?",
    # "Break down trafficking by crime type across every region over time",
    # "Plot incidents over time for each country",
    # "Show me daily trafficking reports in Cambodia for 2024",
    # "What happened in 2022?",
    # "How much online fraud is reported?",
    # "Where are romance scams most reported?",
    # "What are the star signs of trafficking victims?",
    # "How old are the victims and which countries do they come from?",
]


def parse_attempt(a):
    """
    Pull the attempts-table columns out of one attempt object.
    THIS IS THE ONE FUNCTION TO ADJUST once the attempt shape is fixed.
    """
    if not isinstance(a, dict):
        return {"outcome": "unknown", "error_code": None,
                "error_message": None, "inference_time": None}

    errors = a.get("errors") or []
    first = errors[0] if errors else None
    return {
        "outcome": a.get("outcome") or ("failed" if errors else "succeeded"),
        "error_type": (first or {}).get("type"),
        "error_message": (first or {}).get("details"),
        "inference_time": a.get("inference_time"),
    }


def summarise(spec):
    """chosen_layout / chosen_charts / chosen_answerable from the final spec."""
    if not isinstance(spec, dict):
        return None, None, None
    answerable = spec.get("answerable")
    vis = spec.get("vis_spec")
    if not isinstance(vis, dict):
        return None, None, answerable

    charts = vis.get("charts")
    marks = []
    if isinstance(charts, list):
        for c in charts:
            vl = c.get("vega_lite", {}) if isinstance(c, dict) else {}
            mark = vl.get("mark") if isinstance(vl, dict) else None
            marks.append(mark.get("type") if isinstance(mark, dict) else str(mark))
    return vis.get("layout_mode"), "|".join(marks) or None, answerable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000/api/generate")
    ap.add_argument("--timeout", type=float, default=300.0)
    args = ap.parse_args()

    res_f = open("results.csv", "w", newline="")
    att_f = open("attempts.csv", "w", newline="")
    res = csv.DictWriter(res_f, ["prompt_id", "succeeded", "success_attempt",
                                 "total_time", "chosen_layout", "chosen_charts",
                                 "chosen_answerable", "vis_spec"])
    att = csv.DictWriter(att_f, ["prompt_id", "attempt_num", "outcome",
                                 "error_code", "error_message", "inference_time"])
    res.writeheader()
    att.writeheader()

    with httpx.Client(timeout=args.timeout) as client:
        for i, prompt in enumerate(PROMPTS, 1):
            pid = str(uuid.uuid4())
            print(f"[{i}/{len(PROMPTS)}] {prompt[:60]}", flush=True)

            t0 = time.perf_counter()
            try:
                body = client.post(args.url, json={"query": prompt}).json()
            except Exception as e:
                body = {"spec": None, "attempts": [], "_error": repr(e)}
            total = round(time.perf_counter() - t0, 2)

            spec = body.get("spec")
            attempts = body.get("attempts") or []
            if not isinstance(attempts, list):
                attempts = [attempts]

            success_attempt = None
            for n, a in enumerate(attempts, 1):
                row = parse_attempt(a)
                if row["outcome"] == "succeeded" and success_attempt is None:
                    success_attempt = n
                att.writerow({"prompt_id": pid, "attempt_num": n, **row})

            layout, marks, answerable = summarise(spec)
            res.writerow({
                "prompt_id": pid,
                "succeeded": spec is not None,
                "success_attempt": success_attempt,
                "total_time": total,
                "chosen_layout": layout,
                "chosen_charts": marks,
                "chosen_answerable": answerable,
                "vis_spec": json.dumps(spec.get("vis_spec")) if isinstance(spec, dict) else None,
            })
            res_f.flush()
            att_f.flush()

    res_f.close()
    att_f.close()
    print("wrote results.csv and attempts.csv")


if __name__ == "__main__":
    main()