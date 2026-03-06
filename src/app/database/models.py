from sqlmodel import Field, Session, SQLModel, select

class RecipeIngredientLink(SQLModel, table=True):
    recipe_id: int = Field(foreign_key="recipe.id", primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredient.id", primary_key=True)


class Recipe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    instructions: str = Field()
    servings: int = Field()
    vegetarian: bool = Field()


class Ingredient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str