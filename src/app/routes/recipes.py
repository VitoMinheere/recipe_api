import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.app.database.models import Recipe
from src.app.database.session import get_session
from src.app.services.recipe_services import create_links, upsert_ingredients

router = APIRouter()

logger = logging.getLogger(__name__)


class RecipeModel(BaseModel):
    id: int | None = None
    name: str
    ingredients: List[str]
    instructions: str
    servings: int
    vegetarian: bool


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=Recipe,
    responses={
        201: {"description": "Recipe created successfully"},
        400: {"description": "Invalid input data"},
        500: {"description": "Internal server error"},
    },
)
def create_recipe(recipe_data: RecipeModel, session: Session = Depends(get_session)):
    """
    Create a new recipe with ingredients.

    - **name**: Name of the recipe.
    - **ingredients**: List of ingredient names.
    - **instructions**: Cooking instructions.
    - **servings**: Number of servings.
    - **vegetarian**: Whether the recipe is vegetarian.
    """
    try:
        ingredients = upsert_ingredients(session, recipe_data.ingredients)

        # Create the recipe
        recipe = Recipe(
            name=recipe_data.name,
            instructions=recipe_data.instructions,
            servings=recipe_data.servings,
            vegetarian=recipe_data.vegetarian,
        )
        session.add(recipe)
        session.commit()

        create_links(session, recipe.id, ingredients)

        # Reload the recipe for response
        session.refresh(recipe)
        return recipe

    except Exception as e:
        print(e)
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recipe: {str(e)}",
        )


@router.get("/", response_model=List[Recipe])
def get_recipes(session: Session = Depends(get_session)):
    """Get a list of all recipes."""
    recipes = session.exec(select(Recipe)).all()
    return recipes
