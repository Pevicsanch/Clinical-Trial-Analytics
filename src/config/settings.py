"""Application settings and configuration.

This module provides centralized configuration management using Pydantic settings.
All configuration values can be overridden via environment variables.
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden by creating a .env file in the project root.
    See .env.example for available configuration options.
    """

    # ========================================================================
    # API Configuration
    # ========================================================================
    api_base_url: str = "https://clinicaltrials.gov/api/v2"
    api_page_size: int = 10000  # Reduced to avoid WAF blocking (can increase after testing)
    api_max_records: int = 100000
    api_timeout: int = 10

    # ========================================================================
    # Database Configuration
    # ========================================================================
    db_path: str = "data/database/clinical_trials.db"
    db_echo: bool = False

    @property
    def database_url(self) -> str:
        """Get SQLAlchemy database URL."""
        return f"sqlite:///{self.db_path}"

    # ========================================================================
    # Logging Configuration
    # ========================================================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: str | None = None  # Optional: if None, logs to console only

    # ========================================================================
    # Computed Properties
    # ========================================================================
    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return self.project_root / "data"

    @property
    def raw_data_dir(self) -> Path:
        """Get raw data directory path."""
        return self.data_dir / "raw"

    @property
    def interim_data_dir(self) -> Path:
        """Get interim data directory path."""
        return self.data_dir / "interim"

    @property
    def processed_data_dir(self) -> Path:
        """Get processed data directory path."""
        return self.data_dir / "processed"

    @property
    def database_dir(self) -> Path:
        """Get database directory path."""
        return self.data_dir / "database"

    @property
    def logs_dir(self) -> Path:
        """Get logs directory path."""
        return self.project_root / "logs"

    # ========================================================================
    # Pydantic Configuration
    # ========================================================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def ensure_directories(self) -> None:
        """Create all necessary directories if they don't exist."""
        directories = [
            self.raw_data_dir,
            self.interim_data_dir,
            self.processed_data_dir,
            self.database_dir,
            self.logs_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()


if __name__ == "__main__":
    """Print current configuration for debugging."""
    import json

    config_dict = {
        "API Configuration": {
            "base_url": settings.api_base_url,
            "page_size": settings.api_page_size,
            "max_records": settings.api_max_records,
        },
        "Database": {
            "path": settings.db_path,
            "url": settings.database_url,
        },
        "Logging": {
            "level": settings.log_level,
            "file": settings.log_file or "console",
        },
        "Paths": {
            "project_root": str(settings.project_root),
            "data_dir": str(settings.data_dir),
            "logs_dir": str(settings.logs_dir),
        }
    }

    print("Current Configuration:")
    print(json.dumps(config_dict, indent=2))
