import re 
import json

from backend.errors.validation_error import ValidationError

def parse_model_response(raw_spec: str) -> tuple[dict | None, list[ValidationError]]:
    """
    Parse the model's text output into a dict, tolerating code fences and
    surrounding prose. Returns (data, None) on success, or (None, errors) if no
    valid JSON object is found — errors feed the self-healing re-prompt.
    """
    #Check that the spec is not empty
    if not raw_spec or not raw_spec.strip():
        err = ValidationError(
            type="JSON Syntax",
            details="JSON object is empty",
            location="parse_model_json"
            )
        return None, [err]


    match = re.search(r"\{.*\}", raw_spec, re.DOTALL)
    if not match:
        err = ValidationError(
            type="JSON Syntax",
            details= "Your response contained no JSON object. Reply with only the specification as a single JSON object starting with '{' and ending with '}' — no explanation, prose, or other text before or after it.",
            location="parse_model_json"
        )
        return None, [err]


    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        err = ValidationError(
            type="JSON Syntax",
            details=f"Model JSON failed JSON validation with: {e}",
            location="parse_model_json"
        )
        return None, [err]

    _JSON_TYPE = {list: "array", str: "string", int: "number",
              float: "number", bool: "boolean", type(None): "null"}
    if not isinstance(data, dict):
        got = _JSON_TYPE.get(type(data), type(data).__name__)
        detail = f"Expected the specification as a JSON object, but got a {got}."
        err = ValidationError(type="JSON Syntax", details=detail, location="parse_json_model")
        return None, [err]

    return data, []