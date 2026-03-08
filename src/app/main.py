from fastapi import FastAPI

from src.app.database.session import create_db_and_tables
from src.app.routes.recipes import router as recipes_router

app = FastAPI()
app.include_router(recipes_router, prefix="/recipes")
create_db_and_tables()
