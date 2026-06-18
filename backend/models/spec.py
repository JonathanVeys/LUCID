from pydantic import BaseModel, Field
from typing import Any
from enum import Enum



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
    vega_lite:dict[str,Any]

class VisSpec(BaseModel):
    title:str=Field(min_length=1)
    description:str=Field(min_length=1)
    layout_mode:LayoutMode
    charts:list[Chart]=Field(min_length=1)
