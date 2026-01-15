"""Logging configuration using Loguru.

Simple logging setup for DA workflows: console output by default, optional file logging.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from src.config.settings import settings


def setup_logger(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logger:
    """Configure logger with console output and optional file handler.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to settings.log_level.
        log_file: Path to log file. If None, logs only to console.
                  Defaults to settings.log_file.

    Returns:
        Configured logger instance.

    Example:
        >>> from src.utils.logger import setup_logger, logger
        >>> setup_logger()
        >>> logger.info("Application started")
    """
    # Use settings defaults if not provided
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file

    # Remove default handler
    logger.remove()

    # ========================================================================
    # Console Handler - Colorized output
    # ========================================================================
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # ========================================================================
    # File Handler - Optional, simple file logging
    # ========================================================================
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )

        logger.add(
            log_file,
            format=file_format,
            level=log_level,
            backtrace=True,
            diagnose=True,
        )
        logger.info(f"Logger initialized - Level: {log_level}, File: {log_file}")
    else:
        logger.info(f"Logger initialized - Level: {log_level}, Console only")

    return logger


def get_logger(name: str) -> logger:
    """Get a logger instance with a specific name.

    Args:
        name: Logger name (typically __name__ of the module).

    Returns:
        Logger instance bound to the specified name.

    Example:
        >>> from src.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Module started")
    """
    return logger.bind(name=name)


# Initialize logger on import
setup_logger()


# ============================================================================
# Convenience functions for common logging patterns
# ============================================================================

def log_function_call(func_name: str, **kwargs) -> None:
    """Log a function call with its arguments.

    Args:
        func_name: Name of the function being called.
        **kwargs: Function arguments to log.
    """
    logger.debug(f"Calling {func_name}", extra={"function": func_name, "args": kwargs})


def log_execution_time(func_name: str, duration: float) -> None:
    """Log function execution time.

    Args:
        func_name: Name of the function.
        duration: Execution time in seconds.
    """
    logger.info(
        f"{func_name} completed in {duration:.2f}s",
        extra={"function": func_name, "duration": duration}
    )


def log_data_operation(operation: str, record_count: int, **kwargs) -> None:
    """Log a data operation (extract, transform, load).

    Args:
        operation: Type of operation (e.g., "extract", "transform", "load").
        record_count: Number of records processed.
        **kwargs: Additional context.
    """
    logger.info(
        f"{operation.upper()}: {record_count} records",
        extra={"operation": operation, "records": record_count, **kwargs}
    )


def log_error_with_context(error: Exception, context: dict) -> None:
    """Log an error with additional context.

    Args:
        error: Exception that occurred.
        context: Dictionary with contextual information.
    """
    logger.error(
        f"Error: {str(error)}",
        extra={"error_type": type(error).__name__, "context": context}
    )
    logger.exception(error)


# ============================================================================
# Context managers for logging
# ============================================================================

from contextlib import contextmanager
import time


@contextmanager
def log_execution_context(operation: str):
    """Context manager to log operation execution time.

    Args:
        operation: Name of the operation being performed.

    Example:
        >>> with log_execution_context("data_loading"):
        ...     # Your code here
        ...     pass
    """
    start_time = time.time()
    logger.info(f"Starting {operation}")

    try:
        yield
        duration = time.time() - start_time
        logger.info(f"Completed {operation} in {duration:.2f}s")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed {operation} after {duration:.2f}s: {str(e)}")
        raise


if __name__ == "__main__":
    """Test logger configuration."""
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Test context manager
    with log_execution_context("test_operation"):
        import time
        time.sleep(0.5)

    # Test data operation logging
    log_data_operation("extract", 1000, source="API")

    logger.success("Logger test completed successfully!")
