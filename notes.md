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

Once I got the vegetarian filter working, the servings part was easy to add. THe including filter took some more time but due to the link table setup I could use the logical approach of getting the Ingredient ids and then filtering over them. For the exclude list this caused issues because I did the following test:

"/recipes/?exclude_ingredients=pasta"

I assumed it would only return the Vegetable Stir Fry as pasta was out but it still returned the pasta as eggs and bacon were not excluded. My first approach to fix this was to get a list of recipe ids with the ingredient and filter those out. I could do this by getting the Ingredient id and getting the Recipe id which is connected to that Ingredient. After that I can query all Recipes excluding the list of ids.

After setting up the include and exclude filters it was then up to the unit tests to prove that combining them also works. As all the filter wind up as WHERE clauses, none of them should clash and it would be simple to pinpoint the result.

Last part in the GET was the search in text. I opted for a basic text search due to time constraints and simplicity. Ideally there would be a setup with a dedicated table which is optimized for text search with a link to the Recipe id. However this would require an extra call whenever the instructions of a Recipe get updated.

## Update Recipe

For the PUT/PATCH I first went for updating the Recipe object and then later on also taking care of the Ingredients and RecipeIngredientsLink. I opted for an endpoint where the full object can be updated at once or just one of the fields. The PAtch should not delete Ingredients as they can be used by different Recipes, it should only delete the Links. This approach could lead to orphaned Ingredients in the table but a daily or weekly scan for Ingredients not in the RecipeIngredientsLink and then cleaning them up could fix that.

While creating the unit tests for the Patch, I noticed I missed a test case for when the ingredients in a Recipe are empty. I added that in with a field_validator and then also added validation on the other fields.
