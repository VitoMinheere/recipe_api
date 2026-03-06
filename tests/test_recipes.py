from fastapi.testclient import TestClient
from src.app.main import app
from src.app.database import get_session
from src.app.routes.recipes import Recipe, Ingredient, RecipeIngredientLink
import pytest
from sqlmodel import create_engine, Session, SQLModel, select
from sqlmodel.pool import StaticPool

client = TestClient(app)

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool)
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
        "vegetarian": False
    }

    response = client.post("/recipes/", json=recipe_data)

    # Assert the response is correct
    assert response.status_code == 201
    created_recipe = response.json()
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
    assert len(links) == 3 