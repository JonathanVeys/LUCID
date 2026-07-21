from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, TypeAdapter
from pydantic_core import ErrorDetails
from typing import Any, Literal, Annotated, Union, Optional
from enum import Enum

from backend.errors.validation_error import ValidationError


class LayoutMode(str, Enum):
    focused="focused"
    informative="informative"

class ChartRole(str, Enum):
    primary="primary"
    supporting="supporting"

class Chart(BaseModel):
    role:ChartRole
    title:str=Field(min_length=1)
    summary:str=Field(min_length=1)
    sql:str=Field(min_length=1)
    url_sql:str=Field(min_length=1)
    geo_granularity:Optional[Literal["country","region"]] = None
    label_field:str=Field(min_length=1)
    vega_lite:dict[str,Any]

class VisSpec(BaseModel):
    title:str=Field(min_length=1)
    description:str=Field(min_length=1)
    layout_mode:LayoutMode
    layout_rationale:str=Field(min_length=1)
    charts:list[Chart]=Field(min_length=1)

class AnsweredResponse(BaseModel):
    answerable:Literal[True]
    vis_spec:VisSpec

class UnansweredResponse(BaseModel):
    answerable:Literal[False]
    reason:str=Field(min_length=1)

Response = Annotated[
    Union[AnsweredResponse, UnansweredResponse],
    Field(discriminator="answerable"),
]
adapter = TypeAdapter(Response)
    




def _describe(err: ErrorDetails) -> str:
    '''
    Turn one Pydantic error into an instruction the model can act on.
    '''
    parts = [str(p) for p in err["loc"] if isinstance(p, str)]
    path = ".".join(parts) or "the specification"
    field = parts[-1] if parts else "field"
    etype = err["type"]

    if etype == "missing":
        return (f"Your specification is missing the required field '{field}' "
                f"(at {path}). Add it as described in the system instructions.")

    if etype.startswith("literal_error"):
        allowed = err.get("ctx", {}).get("expected", "")
        return (f"The field '{field}' (at {path}) has an invalid value "
                f"{err.get('input')!r}. It must be one of: {allowed}.")

    if etype in ("string_type", "int_type", "float_type", "bool_type",
                 "dict_type", "list_type", "model_type"):
        return (f"The field '{field}' (at {path}) is the wrong type: "
                f"{err['msg'].lower()}. You provided {type(err.get('input')).__name__}.")

    if etype in ("string_too_short", "too_short"):
        return (f"The field '{field}' (at {path}) must not be empty.")

    return f"Problem with '{field}' (at {path}): {err['msg']}."


def validate_spec(spec: dict) -> tuple[UnansweredResponse | AnsweredResponse | None,
                                       list[ValidationError]]:
    try:
        result = adapter.validate_python(spec)
    except PydanticValidationError as e:
        errors = [
            ValidationError(type="VisSpec Schema", details=_describe(err), location="validate_spec")
            for err in e.errors()
        ]
        return None, errors
    return result, []




 