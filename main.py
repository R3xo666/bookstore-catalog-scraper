"""CLI entrypoint for Bookstore Catalog Scraper."""

import argparse
import json
import logging
import os
from pathlib import Path
import signal
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from src.crawler import BookCatalogCrawler
from src.exporter import export_dataset
from src.models import BookItem, ScraperConfig

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def parse_arguments() -> argparse.Namespace:
    """Parse command line options.

    Returns:
        Populated Namespace object with arguments.
    """
    parser = argparse.ArgumentParser(
        description="Production-grade bookstore catalog scraper and normalizer."
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config/config.json",
        help="Path to JSON configuration file (default: config/config.json)",
    )
    parser.add_argument(
        "--url",
        "-u",
        type=str,
        default=None,
        help="Override starting URL",
    )
    parser.add_argument(
        "--pages",
        "-p",
        type=int,
        default=None,
        help="Override maximum pages to scrape (0 for all pages)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Override output directory for exported files",
    )
    parser.add_argument(
        "--base-name",
        "-b",
        type=str,
        default=None,
        help="Custom base filename without extension (e.g., 'sample_2pages')",
    )
    return parser.parse_args()


def load_configuration(config_path_str: str, args: argparse.Namespace) -> ScraperConfig:
    """Load configuration from JSON and apply CLI overrides.

    Args:
        config_path_str: File path to config.json.
        args: Parsed command-line arguments.

    Returns:
        Validated ScraperConfig instance.
    """
    raw_config: dict[str, Any] = {}
    config_file = Path(config_path_str)

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as file_handle:
                raw_config = json.load(file_handle)
        except json.JSONDecodeError as err:
            console.print(f"[bold red]Error parsing config file:[/bold red] {err}")
            sys.exit(1)
    else:
        logger.warning("Config file '%s' not found, using default configuration.", config_path_str)

    # CLI Overrides
    if args.url is not None:
        raw_config["start_url"] = args.url
    if args.pages is not None:
        raw_config["max_pages"] = args.pages
    if args.output is not None:
        raw_config["output_dir"] = args.output

    return ScraperConfig(**raw_config)


class ScraperApp:
    """Encapsulates the scraping lifecycle, progress tracking, and signal handling."""

    def __init__(self, config: ScraperConfig, base_name: str | None = None) -> None:
        self.config = config
        self.base_name = base_name
        self.accumulated_items: list[BookItem] = []
        self.interrupted = False
        self.crawler = BookCatalogCrawler(config)
        self._register_signals()

    def _register_signals(self) -> None:
        """Register graceful interrupt handlers for SIGINT and SIGTERM."""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, _frame: Any) -> None:
        """Handle interruption signal by setting flag and triggering immediate flush."""
        if self.interrupted:
            # Second interrupt forces immediate exit
            console.print("\n[bold red]Forced termination requested. Exiting.[/bold red]")
            sys.exit(1)

        self.interrupted = True
        console.print("\n[bold yellow]Interrupt signal received (Ctrl+C). Flushing collected items...[/bold yellow]")
        self._flush_and_exit()

    def _flush_and_exit(self) -> None:
        """Export collected items so far and terminate."""
        if self.accumulated_items:
            csv_path, excel_path = export_dataset(
                items=self.accumulated_items,
                output_dir=self.config.output_dir,
                base_filename=self.base_name,
            )
            console.print(
                Panel.fit(
                    f"[green]Flushed {len(self.accumulated_items)} items before exiting:[/green]\n"
                    f"• CSV: [bold cyan]{csv_path}[/bold cyan]\n"
                    f"• Excel: [bold cyan]{excel_path}[/bold cyan]",
                    title="Graceful Exit",
                )
            )
        else:
            console.print("[yellow]No items collected before interrupt.[/yellow]")
        self.crawler.close()
        sys.exit(0)

    def run(self) -> None:
        """Execute the crawling workflow with an interactive Rich progress bar."""
        console.print(
            Panel(
                f"[bold cyan]Target URL:[/bold cyan] {self.config.start_url}\n"
                f"[bold cyan]Max Pages:[/bold cyan] {'Unlimited' if self.config.max_pages == 0 else self.config.max_pages}\n"
                f"[bold cyan]Throttling:[/bold cyan] {self.config.delay_min}s - {self.config.delay_max}s\n"
                f"[bold cyan]Output Directory:[/bold cyan] {self.config.output_dir}",
                title="[bold green]Bookstore Catalog Scraper[/bold green]",
                border_style="green",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            total_steps = self.config.max_pages if self.config.max_pages > 0 else None
            task = progress.add_task(
                "[cyan]Crawling catalog...",
                total=total_steps,
            )

            for page_url, books in self.crawler.crawl_catalog():
                if self.interrupted:
                    break

                self.accumulated_items.extend(books)
                progress.update(
                    task,
                    advance=1,
                    description=f"[cyan]Crawled {page_url.split('/')[-1]} (+{len(books)} books, total: {len(self.accumulated_items)})",
                )

        console.print(f"\n[bold green]Completed crawling![/bold green] Total books collected: {len(self.accumulated_items)}")

        # Final export
        csv_path, excel_path = export_dataset(
            items=self.accumulated_items,
            output_dir=self.config.output_dir,
            base_filename=self.base_name,
        )

        console.print(
            Panel.fit(
                f"• CSV: [bold cyan]{csv_path}[/bold cyan]\n"
                f"• Excel: [bold cyan]{excel_path}[/bold cyan]",
                title="[bold green]Datasets Exported Successfully[/bold green]",
                border_style="green",
            )
        )
        self.crawler.close()


def main() -> None:
    """Main CLI execution flow."""
    args = parse_arguments()
    config = load_configuration(args.config, args)
    app = ScraperApp(config, base_name=args.base_name)
    app.run()


if __name__ == "__main__":
    main()
