from typing import List
import logging

from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from src.app.database.session import get_session
from src.app.database.models import Recipe, Ingredient, RecipeIngredientLink

router = APIRouter()

logger = logging.getLogger(__name__)

class RecipeCreate(BaseModel):
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
def create_recipe(recipe_data: RecipeCreate, session: Session = Depends(get_session)):
    """
    Create a new recipe with ingredients.

    - **name**: Name of the recipe.
    - **ingredients**: List of ingredient names.
    - **instructions**: Cooking instructions.
    - **servings**: Number of servings.
    - **vegetarian**: Whether the recipe is vegetarian.
    """
    try:
        ingredients = _upsert_ingredients(session, recipe_data.ingredients)

        # Create the recipe
        recipe = Recipe(
            name=recipe_data.name,
            instructions=recipe_data.instructions,
            servings=recipe_data.servings,
            vegetarian=recipe_data.vegetarian,
        )
        session.add(recipe)
        session.commit()

        # Create links
        _create_links(session, recipe.id, ingredients)

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


def _upsert_ingredients(
    session: Session, ingredient_names: List[str]
) -> List[Ingredient]:
    """Upsert ingredients (create if they don't exist)."""
    ingredients = []
    for ingredient_name in ingredient_names:
        try:
            ingredient = session.exec(
                select(Ingredient).where(Ingredient.name == ingredient_name)
            ).first()

            if not ingredient:
                ingredient = Ingredient(name=ingredient_name)
                session.add(ingredient)
                session.commit()
                session.refresh(ingredient)
            ingredients.append(ingredient)
        except Exception as e:
            logger.error(f"Error upserting ingredient '{ingredient_name}': {e}")
            session.rollback()
            raise     
    return ingredients


def _create_links(
    session: Session, recipe_id: int, ingredients: List[Ingredient]
) -> None:
    """Create links between a recipe and its ingredients."""
    try:
        ingredient_ids = [ingredient.id for ingredient in ingredients]
        for ingredient_id in ingredient_ids:
            link = RecipeIngredientLink(
                recipe_id=recipe_id,
                ingredient_id=ingredient_id,
            )
            session.add(link)
        session.commit()
    except Exception as e:
        logger.error(f"Error creating links for recipe {recipe_id}: {e}")
        session.rollback()
        raise 
