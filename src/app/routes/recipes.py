import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from src.app.database.models import Ingredient, Recipe, RecipeIngredientLink
from src.app.database.session import get_session
from src.app.models.recipe import RecipeModel, RecipeUpdate
from src.app.services.recipes import (create_links, get_ingredients_by_names,
                                      upsert_ingredients)

router = APIRouter()

logger = logging.getLogger(__name__)


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
        bool | None, Query(description="Filter by vegetarian status")
    ] = None,
    servings: Annotated[
        int | None, Query(description="Filter by number of servings")
    ] = None,
    include_ingredients: Annotated[
        str | None, Query(description="Filter by including ingredients")
    ] = None,
    exclude_ingredients: Annotated[
        str | None, Query(description="Filter by excluding ingredients")
    ] = None,
    search: Annotated[
        str | None, Query(description="Search text in instructions")
    ] = None,
):
    """Get a list of all recipes."""
    query = select(Recipe).distinct()

    if vegetarian is not None:
        query = query.where(Recipe.vegetarian == vegetarian)
    if servings is not None:
        query = query.where(Recipe.servings == servings)
    if search:
        query = query.where(Recipe.instructions.ilike(f"%{search}%"))

    if include_ingredients is not None:
        if ingredients := get_ingredients_by_names(
            session, include_ingredients.split(",")
        ):
            ingredient_ids = set(i.id for i in ingredients)
            query = query.join(RecipeIngredientLink).where(
                RecipeIngredientLink.ingredient_id.in_(ingredient_ids)
            )
        else:
            return []  # No matching ingredients, return empty list

    if exclude_ingredients is not None:
        if ingredients := get_ingredients_by_names(
            session, exclude_ingredients.split(",")
        ):
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


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, session: Session = Depends(get_session)):
    """Delete a recipe and its ingredient associations."""
    # Get the recipe
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    # Delete all ingredient links for this recipe
    links = session.exec(
        select(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe_id)
    ).all()

    for link in links:
        session.delete(link)

    # Delete the recipe
    session.delete(recipe)
    session.commit()

    return None  # 204 No Content


@router.patch("/{recipe_id}", response_model=Recipe)
def update_recipe(
    recipe_id: int, recipe_data: RecipeUpdate, session: Session = Depends(get_session)
):
    """Fully update a recipe."""
    # Get the existing recipe
    db_recipe = session.get(Recipe, recipe_id)
    if not db_recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
        )

    # Update basic fields
    for field, value in recipe_data.model_dump(exclude={"ingredients"}).items():
        if value is not None:
            setattr(db_recipe, field, value)

    # Handle ingredients
    if recipe_data.ingredients is not None:
        # Remove all existing ingredient links
        existing_links = session.exec(
            select(RecipeIngredientLink).where(
                RecipeIngredientLink.recipe_id == recipe_id
            )
        ).all()

        for link in existing_links:
            session.delete(link)

        # Add new ingredient links
        for ingredient_name in recipe_data.ingredients:
            # Find or create the ingredient
            ingredient = session.exec(
                select(Ingredient).where(Ingredient.name == ingredient_name)
            ).first()

            if not ingredient:
                ingredient = Ingredient(name=ingredient_name)
                session.add(ingredient)
                session.commit()
                session.refresh(ingredient)

            # Create the link
            link = RecipeIngredientLink(
                recipe_id=recipe_id, ingredient_id=ingredient.id
            )
            session.add(link)

    session.commit()
    session.refresh(db_recipe)
    return db_recipe
