import logging
from typing import List

from fastapi import Annotated, APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.app.database.models import Ingredient, Recipe, RecipeIngredientLink
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
        logger.error(f"Error creating recipe: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recipe: {str(e)}",
        )


@router.get("/", response_model=List[Recipe])
def get_recipes(
    session: Session = Depends(get_session),
    vegetarian: Annotated[
        bool | None, Query(None, description="Filter by vegetarian status")
    ] = None,
    servings: Annotated[
        int | None, Query(None, description="Filter by number of servings")
    ] = None,
    include_ingredients: Annotated[
        str | None, Query(None, description="Filter by including ingredients")
    ] = None,
    exclude_ingredients: Annotated[
        str | None, Query(None, description="Filter by excluding ingredients")
    ] = None,
):
    """Get a list of all recipes."""
    query = select(Recipe).distinct()

    if vegetarian is not None:
        query = query.where(Recipe.vegetarian == vegetarian)
    if servings is not None:
        query = query.where(Recipe.servings == servings)

    if include_ingredients is not None:
        include_list = include_ingredients.split(",")
        ingredients = session.exec(
            select(Ingredient).where(Ingredient.name.in_(include_list))
        ).all()
        if ingredients:
            ingredient_ids = set(i.id for i in ingredients)
            query = query.join(RecipeIngredientLink).where(
                RecipeIngredientLink.ingredient_id.in_(ingredient_ids)
            )
        else:
            return []  # No matching ingredients, return empty list

    if exclude_ingredients is not None:
        exclude_list = exclude_ingredients.split(",")
        ingredients = session.exec(
            select(Ingredient).where(Ingredient.name.in_(exclude_list))
        ).all()
        if ingredients:
            ingredient_ids = set(i.id for i in ingredients)
            recipe_ids_with_excluded = session.exec(
                select(RecipeIngredientLink.recipe_id).where(
                    RecipeIngredientLink.ingredient_id.in_(ingredient_ids)
                )
            ).all()
            query = query.where(Recipe.id.not_in(recipe_ids_with_excluded))

    recipes = session.exec(query).all()
    return recipes


@router.get("/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: int, session: Session = Depends(get_session)):
    """Get a single recipe by ID."""
    recipe = session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )
    return recipe
