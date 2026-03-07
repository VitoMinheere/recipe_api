from fastapi import FastAPI

from src.app.routes.recipes import router as recipes_router
from src.app.database.session import create_db_and_tables

app = FastAPI()
app.include_router(recipes_router, prefix="/recipes")
create_db_and_tables()
