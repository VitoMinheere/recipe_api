import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlmodel import Session, select

from src.app.database.models import Ingredient, Recipe, RecipeIngredientLink
from src.app.database.session import get_session
from src.app.main import app
from src.app.models.recipe import RecipeModel

client = TestClient(app)


@pytest.mark.usefixtures("session")
class TestRecipeCreation:
    """Tests for the /recipes/ POST endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependency_override(self, session: Session):
        """Override the get_session dependency for all tests in this class."""

        def get_session_override():
            return session

        app.dependency_overrides[get_session] = get_session_override
        yield
        app.dependency_overrides.clear()

    def test_create_recipe(self, session: Session):
        recipe_data = {
            "name": "Pasta Carbonara",
            "ingredients": ["pasta", "eggs", "cheese", "bacon"],
            "instructions": "Cook pasta. Mix eggs and cheese. Add bacon. Combine.",
            "servings": 2,
            "vegetarian": False,
        }

        response = client.post("/recipes/", json=recipe_data)

        # Assert the response is correct
        assert response.status_code == 201
        created_recipe = response.json()
        assert created_recipe["name"] == "Pasta Carbonara"
        assert created_recipe["servings"] == 2
        assert created_recipe["vegetarian"] is False

        # Check the recipe exists in the database
        db_recipe = session.exec(
            select(Recipe).where(Recipe.id == created_recipe["id"])
        ).first()
        assert db_recipe is not None
        assert db_recipe.name == "Pasta Carbonara"

        # Check ingredients exist in the database
        db_ingredients = session.exec(select(Ingredient)).all()
        ingredient_names = [ing.name for ing in db_ingredients]
        assert "pasta" in ingredient_names
        assert "eggs" in ingredient_names
        assert "bacon" in ingredient_names

        # Verify links exist
        links = session.exec(select(RecipeIngredientLink)).all()
        assert len(links) == len(recipe_data["ingredients"])

    def test_create_recipe_missing_data(self):
        """Test 422 error for missing required fields."""
        invalid_data = {
            "name": "Incomplete Recipe",
            # Missing ingredients, instructions, servings, vegetarian
        }
        response = client.post("/recipes/", json=invalid_data)
        assert response.status_code == 422

    def test_create_recipe_empty_ingredients(self):
        """Test 422 error for empty ingredients list."""
        invalid_data = {
            "name": "Incomplete Recipe",
            "ingredients": [],
            "instructions": "Test instructions",
            "servings": 1,
            "vegetarian": True,
        }
        response = client.post("/recipes/", json=invalid_data)
        assert response.status_code == 422

    def test_create_recipe_server_error(self, mocker, session: Session):
        """Test 500 error on database failure."""
        mocker.patch(
            "src.app.database.session.Session.commit", side_effect=Exception("DB error")
        )
        recipe_data = {
            "name": "Test Recipe",
            "ingredients": ["test"],
            "instructions": "Test instructions",
            "servings": 1,
            "vegetarian": True,
        }

        response = client.post("/recipes/", json=recipe_data)
        assert response.status_code == 500
        assert "Failed to create recipe" in response.json()["detail"]


@pytest.mark.usefixtures("session_with_data")
class TestRecipeFetch:
    """Tests for the /recipes/{} GET endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependency_override(self, session_with_data: Session):
        """Override the get_session dependency for all tests in this class."""

        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override
        yield
        app.dependency_overrides.clear()

    def test_get_recipe(self, session_with_data: Session):
        """Test getting a list of recipes."""
        response = client.get("/recipes/")
        recipes = response.json()

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(recipes) == 3

    def test_get_recipe_no_recipes(self, session: Session):
        """Test getting recipes when none exist."""

        def get_session_override():
            return session

        app.dependency_overrides[get_session] = get_session_override
        response = client.get("/recipes/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_recipe_by_id(self, session_with_data: Session):
        """Test getting a single recipe by ID."""
        # Get the first recipe from the database
        db_recipe = session_with_data.exec(select(Recipe)).first()
        recipe_id = db_recipe.id

        # Then, get the recipe by ID
        response = client.get(f"/recipes/{recipe_id}")
        assert response.status_code == 200
        assert response.json()["name"] == db_recipe.name

    def test_filter_by_vegetarian(self, session_with_data: Session):
        """Test filtering recipes by vegetarian status."""
        # Test vegetarian recipes
        response = client.get("/recipes/?vegetarian=true")
        assert response.status_code == 200

        recipes = response.json()
        assert len(recipes) == 1  # One vegetarian recipe
        recipe_names = [recipe["name"] for recipe in recipes]
        assert "Vegetable Stir Fry" in recipe_names

        # Test non-vegetarian recipes
        response = client.get("/recipes/?vegetarian=false")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 2  # We expect 1 non-vegetarian recipe
        assert recipes[0]["name"] == "Pasta Carbonara"
        assert recipes[1]["name"] == "Salmon Bake"

    def test_filter_by_servings(self, session_with_data: Session):
        """Test filtering recipes by amount of servings."""
        # Test vegetarian recipes
        response = client.get("/recipes/?servings=3")
        assert response.status_code == 200

        recipes = response.json()
        assert len(recipes) == 1  # One vegetarian recipe
        recipe_names = [recipe["name"] for recipe in recipes]
        assert "Vegetable Stir Fry" in recipe_names

    def test_filter_by_ingredients(self, session_with_data: Session):
        """Test filtering recipes by ingredients."""
        response = client.get("/recipes/?include_ingredients=pasta")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1  # Only one recipe with pasta
        assert recipes[0]["name"] == "Pasta Carbonara"

        # Try with none existing ingredient
        response = client.get("/recipes/?include_ingredients=none_existing_ingredient")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 0

        response = client.get("/recipes/?include_ingredients=potatoes,onion")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 2
        assert recipes[0]["name"] == "Salmon Bake"
        assert recipes[1]["name"] == "Vegetable Stir Fry"

    def test_filter_by_excluding_ingredient(self, session_with_data: Session):
        """Test filtering recipes by excluding ingredients."""
        response = client.get("/recipes/?exclude_ingredients=pasta")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 2  # Two recipes without pasta
        assert recipes[0]["name"] == "Vegetable Stir Fry"
        assert recipes[1]["name"] == "Salmon Bake"

        response = client.get("/recipes/?exclude_ingredients=pasta,onion,salmon")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 0

    def test_combined_filters(self, session_with_data: Session):
        """Test combining multiple filters."""
        # Vegetarian recipes that don't include pasta
        response = client.get("/recipes/?vegetarian=true&exclude_ingredients=pasta")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1  # Only Vegetable Stir Fry
        assert recipes[0]["name"] == "Vegetable Stir Fry"

        # Non Vegetarian recipes that don't include pasta
        response = client.get(
            "/recipes/?vegetarian=false&exclude_ingredients=pasta&include_ingredients=potatoes"
        )
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1  # Only Salmon Bake
        assert recipes[0]["name"] == "Salmon Bake"

        # All recipes with potatoes in ingredients and "oven" in instructions
        response = client.get("/recipes/?include_ingredients=potatoes&search=oven")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1  # Only Salmon Bake
        assert recipes[0]["name"] == "Salmon Bake"

    def test_search_instructions(self, session_with_data: Session):
        """Test searching recipes by instructions text."""
        # Test recipes with "soy" in instructions
        response = client.get("/recipes/?search=soy")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1  # Only one recipe with "soy" in instructions
        assert recipes[0]["name"] == "Vegetable Stir Fry"

        # Test recipes with "oven" in instructions
        response = client.get("/recipes/?search=oven")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1  # Only one recipe with "oven" in instructions
        assert recipes[0]["name"] == "Salmon Bake"

        # Test case-insensitive search
        response = client.get("/recipes/?search=PASTA")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1  # Only one recipe with "pasta" in instructions
        assert recipes[0]["name"] == "Pasta Carbonara"


@pytest.mark.usefixtures("session_with_data")
class TestRecipeDelete:
    """Tests for the /recipe/{} DELETE endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependency_override(self, session_with_data: Session):
        """Override the get_session dependency for all tests in this class."""

        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override
        yield
        app.dependency_overrides.clear()

    def test_delete_recipe_success(self, session_with_data: Session):
        """Test successfully deleting a recipe."""
        # Get an existing recipe from the database
        db_recipe = session_with_data.exec(select(Recipe)).first()
        ingredients_before = session_with_data.exec(select(Ingredient)).all()
        recipe_id = db_recipe.id

        # Verify the recipe exists before deletion
        response = client.get(f"/recipes/{recipe_id}")
        assert response.status_code == 200

        # Delete the recipe
        response = client.delete(f"/recipes/{recipe_id}")
        assert response.status_code == 204  # No Content

        # Verify the recipe no longer exists
        response = client.get(f"/recipes/{recipe_id}")
        assert response.status_code == 404  # Not Found

        # Verify the recipe is removed from the database
        db_recipe = session_with_data.get(Recipe, recipe_id)
        assert db_recipe is None

        # Verify the links are also removed
        links = session_with_data.exec(
            select(RecipeIngredientLink).where(
                RecipeIngredientLink.recipe_id == recipe_id
            )
        ).all()
        assert len(links) == 0

        # Check that ingredients are not deleted (since they may be shared with other recipes)
        ingredients_after = session_with_data.exec(select(Ingredient)).all()
        assert len(ingredients_after) == len(ingredients_before)

    def test_delete_nonexistent_recipe(self, session_with_data: Session):
        """Test deleting a non-existent recipe."""
        # Use a non-existent ID (e.g., 9999)
        response = client.delete("/recipes/9999")
        assert response.status_code == 404  # Not Found


@pytest.mark.usefixtures("session_with_data")
class TestRecipeUpdate:
    """Test suite for recipe updates."""

    @pytest.fixture(autouse=True)
    def setup_dependency_override(self, session_with_data: Session):
        """Override the get_session dependency for all tests in this class."""

        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override
        yield
        app.dependency_overrides.clear()

    def test_update_recipe_full(self, session_with_data: Session):
        """Test fully updating a recipe with PATCH."""
        # Get an existing recipe
        db_recipe = session_with_data.exec(select(Recipe)).first()
        recipe_id = db_recipe.id
        original_vegetarian_status = db_recipe.vegetarian

        # Update data
        update_data = {
            "name": "Updated Recipe Name",
            "instructions": "Updated instructions with more details",
            "servings": 5,
            "vegetarian": not db_recipe.vegetarian,  # Flip vegetarian status
            "ingredients": ["new_ingredient1", "new_ingredient2"],
        }

        # Update the recipe
        response = client.patch(f"/recipes/{recipe_id}", json=update_data)
        assert response.status_code == 200

        # Verify the response
        updated_recipe = response.json()
        assert updated_recipe["name"] == "Updated Recipe Name"
        assert (
            updated_recipe["instructions"] == "Updated instructions with more details"
        )
        assert updated_recipe["servings"] == 5
        assert updated_recipe["vegetarian"] != original_vegetarian_status

        # Verify the database state
        db_updated = session_with_data.get(Recipe, recipe_id)
        assert db_updated.name == "Updated Recipe Name"
        assert db_updated.instructions == "Updated instructions with more details"
        assert db_updated.servings == 5
        assert db_updated.vegetarian != original_vegetarian_status

        # Verify ingredients were updated
        ingredient_names = [
            ingredient.name
            for ingredient in session_with_data.exec(
                select(Ingredient)
                .join(
                    RecipeIngredientLink,
                    Ingredient.id == RecipeIngredientLink.ingredient_id,
                )
                .where(RecipeIngredientLink.recipe_id == recipe_id)
            ).all()
        ]
        assert "new_ingredient1" in ingredient_names
        assert "new_ingredient2" in ingredient_names

    def test_update_recipe_partial(self, session_with_data: Session):
        """Test partially updating a recipe."""
        # Get an existing recipe
        db_recipe = session_with_data.exec(select(Recipe)).first()
        recipe_id = db_recipe.id

        # Update only some fields
        update_data = {
            "name": "Partially Updated Recipe Name",
            "servings": 3,
            # Don't update instructions, vegetarian, or ingredients
        }

        # Update the recipe
        response = client.patch(f"/recipes/{recipe_id}", json=update_data)
        assert response.status_code == 200

        # Verify the response
        updated_recipe = response.json()
        assert updated_recipe["name"] == "Partially Updated Recipe Name"
        assert updated_recipe["servings"] == 3
        # Verify unchanged fields
        assert updated_recipe["instructions"] == db_recipe.instructions
        assert updated_recipe["vegetarian"] == db_recipe.vegetarian


class TestFieldValidators:
    """Test suite for field validators in Recipe models."""

    # Tests for name validator
    def test_name_validator_valid(self):
        """Test that valid names pass validation."""
        # Test with normal name
        recipe = RecipeModel(
            name="Valid Recipe Name",
            instructions="Cook for 30 minutes",
            servings=2,
            vegetarian=False,
            ingredients=["ingredient1"],
        )
        assert recipe.name == "Valid Recipe Name"

        # Test with name that has extra whitespace
        recipe = RecipeModel(
            name="  Valid Recipe Name  ",
            instructions="Cook for 30 minutes",
            servings=2,
            vegetarian=False,
            ingredients=["ingredient1"],
        )
        assert recipe.name == "Valid Recipe Name"  # Should be stripped

    def test_name_validator_empty(self):
        """Test that empty names fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            RecipeModel(
                name="",
                instructions="Cook for 30 minutes",
                servings=2,
                vegetarian=False,
                ingredients=["ingredient1"],
            )
        assert "Recipe name cannot be empty" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            RecipeModel(
                name="   ",  # Only whitespace
                instructions="Cook for 30 minutes",
                servings=2,
                vegetarian=False,
                ingredients=["ingredient1"],
            )
        assert "Recipe name cannot be empty" in str(exc_info.value)
