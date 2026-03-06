# recipe_api
A REST API for managing recipes

# Recipe API

A FastAPI-based API for managing recipes.

## Setup

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

### Clone the repo:
   ```bash
   git clone https://github.com/VitoMinheere/recipe_api
   cd recipe_api
   ```

### Install Dependencies
Use uv to install dependencies from pyproject.toml: 
    ```bash
    uv pip install -e .

### Run the application
Start the FastAPI server with Uvicorn:
    ```bash
    uvicorn src.app.main\:app --reload

### Access the API
Open the interactive API documentation (Swagger UI) at:
http://localhost:8000/docs
