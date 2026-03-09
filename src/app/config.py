"""
Application configuration using Pydantic settings management.
"""
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        database_url: Database connection URL
        debug: Debug mode flag
        test_mode: Test mode flag
    """
    database_url: str = Field(
        default="sqlite:///recipes.db",
        json_schema_extra={"env": "DATABASE_URL"},
        description="Database connection URL"
    )
    debug: bool = Field(
        default=False,
        json_schema_extra={"env": "DEBUG"},
        description="Enable debug mode"
    )

    class ConfigDict:
        """
        Pydantic BaseSettings configuration.

        Attributes:
            env_file: Path to .env file
            env_file_encoding: Encoding for .env file
        """
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a singleton instance of the settings
settings = Settings()
