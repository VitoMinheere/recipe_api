from fastapi import APIRouter, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Recipe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    ingredients: List[str] = Field(default=[], sa_type=JSON)
    instructions: str  = Field()
    servings: int = Field()
    vegetarian: bool = Field()

class RecipeCreate(Recipe):
    pass

@router.post("/", status_code=201)
def create_recipe(recipe: RecipeCreate):
    # TODO: Persist to database
    return recipe
