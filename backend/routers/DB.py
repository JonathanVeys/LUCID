import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from pathlib import Path
import json

from backend.schema.introspect import load_schema, format_schema_for_prompt, format_vocab_for_prompt


load_dotenv()









"""
Region-coloured choropleth scaffold for LUCID.

KEY DECISION (from inspecting the data): `location_region` is internally
inconsistent — the same country appears under different regions across rows
(Sudan -> East Africa / Other / None; Russia -> Other; Nigeria -> West Africa /
Other / None), and the 'Other' bucket swallows mappable countries that then have
no geometry. So the map does NOT key on location_region. Instead:

  MODEL SQL aggregates by location_country:
      SELECT location_country, COUNT(*) FROM articles
      WHERE theme = :theme GROUP BY location_country
  SCAFFOLD resolves each country -> canonical region (deterministic), sums to
  region level, and broadcasts onto member-country geometry.

This keeps the unreliable region column out of the pipeline. The country->region
mapping is authored here and aligned to the extractor's sane labels where it made
one; lines marked OVERRIDE deliberately diverge from the extractor (it put these
in 'Other'/None, which would erase them). Geometry: vega-datasets world-110m.
"""
import pycountry

REGION_TO_ISO3 = {
 "North America":  ["USA","CAN","GRL","BMU"],
 "Central America":["MEX","GTM","BLZ","HND","SLV","NIC","CRI","PAN","CUB","DOM","HTI","JAM",
                    "BHS","TTO","BRB","LCA","GRD","VCT","ATG","DMA","KNA","PRI"],
 "South America":  ["COL","VEN","GUY","SUR","ECU","PER","BRA","BOL","PRY","URY","ARG","CHL","GUF"],
 "Europe":         ["GBR","IRL","FRA","BEL","NLD","LUX","DEU","AUT","CHE","LIE","ITA","ESP","PRT",
                    "AND","MCO","SMR","VAT","MLT","GRC","CYP","DNK","SWE","NOR","FIN","ISL","EST",
                    "LVA","LTU","POL","CZE","SVK","HUN","SVN","HRV","BIH","SRB","MNE","MKD","ALB",
                    "XKX","ROU","BGR","MDA","UKR","BLR","RUS"],
 "Middle East":    ["SAU","IRQ","IRN","ISR","JOR","LBN","SYR","YEM","OMN","ARE","BHR","QAT","KWT",
                    "TUR","ARM","AZE","GEO","EGY","LBY","DZA","MAR","TUN"],
 "West Africa":    ["NGA","GHA","MLI","LBR","SEN","CIV","GIN","SLE","BFA","NER","TGO","BEN","GMB",
                    "GNB","CPV","MRT"],
 "East Africa":    ["ETH","KEN","TZA","UGA","RWA","BDI","SOM","SSD","SDN","ERI","DJI","COM","SYC",
                    "MUS","MDG","MWI"],
 "Central Africa": ["COD","COG","CMR","CAF","TCD","GAB","GNQ","AGO","STP"],
 "Southern Africa":["ZAF","SWZ","LSO","BWA","NAM","ZWE","ZMB","MOZ"],
 "East Asia":      ["CHN","JPN","KOR","PRK","MNG","TWN","HKG","MAC"],
 "Southeast Asia": ["THA","VNM","KHM","LAO","MMR","MYS","SGP","IDN","PHL","BRN","TLS"],
 "South Asia":     ["IND","PAK","BGD","LKA","NPL","BTN","MDV","AFG","UZB","KAZ","KGZ","TJK","TKM"],
 "Pacific":        ["AUS","NZL","PNG","FJI","TON","WSM","VUT","SLB","FSM","KIR","PLW","NRU","TUV",
                    "MHL","NCL","PYF"],
}
ISO3_TO_REGION = {c: r for r, codes in REGION_TO_ISO3.items() for c in codes}

