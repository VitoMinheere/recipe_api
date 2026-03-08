import logging
from typing import List

from sqlmodel import Session, select

from src.app.database.models import Ingredient, RecipeIngredientLink

logger = logging.getLogger(__name__)


def upsert_ingredients(
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


def create_links(
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

def get_ingredients_by_names(session: Session, ingredient_names: List[str]) -> List[Ingredient]:
    """Fetch ingredients by their names."""
    try:
        ingredients = session.exec(
            select(Ingredient).where(Ingredient.name.in_(ingredient_names))
        ).all()
        return ingredients
    except Exception as e:
        logger.error(f"Error fetching ingredients by names {ingredient_names}: {e}")
        raise