# Recipe Management API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready RESTful API for managing recipes with filtering capabilities.

## Features

-  **Complete CRUD Operations** - Create, read, update, and delete recipes
-  **Advanced Filtering** - Filter by vegetarian status, servings, ingredients, and text search
-  **Input Validation** - Comprehensive validation for all fields
-  **Error Handling** - Proper error responses and status codes
-  **Configuration** - Environment-based configuration
-  **Documentation** - Interactive API documentation with Swagger UI
-  **Testing** - Comprehensive unit and integration tests

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Further Improvements](#further-improvements)
- [License](#license)

---

## Requirements

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) (for dependency management)
- SQLite (included with Python)

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/VitoMinheere/recipe_api.git
   cd recipe_api
   ```

2. Install dependencies using UV:

   ```bash
   uv pip install -e .
   ```

---

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory:

```env
# Database configuration
DATABASE_URL=sqlite:///recipes.db

# Application settings
DEBUG=False
```

> **Note**: The `.env` file is included in `.gitignore` and won't be committed to version control.

---

## Running the Application

Start the FastAPI server with Uvicorn:

```bash
uvicorn src.app.main:app --reload
```

For production, use:

```bash
uvicorn src.app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

---

## API Documentation

After starting the application, access the interactive API documentation (Swagger UI) at:

📖 [http://localhost:8000/docs](http://localhost:8000/docs)

This provides a complete interface to explore and test all API endpoints.

---

## Usage Examples

### Create a Recipe

```bash
curl -X POST "http://localhost:8000/recipes/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spaghetti Carbonara",
    "instructions": "Cook pasta. Mix eggs and cheese. Add bacon. Combine.",
    "servings": 2,
    "vegetarian": false,
    "ingredients": ["spaghetti", "eggs", "bacon", "cheese"]
  }'
```

### Get All Recipes

```bash
curl "http://localhost:8000/recipes/"
```

### Filter Recipes

```bash
# Get vegetarian recipes
curl "http://localhost:8000/recipes/?vegetarian=true"

# Get recipes with specific ingredients
curl "http://localhost:8000/recipes/?include_ingredients=potatoes,carrots"

# Search recipes by instructions
curl "http://localhost:8000/recipes/?search=oven"
```

### Update a Recipe (Partial Update)

```bash
curl -X PATCH "http://localhost:8000/recipes/1" \
  -H "Content-Type: application/json" \
  -d '{"servings": 4}'
```

### Delete a Recipe

```bash
curl -X DELETE "http://localhost:8000/recipes/1"
```

---

## Testing

Run the test suite with:

```bash
pytest tests/
```

### Test Coverage

To run tests with coverage:

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Project Structure

```
recipe_api/
├── src/
│   ├── app/
│   │   ├── main.py          # Application entry point
│   │   ├── database/        # Database models and session
│   │   ├── models/          # Pydantic models and validators
│   │   ├── routes/          # API routes
│   │   ├── services/        # Code that gets reused in other parts
│   │   └── config.py        # Configuration management
│   └── ...
├── tests/
│   ├── unit/               # Unit tests
│   ├── integration/         # Integration tests
│   └── conftest.py          # Test fixtures
├── pyproject.toml          # Project configuration and dependencies
├── README.md                # This file
└── .env                     # Environment variables (not committed)
```

---

## Further Improvements

For a production environment, consider these enhancements:

### Database
- **PostgreSQL Migration**: Replace SQLite with PostgreSQL for better performance and scalability
- **Connection Pooling**: Implement connection pooling for better database performance
- **Migrations**: Use Alembic for database migrations to handle schema changes

### API
- **Pagination**: Implement pagination for recipe listings
- **Authentication**: Add JWT authentication to secure endpoints
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Caching**: Add caching for frequently accessed recipes
- **Versioning**: Implement API versioning for backward compatibility

### Deployment
- **Docker**: Containerize the application for easy deployment
- **Logging**: Implement structured logging for monitoring
- **Health Checks**: Add health check endpoints

### Search
- **Full-Text Search**: Implement advanced full-text search capabilities
- **Advanced Filtering**: Add more filtering options (e.g., by cooking time, difficulty)

### Monitoring
- **Metrics**: Add metrics collection for performance monitoring
- **Tracing**: Implement request tracing for debugging
- **Error Reporting**: Set up error reporting for production issues

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```