## Create recipe
Moving from a Pydantic model to a SQLModel required thinking about how to handle the list of ingredients.
I could use a JSON field however other requirements include filtering on those values which would require a check of every row to see if it has that value in the JSON field.

Another approach is to make a separate class for Ingredient, they can be added to the Recipe model using a relationship. This would require a table to link  them and a many to many relationship as ingredients can be in multiple recipes and recipes contain multiple ingredients. At a large scale this could result in a huge table but it can be mitigated for now by using indexes in that table.