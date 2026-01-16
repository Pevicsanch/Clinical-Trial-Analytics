#!/usr/bin/env python3
"""ETL Pipeline - Extract, Transform, Load.

Orchestrates the complete ETL process:
1) Extract from ClinicalTrials.gov API (raw JSONL + metadata)
2) Transform raw JSONL into tabular structures
3) Load into SQLite database
4) Validate data quality checks

Usage:
    python scripts/run_etl.py
    python scripts/run_etl.py --max-records 20000
"""

import argparse
import sys
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.table import Table

# Add project root to path (so src imports work when running as script)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.etl.extract import extract_raw_data
from src.etl.transform import transform_raw_data, transform_related_tables
from src.etl.validate import validate_data
from src.utils.logger import setup_logger

console = Console()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Clinical Trial Analytics - ETL Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help=f"Maximum number of records to fetch (default: {settings.api_max_records} from settings)",
    )
    return parser.parse_args()


def main() -> None:
    """Run complete ETL pipeline."""
    args = parse_args()

    # Setup logging early
    setup_logger()

    console.print("\n[bold cyan]Clinical Trial Analytics - ETL Pipeline[/bold cyan]\n")

    # Resolve max_records from CLI or settings
    max_records = args.max_records if args.max_records is not None else settings.api_max_records
    console.print(f"[bold]Configuration[/bold]")
    console.print(f"  • max_records: [cyan]{max_records:,}[/cyan]")
    console.print(f"  • page_size:   [cyan]{settings.api_page_size:,}[/cyan]")
    console.print(f"  • db_path:     [cyan]{settings.db_path}[/cyan]\n")

    try:
        # ---------------------------------------------------------------------
        # 1) EXTRACT
        # ---------------------------------------------------------------------
        console.print("[bold yellow]Step 1: Extract[/bold yellow]")
        console.print("Fetching data from ClinicalTrials.gov API...")

        try:
            data_file, metadata_file = extract_raw_data(max_records=max_records)
        except Exception as e:
            # If the API fails mid-pagination (e.g. 400 invalid pageToken), fail gracefully
            console.print("\n[red]Extraction failed.[/red]")
            console.print(
                "[yellow]Tip:[/yellow] If you requested a very large sample (e.g. 100k), "
                "ClinicalTrials.gov may return 400 for a pageToken after deep pagination. "
                "Try a smaller max-records (e.g. 10k–30k) or rerun later."
            )
            logger.exception("Extraction failed")
            raise

        console.print(f"[green]✓[/green] Raw data saved: {data_file.name}")
        console.print(f"[green]✓[/green] Metadata saved: {metadata_file.name}\n")

        # ---------------------------------------------------------------------
        # 2) TRANSFORM
        # ---------------------------------------------------------------------
        console.print("[bold yellow]Step 2: Transform[/bold yellow]")
        console.print("Transforming raw data to tabular format...")

        transform_result = transform_raw_data(data_file)
        studies_data = transform_result["studies_raw"]

        console.print(f"[green]✓[/green] Transformed {len(studies_data):,} studies\n")

        # ---------------------------------------------------------------------
        # 3) LOAD
        # ---------------------------------------------------------------------
        console.print("[bold yellow]Step 3: Load[/bold yellow]")
        console.print("Loading data into database...")

        from src.etl.load import get_engine, load_studies, load_conditions, load_locations, load_sponsors

        engine = get_engine()

        # Load studies first to get nct_id -> study_id mapping
        nct_id_to_study_id = load_studies(studies_data, engine)

        # Transform related tables (needs study_id mapping)
        related_data = transform_related_tables(data_file, nct_id_to_study_id)

        # Load related tables
        conditions_count = load_conditions(related_data["conditions"], engine)
        locations_count = load_locations(related_data["locations"], engine)
        sponsors_count = load_sponsors(related_data["sponsors"], engine)

        load_counts = {
            "studies": len(nct_id_to_study_id),
            "conditions": conditions_count,
            "locations": locations_count,
            "sponsors": sponsors_count,
        }

        table = Table(title="Load Results")
        table.add_column("Table", style="cyan")
        table.add_column("Records", style="green", justify="right")
        for table_name, count in load_counts.items():
            table.add_row(table_name.capitalize(), f"{count:,}")
        console.print(table)
        console.print()

        # ---------------------------------------------------------------------
        # 4) VALIDATE
        # ---------------------------------------------------------------------
        console.print("[bold yellow]Step 4: Validate[/bold yellow]")
        console.print("Running validation checks...")

        validation_results = validate_data(engine)

        val_table = Table(title="Validation Summary")
        val_table.add_column("Check", style="cyan")
        val_table.add_column("Result", style="green")
        val_table.add_row("Studies loaded", f"{validation_results['counts']['studies']:,}")
        val_table.add_row("Unique NCT IDs", "✓" if validation_results["uniqueness"]["is_unique"] else "✗")
        val_table.add_row("Start date coverage", f"{validation_results['dates']['start_date_pct']}%")
        val_table.add_row("Date inconsistencies", str(validation_results["dates"]["date_inconsistencies"]))
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
        console.print(f"\n[red]Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()