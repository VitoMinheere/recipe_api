import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.app.database.models import Ingredient, Recipe, RecipeIngredientLink


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


@pytest.fixture(name="session_with_data")
def session_with_data_fixture():
    """Create a test database session with pre-populated data."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create ingredients
        pasta = Ingredient(name="pasta")
        eggs = Ingredient(name="eggs")
        bacon = Ingredient(name="bacon")
        potatoes = Ingredient(name="potatoes")
        onion = Ingredient(name="onion")
        salmon = Ingredient(name="salmon")

        session.add_all([pasta, eggs, bacon, potatoes, onion, salmon])
        session.commit()

        # Create recipes
        carbonara = Recipe(
            name="Pasta Carbonara",
            instructions="Cook pasta. Mix eggs and cheese. Add bacon.",
            servings=2,
            vegetarian=False,
        )
        stir_fry = Recipe(
            name="Vegetable Stir Fry",
            instructions="Stir fry vegetables with soy sauce.",
            servings=3,
            vegetarian=True,
        )
        salmon_bake = Recipe(
            name="Salmon Bake",
            instructions="Bake salmon with potato and herbs.",
            servings=4,
            vegetarian=False,
        )

        session.add_all([carbonara, stir_fry, salmon_bake])
        session.commit()

        # Create links
        carbonara_links = [
            RecipeIngredientLink(recipe_id=carbonara.id, ingredient_id=pasta.id),
            RecipeIngredientLink(recipe_id=carbonara.id, ingredient_id=eggs.id),
            RecipeIngredientLink(recipe_id=carbonara.id, ingredient_id=bacon.id),
        ]
        stir_fry_links = [
            RecipeIngredientLink(recipe_id=stir_fry.id, ingredient_id=potatoes.id),
            RecipeIngredientLink(recipe_id=stir_fry.id, ingredient_id=onion.id),
        ]
        salmon_bake_links = [
            RecipeIngredientLink(recipe_id=salmon_bake.id, ingredient_id=potatoes.id),
            RecipeIngredientLink(recipe_id=salmon_bake.id, ingredient_id=salmon.id),
        ]

        session.add_all(carbonara_links + stir_fry_links + salmon_bake_links)
        session.commit()

        # Refresh objects to load relationships
        session.refresh(carbonara)
        session.refresh(stir_fry)
        session.refresh(salmon_bake)

        yield session

    SQLModel.metadata.drop_all(engine)
