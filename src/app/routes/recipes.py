from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from pydantic import BaseModel
from typing import List

from src.app.database import get_session

router = APIRouter()

class RecipeIngredientLink(SQLModel, table=True):
    recipe_id: int = Field(foreign_key="recipe.id", primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", primary_key=True)

class Recipe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    instructions: str  = Field()
    servings: int = Field()
    vegetarian: bool = Field()

class Ingredient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

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
def create_recipe(
    recipe_data: RecipeCreate, 
    session: Session = Depends(get_session)
    ):
    """
    Create a new recipe with ingredients.

    - **name**: Name of the recipe.
    - **ingredients**: List of ingredient names.
    - **instructions**: Cooking instructions.
    - **servings**: Number of servings.
    - **vegetarian**: Whether the recipe is vegetarian.
    """
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

def _upsert_ingredients(session: Session, ingredient_names: List[str]) -> List[Ingredient]:
    """Upsert ingredients (create if they don't exist)."""
    ingredients = []
    for ingredient_name in ingredient_names:
        ingredient = session.exec(
            select(Ingredient).where(Ingredient.name == ingredient_name)
        ).first()

        if not ingredient:
            ingredient = Ingredient(name=ingredient_name)
            session.add(ingredient)
            session.commit()
            session.refresh(ingredient)
        ingredients.append(ingredient)
    return ingredients

def _create_links(session: Session, recipe_id: int, ingredients: List[Ingredient]) -> None:
    """Create links between a recipe and its ingredients."""
    ingredient_ids = [ingredient.id for ingredient in ingredients]
    for ingredient_id in ingredient_ids:
        link = RecipeIngredientLink(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
        )
        session.add(link)
    session.commit()