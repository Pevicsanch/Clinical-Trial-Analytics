#!/usr/bin/env python3
"""Simple database setup script using sqlite3 directly."""

import sqlite3
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from rich.console import Console

console = Console()


def main():
    """Create database and execute SQL scripts."""
    db_path = Path(settings.db_path)

    # Remove existing database
    if db_path.exists():
        console.print(f"[yellow]Removing existing database: {db_path}[/yellow]")
        db_path.unlink()

    # Create database directory
    db_path.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]Creating database: {db_path}[/green]")

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Execute schema scripts
    schema_dir = Path("sql/schema")
    sql_files = sorted(schema_dir.glob("*.sql"))

    for sql_file in sql_files:
        console.print(f"[cyan]Executing: {sql_file.name}[/cyan]")
        sql_content = sql_file.read_text()
        cursor.executescript(sql_content)

    conn.commit()
    conn.close()

    console.print("\n[bold green]✓ Database created successfully![/bold green]")
    console.print(f"\nDatabase location: [cyan]{db_path}[/cyan]")

    # Verify tables
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    console.print(f"\n[bold]Tables created ({len(tables)}):[/bold]")
    for table in tables:
        console.print(f"  • {table[0]}")

    conn.close()


if __name__ == "__main__":
    main()
