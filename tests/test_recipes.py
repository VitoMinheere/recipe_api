from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

def test_create_recipe():
    recipe_data = {
        "name": "Pasta Carbonara",
        "ingredients": ["pasta", "eggs", "cheese", "bacon"],
        "instructions": "Cook pasta. Mix eggs and cheese. Add bacon. Combine.",
        "servings": 2,
        "vegetarian": False
    }

    response = client.post("/recipes/", json=recipe_data)

    assert response.status_code == 201
    assert response.json()["name"] == "Pasta Carbonara"
    assert response.json()["servings"] == 2
