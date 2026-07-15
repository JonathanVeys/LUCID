from pydantic import BaseModel
from enum import Enum
from typing import Literal

class PromptCategory(str, Enum):
    RETRIEVE_VALUE="retrieve value"
    FILTER="filter"
    COMPUTE_DERIVED_VALUE="compute derived value"
    FIND_EXTREMUM="find extremum"
    SORT="sort"
    DETERMINE_RANGE="determine range"
    CHARACTERISE_DISTRIBUTION="characterise distribution"
    FIND_ANOMALIES="find anomalies"
    CLUSTER="cluster"
    CORRELATE="correlate"

class ExpectedLayout(str, Enum):
    FOCUSED="focused"
    INFORMATIVE="informative"

class ExpectedCharts(str, Enum):
    BAR="bar"
    LINE="line"
    AREA="area"
    POINT="point"
    RECT="rect"
    ARC="arc"
    GEOSHAPE="geoshape"



class PromptTableSchema(BaseModel):
    prompt:str
    prompt_category:PromptCategory
    vague_language:bool
    spelling_errors:bool
    answerable:bool
    complexity:Literal[0, 1, 2, 3, 4, 5]
    expected_layout:ExpectedLayout|None=None
    expected_charts:list[ExpectedCharts]=[]
