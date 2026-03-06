import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from src.app.database import get_session
from src.app.main import app
from src.app.routes.recipes import Ingredient, Recipe, RecipeIngredientLink

client = TestClient(app)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_recipe(session: Session):
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

    # 1. Check the recipe exists in the database
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

def test_create_recipe_missing_data():
    """Test 422 error for missing required fields."""
    invalid_data = {
        "name": "Incomplete Recipe",
        # Missing ingredients, instructions, servings, vegetarian
    }
    response = client.post("/recipes/", json=invalid_data)
    assert response.status_code == 422

def test_create_recipe_server_error(mocker, session: Session):
    """Test 500 error on database failure."""
    mocker.patch("src.app.routes.recipes.Session.commit", side_effect=Exception("DB error"))
    recipe_data = {
        "name": "Test Recipe",
        "ingredients": ["test"],
        "instructions": "Test instructions",
        "servings": 1,
        "vegetarian": True,
    }
    with pytest.raises(Exception, match="DB error"):
        response = client.post("/recipes/", json=recipe_data)
        assert response.status_code == 500
        assert "Failed to create recipe" in response.json()["detail"]