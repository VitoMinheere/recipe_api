import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from src.app.database.models import Ingredient, Recipe, RecipeIngredientLink
from src.app.database.session import get_session
from src.app.main import app

client = TestClient(app)


@pytest.mark.usefixtures("session")
class TestRecipeCreation:
    """Tests for the /recipes/ POST endpoint."""

    def test_create_recipe(self, session: Session):
        def get_session_override():
            return session

        app.dependency_overrides[get_session] = get_session_override

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
        print(created_recipe)
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

    def test_get_recipe(self, session_with_data: Session):
        """Test getting a list of recipes."""

        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override

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

        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override
        # Get the first recipe from the database
        db_recipe = session_with_data.exec(select(Recipe)).first()
        recipe_id = db_recipe.id

        # Then, get the recipe by ID
        response = client.get(f"/recipes/{recipe_id}")
        assert response.status_code == 200
        assert response.json()["name"] == db_recipe.name

    def test_filter_by_vegetarian(self, session_with_data):
        """Test filtering recipes by vegetarian status."""

        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override

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

    def test_filter_by_servings(self, session_with_data):
        """Test filtering recipes by amount of servings."""

        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override

        # Test vegetarian recipes
        response = client.get("/recipes/?servings=3")
        assert response.status_code == 200

        recipes = response.json()
        assert len(recipes) == 1  # One vegetarian recipe
        recipe_names = [recipe["name"] for recipe in recipes]
        assert "Vegetable Stir Fry" in recipe_names

    def test_filter_by_ingredients(self, session_with_data):
        """Test filtering recipes by ingredients."""

        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override

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

    def test_filter_by_excluding_ingredient(self, session_with_data):
        """Test filtering recipes by excluding ingredients."""
        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override

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

    def test_combined_filters(self, session_with_data):
        """Test combining multiple filters."""
        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override
        # Vegetarian recipes that don't include pasta
        response = client.get("/recipes/?vegetarian=true&exclude_ingredients=pasta")
        assert response.status_code == 200
        recipes = response.json()
        assert len(recipes) == 1  # Only Vegetable Stir Fry
        assert recipes[0]["name"] == "Vegetable Stir Fry"

        # Non Vegetarian recipes that don't include pasta
        response = client.get("/recipes/?vegetarian=false&exclude_ingredients=pasta&include_ingredients=potatoes")
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

    def test_search_instructions(self, session_with_data):
        """Test searching recipes by instructions text."""
        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override
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

    def test_delete_recipe_success(self, session_with_data: Session):
        """Test successfully deleting a recipe."""
        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override
        # Get an existing recipe from the database
        db_recipe = session_with_data.exec(select(Recipe)).first()
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
            select(RecipeIngredientLink).where(RecipeIngredientLink.recipe_id == recipe_id)
        ).all()
        assert len(links) == 0

    def test_delete_nonexistent_recipe(self, session_with_data: Session):
        """Test deleting a non-existent recipe."""
        def get_session_override():
            return session_with_data

        app.dependency_overrides[get_session] = get_session_override
        # Use a non-existent ID (e.g., 9999)
        response = client.delete("/recipes/9999")
        assert response.status_code == 404  # Not Found