from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class RecipeCreate(BaseModel):
    name: str
    ingredients: list[str]
    instructions: str
    servings: int
    vegetarian: bool

@router.post("/", status_code=201)
def create_recipe(recipe: RecipeCreate):
    # TODO: Persist to database
    return recipe
