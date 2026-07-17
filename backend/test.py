from pathlib import Path
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from backend.schema.introspect import format_schema_for_prompt
from backend.routers.llm import db_schema

load_dotenv()

PARENT_PATH = Path(__file__).parent.parent
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    db_schema = format_schema_for_prompt(engine, table_names=["article_classifications", "incidents", "pipeline_runs", "raw_articles"])
    # print(db_schema)

    with engine.connect() as conn:
            rows = conn.execute(text("""SELECT location_country, article_url, victim_count
FROM incidents
WHERE reported_date >= '2015-01-01'
AND location_country IS NOT NULL;"""))
            for idx,row in enumerate(rows):
                print(row)
                if idx == 100:
                     break


