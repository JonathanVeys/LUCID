# import pydantic
from pydantic import BaseModel, Field, ConfigDict, model_validator, TypeAdapter, ValidationError as PydanticValidationError
from pydantic_core import ErrorDetails
from typing import Any, Literal, Annotated, Union, Optional
from enum import Enum

from backend.errors.validation_error import ValidationError

from backend.validation.component_validation.parse_model_response import parse_model_response


class ChartRole(str, Enum):
    primary="primary"
    supporting="supporting"

class MarkSpec(BaseModel):
    model_config = ConfigDict(extra="allow")     
    type: Literal["bar", "line", "area", "point", "rect", "arc", "geoshape"]

class VegaLite(BaseModel):
    model_config = ConfigDict(extra="allow")    
    mark: MarkSpec
    encoding:dict[str, Any]=Field(min_length=1)


class BaseChart(BaseModel):
    model_config=ConfigDict(extra="forbid")
    role:ChartRole
    title:str=Field(min_length=1)
    summary:str=Field(min_length=1)
    sql:str=Field(min_length=1)
    url_sql:str=Field(min_length=1)
    label_field:str=Field(min_length=1)
    vega_lite:VegaLite


class LookupData(BaseModel):
    model_config = ConfigDict(extra="allow")
    values: list[Any]

class LookupFrom(BaseModel):
    model_config = ConfigDict(extra="allow")
    data: LookupData
    key: Literal["id"]
    fields: list[str]

    @model_validator(mode="after")
    def _fields_exact(self):
        if set(self.fields) != {"value", "label", "urls"}:
            raise ValueError(
                f"A map lookup's 'fields' must be exactly "
                f'["value", "label", "urls"]; got {self.fields!r}.')
        return self

class LookupTransform(BaseModel):
    model_config = ConfigDict(extra="allow")
    lookup: Literal["id"]
    from_: LookupFrom = Field(alias="from")

class GeoVegaLite(VegaLite):
    transform: list[LookupTransform] = Field(min_length=1, max_length=1)


class SimpleChart(BaseChart):
    chart_kind:Literal["simple"]

    @model_validator(mode="after")
    def _mark_matches_kind(self):
        if self.vega_lite.mark.type == "geoshape":
            raise ValueError(
                "chart_kind is 'simple' but the mark is 'geoshape'. Set "
                "chart_kind to 'map' and add geo_granularity, or choose a "
                "non-map mark.")
        return self

class ChoroplethChart(BaseChart):
    chart_kind:Literal["map"]
    geo_granularity:Literal["country", "region"]
    vega_lite:GeoVegaLite

    @model_validator(mode="after")
    def _mark_matches_kind(self):
        if self.vega_lite.mark.type != "geoshape":
            raise ValueError(
                f"chart_kind is 'map' but the mark is "
                f"'{self.vega_lite.mark.type}'. A map must use mark type "
                f"'geoshape'.")
        return self


ChartUnion = Annotated[
    Union[SimpleChart, ChoroplethChart],
    Field(discriminator="chart_kind"),
]


class FocusedSpec(BaseModel):
    model_config=ConfigDict(extra="forbid")
    layout_mode:Literal["focused"]
    title:str=Field(min_length=1)
    description:str=Field(min_length=1)
    layout_rationale:str=Field(min_length=1)
    charts:list[ChartUnion] = Field(min_length=1)

    @model_validator(mode="after")
    def _single_primary(self):
        roles = [c.role for c in self.charts]
        n_primary = roles.count(ChartRole.primary)
        if len(self.charts) != 1 or n_primary != 1:
            raise ValueError(
                f"A focused layout requires exactly 1 chart: one with role 'primary'. You provided {len(self.charts)} chart(s) with roles {[r.value for r in roles]}. "
                f"Either remove the added charts, or use layout_mode 'informative' if multiple charts answer the question.")
        return self

