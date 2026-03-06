from fastapi import FastAPI

from src.app.routes.recipes import router as recipes_router

app = FastAPI()
app.include_router(recipes_router, prefix="/recipes")
