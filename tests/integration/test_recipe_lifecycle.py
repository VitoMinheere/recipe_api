# tests/integration/test_recipe_lifecycle.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from src.app.database.models import Ingredient, Recipe, RecipeIngredientLink
from src.app.database.session import get_session
from src.app.main import app

client = TestClient(app)


@pytest.mark.usefixtures("session")
class TestRecipeLifecycle:
    """End-to-end tests for the complete recipe lifecycle."""

    @pytest.fixture(autouse=True)
    def setup_dependency_override(self, session: Session):
        """Override the get_session dependency for all tests in this class."""

        def get_session_override():
            return session

        app.dependency_overrides[get_session] = get_session_override
        yield
        app.dependency_overrides.clear()

    def test_complete_recipe_lifecycle(self, session: Session):
        """Test the complete lifecycle of a recipe: create, read, update, filter, delete."""
        # 1. Create a new recipe
        create_data = {
            "name": "Test Recipe Lifecycle",
            "instructions": "Step 1. Step 2. Step 3.",
            "servings": 4,
            "vegetarian": True,
            "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
        }

        # Create the recipe
        create_response = client.post("/recipes/", json=create_data)
        assert create_response.status_code == 201
        created_recipe = create_response.json()
        recipe_id = created_recipe["id"]

        # Verify the recipe was created correctly
        assert created_recipe["name"] == create_data["name"]
        assert created_recipe["instructions"] == create_data["instructions"]
        assert created_recipe["servings"] == create_data["servings"]
        assert created_recipe["vegetarian"] == create_data["vegetarian"]

        # Verify the database state
        db_recipe = session.get(Recipe, recipe_id)
        assert db_recipe is not None
        assert db_recipe.name == create_data["name"]

        # Verify ingredients were created
        ingredients = session.exec(
            select(Ingredient)
            .join(
                RecipeIngredientLink,
                Ingredient.id == RecipeIngredientLink.ingredient_id,
            )
            .where(RecipeIngredientLink.recipe_id == recipe_id)
        ).all()
        assert len(ingredients) == len(create_data["ingredients"])
        ingredient_names = [ing.name for ing in ingredients]
        assert "ingredient1" in ingredient_names
        assert "ingredient2" in ingredient_names
        assert "ingredient3" in ingredient_names

        # 2. Get the recipe by ID
        get_response = client.get(f"/recipes/{recipe_id}")
        assert get_response.status_code == 200
        fetched_recipe = get_response.json()
        assert fetched_recipe["id"] == recipe_id
        assert fetched_recipe["name"] == create_data["name"]

        # 3. Update the recipe (partial update)
        update_data = {
            "name": "Updated Recipe Name",
            "servings": 6,
            "ingredients": ["ingredient1", "ingredient4", "ingredient5"],
        }

        update_response = client.patch(f"/recipes/{recipe_id}", json=update_data)
        assert update_response.status_code == 200
        updated_recipe = update_response.json()
        assert updated_recipe["name"] == update_data["name"]
        assert updated_recipe["servings"] == update_data["servings"]

        # Verify the database state after update
        db_updated = session.get(Recipe, recipe_id)
        assert db_updated.name == update_data["name"]
        assert db_updated.servings == update_data["servings"]

        # Verify ingredients were updated
        updated_ingredients = session.exec(
            select(Ingredient)
            .join(
                RecipeIngredientLink,
                Ingredient.id == RecipeIngredientLink.ingredient_id,
            )
            .where(RecipeIngredientLink.recipe_id == recipe_id)
        ).all()
        updated_ingredient_names = [ing.name for ing in updated_ingredients]
        assert "ingredient1" in updated_ingredient_names  # Should still be there
        assert "ingredient4" in updated_ingredient_names  # New ingredient
        assert "ingredient5" in updated_ingredient_names  # New ingredient
        assert "ingredient2" not in updated_ingredient_names  # Should be removed
        assert "ingredient3" not in updated_ingredient_names  # Should be removed

        # 4. Test filtering
        # Filter by servings
        filter_response = client.get(f"/recipes/?servings={update_data['servings']}")
        assert filter_response.status_code == 200
        filtered_recipes = filter_response.json()
        recipe_ids = [r["id"] for r in filtered_recipes]
        assert recipe_id in recipe_ids

        # Filter by included ingredients
        filter_response = client.get(
            "/recipes/?include_ingredients=ingredient1,ingredient4"
        )
        assert filter_response.status_code == 200
        filtered_recipes = filter_response.json()
        recipe_ids = [r["id"] for r in filtered_recipes]
        assert recipe_id in recipe_ids

        # Filter by excluded ingredients
        filter_response = client.get("/recipes/?exclude_ingredients=ingredient2")
        assert filter_response.status_code == 200
        filtered_recipes = filter_response.json()
        recipe_ids = [r["id"] for r in filtered_recipes]
        assert recipe_id in recipe_ids  # Our recipe doesn't have ingredient2 anymore

        # 5. Test full update
        full_update_data = {
            "name": "Fully Updated Recipe",
            "instructions": "New instructions. Step A. Step B.",
            "servings": 8,
            "vegetarian": False,
            "ingredients": ["final_ingredient1", "final_ingredient2"],
        }

        full_update_response = client.patch(
            f"/recipes/{recipe_id}", json=full_update_data
        )
        assert full_update_response.status_code == 200
        fully_updated_recipe = full_update_response.json()
        assert fully_updated_recipe["name"] == full_update_data["name"]
        assert fully_updated_recipe["instructions"] == full_update_data["instructions"]
        assert fully_updated_recipe["servings"] == full_update_data["servings"]
        assert fully_updated_recipe["vegetarian"] == full_update_data["vegetarian"]

        # 6. Delete the recipe
        delete_response = client.delete(f"/recipes/{recipe_id}")
        assert delete_response.status_code == 204

        # Verify the recipe was deleted
        get_response = client.get(f"/recipes/{recipe_id}")
        assert get_response.status_code == 404

        # Verify the recipe was removed from the database
        db_deleted = session.get(Recipe, recipe_id)
        assert db_deleted is None

        # Verify the ingredient links were removed
        remaining_links = session.exec(
            select(RecipeIngredientLink).where(
                RecipeIngredientLink.recipe_id == recipe_id
            )
        ).all()
        assert len(remaining_links) == 0

        # Verify ingredients still exist (they shouldn't be deleted)
        for ingredient_name in [
            "ingredient1",
            "ingredient4",
            "ingredient5",
            "final_ingredient1",
            "final_ingredient2",
        ]:
            ingredient = session.exec(
                select(Ingredient).where(Ingredient.name == ingredient_name)
            ).first()
            assert ingredient is not None, (
                f"Ingredient {ingredient_name} should still exist"
            )
