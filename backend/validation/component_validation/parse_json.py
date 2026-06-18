import re, json


def parse_model_json(raw_spec: str) -> tuple[dict | None, list[str] | None]:
    """
    Parse the model's text output into a dict, tolerating code fences and
    surrounding prose. Returns (data, None) on success, or (None, errors) if no
    valid JSON object is found — errors feed the self-healing re-prompt.
    """
    if not raw_spec or not raw_spec.strip():
        return None, ["Model returned empty output."]

    match = re.search(r"\{.*\}", raw_spec, re.DOTALL)
    if not match:
        return None, ["No JSON object found in model output."]

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        return None, [f"Output was not valid JSON: {e}"]

    if not isinstance(data, dict):
        return None, [f"Expected a JSON object, got {type(data).__name__}"]

    return data, None