import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# PostgreSQL connection string
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:dev123@localhost:5432/code_review"
)

# Redis connection string
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)
