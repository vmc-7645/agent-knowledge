from sqlalchemy import create_engine
import pprint, os

url = os.getenv("DATABASE_URL",
    "postgresql+psycopg2://postgres:password@127.0.0.1:5432/agentdb")

# SQLAlchemy exposes the parsed URL
engine = create_engine(url)
print("SQLAlchemy URL      :", engine.url)

# What psycopg2 actually sees (dict)
print("psycopg2 connect args:")
pprint.pp(engine.url.translate_connect_args())
