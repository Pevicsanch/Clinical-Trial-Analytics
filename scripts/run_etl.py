"""ETL Pipeline - Extract, Transform, Load.

Main script that orchestrates the complete ETL process.
"""

import sys
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.etl.extract import extract_raw_data
from src.etl.transform import transform_raw_data, transform_related_tables
from src.etl.validate import validate_data
from src.utils.logger import setup_logger

console = Console()


def main():
    """Run complete ETL pipeline."""
    # Setup logging
    setup_logger()

    console.print("\n[bold cyan]Clinical Trial Analytics - ETL Pipeline[/bold cyan]\n")

    try:
        # 1. EXTRACT
        console.print("[bold yellow]Step 1: Extract[/bold yellow]")
        console.print("Fetching data from ClinicalTrials.gov API...")
        data_file, metadata_file = extract_raw_data()
        console.print(f"[green]✓[/green] Raw data saved: {data_file.name}")
        console.print(f"[green]✓[/green] Metadata saved: {metadata_file.name}\n")

        # 2. TRANSFORM
        console.print("[bold yellow]Step 2: Transform[/bold yellow]")
        console.print("Transforming raw data to tabular format...")

        # First pass: transform studies
        transform_result = transform_raw_data(data_file)
        studies_data = transform_result["studies_raw"]

        console.print(f"[green]✓[/green] Transformed {len(studies_data)} studies\n")

        # 3. LOAD
        console.print("[bold yellow]Step 3: Load[/bold yellow]")
        console.print("Loading data into database...")

        # Load studies first to get study_id mapping
        from src.etl.load import get_engine, load_studies

        engine = get_engine()
        nct_id_to_study_id = load_studies(studies_data, engine)

        # Transform related tables (needs study_id mapping)
        related_data = transform_related_tables(data_file, nct_id_to_study_id)

        # Load related tables
        from src.etl.load import load_conditions, load_locations, load_sponsors

        conditions_count = load_conditions(related_data["conditions"], engine)
        locations_count = load_locations(related_data["locations"], engine)
        sponsors_count = load_sponsors(related_data["sponsors"], engine)

        load_counts = {
            "studies": len(nct_id_to_study_id),
            "conditions": conditions_count,
            "locations": locations_count,
            "sponsors": sponsors_count,
        }

        # Display results
        table = Table(title="Load Results")
        table.add_column("Table", style="cyan")
        table.add_column("Records", style="green", justify="right")

        for table_name, count in load_counts.items():
            table.add_row(table_name.capitalize(), str(count))

        console.print(table)
        console.print()

        # 4. VALIDATE
        console.print("[bold yellow]Step 4: Validate[/bold yellow]")
        console.print("Running validation checks...")

        validation_results = validate_data(engine)

        # Display validation summary
        val_table = Table(title="Validation Summary")
        val_table.add_column("Check", style="cyan")
        val_table.add_column("Result", style="green")

        val_table.add_row(
            "Studies loaded",
            str(validation_results["counts"]["studies"]),
        )
        val_table.add_row(
            "Unique NCT IDs",
            "✓" if validation_results["uniqueness"]["is_unique"] else "✗",
        )
        val_table.add_row(
            "Start date coverage",
            f"{validation_results['dates']['start_date_pct']}%",
        )
        val_table.add_row(
            "Date inconsistencies",
            str(validation_results["dates"]["date_inconsistencies"]),
        )

        console.print(val_table)
        console.print()

        console.print("[bold green]✓ ETL Pipeline completed successfully![/bold green]\n")
        console.print("Next steps:")
        console.print("  • Run [cyan]make sql[/cyan] to explore data")
        console.print("  • Run [cyan]make nb[/cyan] to start analysis\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]ETL pipeline interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        logger.exception("ETL pipeline failed")
        console.print(f"\n[red]Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
