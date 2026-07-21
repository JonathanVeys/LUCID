from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, TypeAdapter, ConfigDict
from pydantic_core import ErrorDetails
from typing import Any, Literal, Annotated, Union, Optional
from enum import Enum

from backend.errors.validation_error import ValidationError

from backend.validation.component_validation.parse_model_response import parse_model_response

class LayoutMode(str, Enum):
    focused="focused"
    informative="informative"
    scalar="scalar"

class ChartRole(str, Enum):
    primary="primary"
    supporting="supporting"

class MarkSpec(BaseModel):
    model_config = ConfigDict(extra="allow")     
    type: Literal["bar", "line", "area", "point", "rect", "arc", "geoshape"]

class VegaLite(BaseModel):
    model_config = ConfigDict(extra="allow")    
    mark: MarkSpec
    encoding: dict[str, Any]

class Chart(BaseModel):
    role:ChartRole
    title:str=Field(min_length=1)
    summary:str=Field(min_length=1)
    sql:str=Field(min_length=1)
    url_sql:str=Field(min_length=1)
    geo_granularity:Optional[Literal["country","region"]] = None
    label_field:str=Field(min_length=1)
    vega_lite:VegaLite

class ChartSpec(BaseModel):
    layout_mode:Literal[LayoutMode.focused, LayoutMode.informative]
    title:str=Field(min_length=1)
    description:str=Field(min_length=1)
    layout_rationale:str=Field(min_length=1)
    charts:list[Chart]=Field(min_length=1)

class ScalarSpec(BaseModel):
    layout_mode:Literal["scalar"]
    title:str=Field(min_length=1)
    unit:str=Field(min_length=1)
    qualifier:str=Field(min_length=1)
    sql:str=Field(min_length=1)
    url_sql:str=Field(min_length=1)

VisSpecUnion = Annotated[Union[ScalarSpec, ChartSpec], Field(discriminator="layout_mode")]

class AnsweredResponse(BaseModel):
    answerable:Literal[True]
    vis_spec:VisSpecUnion

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




if __name__ == "__main__":
    BAD_MARK_SPEC = '''
{
  "answerable": true,
  "vis_spec": {
    "title": "Incidents by crime type",
    "description": "A view built to explore which crime types are reported most often.",
    "layout_mode": "focused",
    "layout_rationale": "The question names one breakdown, so a single chart answers it.",
    "charts": [
      {
        "role": "primary",
        "title": "Incidents by crime type",
        "summary": "Compare the bar heights to see which crime types are most reported.",
        "sql": "SELECT crime_type, COUNT(*) AS incident_count FROM incidents WHERE crime_type IS NOT NULL GROUP BY crime_type ORDER BY incident_count DESC LIMIT 15",
        "url_sql": "SELECT crime_type, (ARRAY_AGG(article_url ORDER BY reported_date DESC))[1:10] AS urls FROM incidents WHERE crime_type IS NOT NULL GROUP BY crime_type ORDER BY COUNT(*) DESC LIMIT 15",
        "label_field": "crime_type",
        "vega_lite": {
          "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
          "mark": "bar",
          "params": [
            {"name": "select", "select": "point"},
            {"name": "highlight", "select": {"type": "point", "on": "pointerover"}}
          ],
          "encoding": {
            "x": {"field": "crime_type", "type": "nominal", "axis": {"title": "Crime type"}},
            "y": {"field": "incident_count", "type": "quantitative", "axis": {"title": "Number of incidents"}}
          }
        }
      }
    ]
  }
}
'''
    spec, err = parse_model_response(BAD_MARK_SPEC)
    if err:
        print(err)
    else:
        if spec:
            ok, errs = validate_spec(spec)
        if not ok:
            for err in errs:
                print(err)
        else:
            print(f"Test Passed")