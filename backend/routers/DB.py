import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from pathlib import Path

from backend.schema.introspect import load_schema, format_schema_for_prompt, format_vocab_for_prompt


load_dotenv()



DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,      
        pool_recycle=1800,     
        connect_args={"sslmode": "require"},
    )
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM INCIDENTS"))
    counter = 0
    for row in rows:
        counter += 1
    print(counter)
# table_info = format_schema_for_prompt(engine)
# col_info = format_vocab_for_prompt(engine)


# PARENT_PATH = Path(__file__).parent.parent
# SYSTEM_PROMPT = (PARENT_PATH / "prompts/system_prompt_final.txt")
# with open(SYSTEM_PROMPT) as f:
#     sys_prompt = f.read()

# sys_prompt = sys_prompt.replace("DATABASE_SCHEMA", table_info)
# sys_prompt = sys_prompt.replace("COLUMN_INFO", col_info)
# print(sys_prompt)