class InformativeSpec(BaseModel):
    model_config=ConfigDict(extra="forbid")
    layout_mode:Literal["informative"]
    title:str=Field(min_length=1)
    description:str=Field(min_length=1)
    layout_rationale:str=Field(min_length=1)
    charts:list[ChartUnion]=Field(min_length=1)

    @model_validator(mode="after")
    def _shape(self):
        roles = [c.role for c in self.charts]
        n_primary = roles.count(ChartRole.primary)
        if len(self.charts) != 3 or n_primary != 1:
            raise ValueError(
                f"An informative layout requires exactly 3 charts: one with role 'primary' and two with role 'supporting'. You provided {len(self.charts)} chart(s) with roles {[r.value for r in roles]}. "
                f"Either add the missing charts, or use layout_mode 'focused' if a single chart answers the question.")
        return self
    
class ScalarSpec(BaseModel):
    model_config=ConfigDict(extra="forbid")
    layout_mode:Literal["scalar"]
    title:str=Field(min_length=1)
    unit:str=Field(min_length=1)
    qualifier:str=Field(min_length=1)
    sql:str=Field(min_length=1)
    url_sql:str=Field(min_length=1)
    
VisSpecUnion = Annotated[
    Union[ScalarSpec, FocusedSpec, InformativeSpec],
    Field(discriminator="layout_mode"),
]

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


def validate_spec(spec: dict) -> tuple[UnansweredResponse|AnsweredResponse|None, list[ValidationError]]:
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
    "title": "Reported pig-butchering scams by country",
    "description": "A map built to explore how reported pig-butchering incidents are distributed across countries.",
    "layout_mode": "focused",
    "layout_rationale":"The question names a specific thing to rank — which countries report the most — so a single chart answers it without supporting views. Because the comparison is between places, a map is used rather than a ranked list: it shows both which countries report most and how those reports cluster geographically.",
    "charts": [
      {
        "role": "primary",
        "title": "Reported incidents by country",
        "summary": "Read the shading to compare which countries report pig-butchering incidents most often; hover a country for its value.",
        "sql": "SELECT location_country, COUNT(*) AS incident_count FROM incidents WHERE crime_type = 'pig_butchering' AND location_country IS NOT NULL GROUP BY location_country ORDER BY incident_count DESC",
        "url_sql": "SELECT location_country, (ARRAY_AGG(article_url ORDER BY reported_date DESC))[1:10] AS urls FROM incidents WHERE crime_type = 'pig_butchering' AND location_country IS NOT NULL GROUP BY location_country ORDER BY COUNT(*) DESC",
        "label_field":"location_country",
        "chart_kind":"map",
        "geo_granularity": "country",
        "vega_lite": {
          "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
          "width": "container",
          "height": "container",
          "projection": {"type": "equalEarth"},
          "data": {
            "url": "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/world-110m.json",
            "format": {"type": "topojson", "feature": "countries"}
          },
          "transform": [
            {
              "lookup": "id",
              "from": {
                "data": {"values": []},
                "key": "id",
                "fields": ["value", "label", "urls"]
              }
            }
          ],
          "params": [
              {"name": "select", "select": "point"},
              {"name": "highlight", "select": {"type": "point", "on": "pointerover"}}
            ],
          "mark": {"type": "geoshape", "stroke": "black", "strokeWidth": 0.4},
          "encoding": {
            "color": {
              "field": "value",
              "type": "quantitative",
              "scale": {"scheme": "yelloworangered", "type":"log"},
              "legend": {"title": "Reported incidents"}
            },
            "tooltip": [
              {"field": "label", "type": "nominal", "title": "Location"},
              {"field": "value", "type": "quantitative", "title": "Reported incidents"}
            ],
            "fillOpacity": {
              "condition": {"param": "select", "value": 1},
              "value": 0.3
            },
            "strokeWidth": {
              "condition": [
                {"param": "select", "empty": false, "value": 2},
                {"param": "highlight", "empty": false, "value": 1}
              ],
              "value": 0.5
            }
          },
          "config": {"view": {"stroke": null}, "mark": {"invalid": null}}
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