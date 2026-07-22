from pydantic import ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails

# from backend.models.spec import VisSpec

# def validate_vis_spec(raw:dict) -> tuple[VisSpec|None, list[ErrorDetails]|None]:
#     '''
#     Validate raw LLM output against the VisSpec contract.

#     Returns (spec, None) on success, or (None, errors) on failure, where
#     `errors` is Pydantic's structured error list — ready to serialise back
#     into a re-prompt for the self-healing loop.
#     '''
#     try:
#         spec = VisSpec.model_validate(raw)
#         return spec, None
#     except ValidationError as e:
#         return None, e.errors()
    


from backend.models.spec import Response, adapter

def validate_vis_spec(raw: dict) -> tuple[Response | None, list[ErrorDetails] | None]:
    try:
        return adapter.validate_python(raw), None
    except PydanticValidationError as e:
        return None, e.errors()