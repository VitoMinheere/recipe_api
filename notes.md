## Create recipe
Moving from a Pydantic model to a SQLModel required thinking about how to handle the list of ingredients.
I could use a JSON field however other requirements include filtering on those values which would require a check of every row to see if it has that value in the JSON field.

Another approach is to make a separate class for Ingredient, they can be added to the Recipe model using a relationship. This would require a table to link  them and a many to many relationship as ingredients can be in multiple recipes and recipes contain multiple ingredients. At a large scale this could result in a huge table but it can be mitigated for now by using indexes in that table.

### Table models
After going over some options I decided to go with the Recipe - Ingredient - RecipeIngredient Table setup. I opted to add the vegetarian bool to the ingredient so later on I could clasify Recipe as vegetarian when all the ingredients are vegetarian. After creating the test I decided against this as it would require users to set it for every ingredient which would require a complicated Request.

The create recipe endpoint is now also creating Ingredients and links between Ingredients and the Recipe. If any of those calls fail, the Database will be filled with useless data and that will add up quickly. A rollback mechanism can be applied to mitigate this.
Did not get the test for the rollback working due to issue with Mocking. Might get back to it later

## Get Recipe

Second endpoint to work on was the GET. First to get all recipes and then to add the filtering on ingredients.
Made another fixture to session with pre added Recipes and Ingredients to make it easier to test and to make sure I am not also testing the POST request in the GET test scenario's.