
from typing import List, Annotated, Optional
from pydantic import BaseModel, field_validator

class RecipeModel(BaseModel):
    id: int | None = None
    name: str
    ingredients: List[str]
    instructions: str
    servings: int
    vegetarian: bool

    @field_validator('name')
    def name_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Recipe name cannot be empty')
        return v.strip()

    @field_validator('instructions')
    def instructions_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Instructions cannot be empty')
        return v.strip()

    @field_validator('servings')
    def servings_positive(cls, v):
        if v <= 0:
            raise ValueError('Servings must be a positive integer')
        return v

    @field_validator('ingredients')
    def ingredients_not_empty(cls, v):
        if not v:
            raise ValueError('At least one ingredient is required')
        for ingredient in v:
            if not ingredient or len(ingredient.strip()) == 0:
                raise ValueError('Ingredient names cannot be empty')
        return [i.strip() for i in v]

class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    instructions: Optional[str] = None
    servings: Optional[int] = None
    vegetarian: Optional[bool] = None
    ingredients: Optional[List[str]] = None

    @field_validator('name')
    def name_not_empty(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('Recipe name cannot be empty')
        return v.strip() if v else None

    @field_validator('instructions')
    def instructions_not_empty(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('Instructions cannot be empty')
        return v.strip() if v else None

    @field_validator('servings')
    def servings_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Servings must be a positive integer')
        return v

    @field_validator('ingredients')
    def ingredients_not_empty(cls, v):
        if v is not None:
            if not v:
                raise ValueError('At least one ingredient is required')
            for ingredient in v:
                if not ingredient or len(ingredient.strip()) == 0:
                    raise ValueError('Ingredient names cannot be empty')
            return [i.strip() for i in v]
        return v

