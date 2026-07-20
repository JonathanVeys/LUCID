from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, TypeAdapter
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
    



def validate_spec(spec: dict) -> tuple[UnansweredResponse | AnsweredResponse | None, list[ValidationError]]:
    '''
    A function for validating a candidate Spec against a pydantic model
    '''
    try:
        result = adapter.validate_python(spec)
    except PydanticValidationError as e:
        errors = [
            ValidationError(
                type='VisSpec Schema',
                details=f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}",
                location="validate_vis_spec"
            )
            for err in e.errors()
        ]
        return None, errors
    return result, []



 