# DB strings pycountry can't map, or where we override the extractor.
# ("region", X) = non-country string mapped straight to a region.
# ("iso", X)    = spelling variant / alias pinned to an ISO3 code.
DIRECT = {
    "Europe": ("region", "Europe"), "European Union": ("region", "Europe"),
    "Multiple Caribbean nations": ("region", "Central America"),   # no 'Caribbean' region
    "Thailand and Cambodia": ("region", "Southeast Asia"),         # multi-nation string
    "The Bahamas": ("iso", "BHS"), "Bahamas": ("iso", "BHS"),
    "Democratic Republic of Congo": ("iso", "COD"),
    "Democratic Republic of the Congo": ("iso", "COD"),
    "South Korea": ("iso", "KOR"), "North Korea": ("iso", "PRK"),
    "Russia": ("iso", "RUS"),          # OVERRIDE: extractor said 'Other'
    "Turkey": ("iso", "TUR"),          # OVERRIDE: extractor said 'Europe'/'Other'  (flag: ME vs EU)
    "Federated States of Micronesia": ("iso", "FSM"),
    "United Kingdom": ("iso", "GBR"), "United States": ("iso", "USA"),
}

def resolve_region(name):
    """DB location_country string -> canonical region (or None = unmappable)."""
    if name is None:
        return None
    if name in DIRECT:
        kind, val = DIRECT[name]
        return val if kind == "region" else ISO3_TO_REGION.get(val)
    rec = pycountry.countries.get(name=name) or pycountry.countries.get(common_name=name)
    if rec is None:
        try:
            rec = pycountry.countries.search_fuzzy(name)[0]
        except LookupError:
            return None
    return ISO3_TO_REGION.get(rec.alpha_3)

def region_values_from_country_counts(rows, country_key="location_country", value_key="victim_count"):
    """Model's GROUP BY location_country result -> {region: summed value}.
    Unresolvable countries (None, unknown strings) are dropped and returned
    separately so you can surface a 'not shown' count rather than hiding it."""
    region_values, dropped = {}, {}
    for row in rows:
        region = resolve_region(row[country_key])
        if region is None:
            dropped[row[country_key]] = dropped.get(row[country_key], 0) + row[value_key]
        else:
            region_values[region] = region_values.get(region, 0) + row[value_key]
    return region_values, dropped

def _iso3_to_numeric_int(a3):
    if a3 == "XKX":
        return None
    rec = pycountry.countries.get(alpha_3=a3)
    return int(rec.numeric) if rec else None  # int() must match world-110m numeric ids

COUNTRY_ID_TO_REGION = {
    nid: region
    for region, codes in REGION_TO_ISO3.items()
    for a3 in codes
    if (nid := _iso3_to_numeric_int(a3)) is not None
}

def expand_region_values(region_values):
    return [{"id": cid, "value": region_values[region], "region": region}
            for cid, region in COUNTRY_ID_TO_REGION.items() if region in region_values]

def build_choropleth_spec(region_values, value_label="Count", title=""):
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": title, "width": 720, "height": 400,
        "projection": {"type": "equalEarth"},
        "data": {"url": "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/world-110m.json",
                 "format": {"type": "topojson", "feature": "countries"}},
        "transform": [{"lookup": "id",
                       "from": {"data": {"values": expand_region_values(region_values)},
                                "key": "id", "fields": ["value", "region"]}}],
        "mark": {"type": "geoshape", "stroke": "white", "strokeWidth": 0.4},
        "encoding": {"color": {"field": "value", "type": "quantitative",
                               "scale": {"scheme": "yelloworangered"},
                               "legend": {"title": value_label}},
                     "tooltip": [{"field": "region", "type": "nominal", "title": "Region"},
                                 {"field": "value", "type": "quantitative", "title": value_label}]},
        "config": {"view": {"stroke": None}, "mark": {"invalid": None}},
    }




if __name__ == "__main__":
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,      
            pool_recycle=1800,     
            connect_args={"sslmode": "require"},
        )
        with engine.connect() as conn:
            SQL = """
SELECT
  COUNT(*) AS all_rows,
  COUNT(*) FILTER (WHERE location_region = 'Southeast Asia') AS sea,
  COUNT(*) FILTER (WHERE crime_type = 'sex_trafficking') AS sex_traff,
  COUNT(*) FILTER (WHERE reported_date >= '2020-01-01'
                     AND reported_date <= '2025-12-31') AS in_window,
  COUNT(*) FILTER (WHERE location_region = 'Southeast Asia'
                     AND crime_type = 'sex_trafficking') AS sea_and_type,
  COUNT(*) FILTER (WHERE location_region = 'Southeast Asia'
                     AND crime_type = 'sex_trafficking'
                     AND reported_date >= '2020-01-01'
                     AND reported_date <= '2025-12-31') AS all_three
FROM incidents;
"""

            value = conn.execute(text(SQL))


            for row in value:
                print(row)