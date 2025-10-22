"""
CLI entry point for TableFinder.

This module handles command-line arguments and orchestrates the search process.
"""

import sys
import argparse
from .db_connection import get_connection
from .search import get_all_tables, search_in_table
from .utils import format_results, save_results_to_file, filter_and_reorder_tables


def main():
    """Main entry point for the table finder CLI."""
    parser = argparse.ArgumentParser(
        description='Search for a value across all tables in a SQL Server database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m TableFinder                    # Interactive mode - prompts for search value
  python -m TableFinder "John Doe"
  python -m TableFinder "12345" --exact
  python -m TableFinder "test" --case-sensitive --table-pattern "ny%"
  python -m TableFinder "value" --start-from "cmem" --skip-tables "cmlog"
  python -m TableFinder "value" --stop-on-first
  python -m TableFinder "value" --output results.json
        """
    )

    parser.add_argument('search_value', nargs='?', help='Value to search for (optional - will prompt if not provided)')
    parser.add_argument('--exact', action='store_true', help='Search for exact matches only')
    parser.add_argument('--case-sensitive', action='store_true', help='Case-sensitive search')
    parser.add_argument('--table-pattern', help='SQL LIKE pattern to filter tables (e.g., "ny%%")')
    parser.add_argument('--start-from', help='Start searching from this table name, then continue with all others')
    parser.add_argument('--skip-tables', help='Comma-separated list of table names to skip (e.g., "cmlog,temp")')
    parser.add_argument('--stop-on-first', action='store_true', help='Stop searching after finding the first match')
    parser.add_argument('--output', help='Save results to JSON file')

    args = parser.parse_args()

    # Prompt for search value if not provided
    if not args.search_value:
        print(f"\n{'='*80}")
        print(f"Database Table Value Finder - Interactive Mode")
        print(f"{'='*80}\n")
        args.search_value = input("Enter the value to search for: ").strip()

        if not args.search_value:
            print("Error: Search value cannot be empty.")
            return 1
        print()

    # Print search configuration
    print(f"\n{'='*80}")
    print(f"Database Table Value Finder")
    print(f"{'='*80}")
    print(f"Search value: '{args.search_value}'")
    print(f"Exact match: {args.exact}")
    print(f"Case sensitive: {args.case_sensitive}")
    if args.table_pattern:
        print(f"Table pattern: {args.table_pattern}")
    if args.start_from:
        print(f"Starting from table: {args.start_from}")
    if args.skip_tables:
        print(f"Skipping tables: {args.skip_tables}")
    if args.stop_on_first:
        print(f"Stop on first match: Yes")
    print(f"{'='*80}\n")

    try:
        # Connect to database
        print("Connecting to database...")
        conn = get_connection()
        print("Connected successfully!\n")

        # Get all tables
        print("Fetching table list...")
        tables = get_all_tables(conn, args.table_pattern)
        print(f"Found {len(tables)} tables\n")

        # Filter and reorder tables
        tables, stats = filter_and_reorder_tables(
            tables,
            start_from=args.start_from,
            skip_tables=args.skip_tables
        )

        # Print filter statistics
        if stats['started_from']:
            print(f"Starting with table '{stats['started_from']}', then continuing through all others")
        if stats['skipped_count'] > 0:
            print(f"Skipping {stats['skipped_count']} table(s): {', '.join(stats['skipped_tables'])}")

        print(f"Searching {stats['final_count']} tables\n")

        # Search through all tables
        all_results = []

        for i, table in enumerate(tables, 1):
            schema, table_name = table.split('.')
            print(f"[{i}/{len(tables)}] Searching {table}...", end='\r')

            results = search_in_table(
                conn,
                schema,
                table_name,
                args.search_value,
                case_sensitive=args.case_sensitive,
                exact_match=args.exact
            )

            all_results.extend(results)

            # Stop on first match if flag is set
            if args.stop_on_first and all_results:
                print(f"\n\nFirst match found in {table}! Stopping search.")
                break

        print(f"\n{'='*80}")
        print(f"Search complete!")
        print(f"{'='*80}")

        # Display results
        print(format_results(all_results, args.search_value))

        # Save to file if requested
        if args.output:
            save_results_to_file(all_results, args.output, args.search_value)

        conn.close()

        return 0 if all_results else 1

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
