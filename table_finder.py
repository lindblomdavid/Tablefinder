"""
Database Table Value Finder
Searches for a specific value across all tables and columns in a SQL Server database.
"""

import os
import sys
import pyodbc
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()


def get_connection_string() -> str:
    """Build SQL Server connection string from environment variables."""
    host = os.getenv('DATABASE__HOST', 'localhost')
    port = os.getenv('DATABASE__PORT', '1433')
    database = os.getenv('DATABASE__DATABASE')
    user = os.getenv('DATABASE__USER')
    password = os.getenv('DATABASE__PASSWORD')

    if not all([database, user, password]):
        raise ValueError("Missing required environment variables. Check .env file.")

    # Try to find best available SQL Server ODBC driver
    drivers = pyodbc.drivers()
    preferred_drivers = [
        'ODBC Driver 18 for SQL Server',
        'ODBC Driver 17 for SQL Server',
        'ODBC Driver 13 for SQL Server',
        'SQL Server Native Client 11.0',
        'SQL Server'
    ]

    driver = None
    for pref_driver in preferred_drivers:
        if pref_driver in drivers:
            driver = pref_driver
            break

    if not driver:
        raise Exception(f"No suitable SQL Server ODBC driver found. Available: {drivers}")

    # SQL Server connection string
    conn_str = (
        f'DRIVER={{{driver}}};'
        f'SERVER={host},{port};'
        f'DATABASE={database};'
        f'UID={user};'
        f'PWD={password};'
        f'TrustServerCertificate=yes;'
    )
    return conn_str


def get_connection():
    """Get a connection to the database."""
    try:
        conn_str = get_connection_string()
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as e:
        print(f"Error connecting to database: {e}")
        print("\nAvailable ODBC drivers:")
        for driver in pyodbc.drivers():
            print(f"  - {driver}")
        raise


def get_all_tables(conn, table_pattern: Optional[str] = None) -> List[str]:
    """
    Get all table names from the database.

    Args:
        conn: Database connection
        table_pattern: Optional SQL LIKE pattern to filter tables (e.g., 'ny%')

    Returns:
        List of table names in format 'schema.table'
    """
    cursor = conn.cursor()

    query = """
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_TYPE = 'BASE TABLE'
    """

    if table_pattern:
        query += f" AND TABLE_NAME LIKE '{table_pattern}'"

    query += " ORDER BY TABLE_SCHEMA, TABLE_NAME"

    cursor.execute(query)
    tables = [f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}" for row in cursor.fetchall()]
    cursor.close()

    return tables


def get_table_columns(conn, schema: str, table: str) -> List[Dict[str, str]]:
    """
    Get all columns for a specific table.

    Returns:
        List of dicts with column info: {'name': str, 'type': str}
    """
    cursor = conn.cursor()

    query = """
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
    ORDER BY ORDINAL_POSITION
    """

    cursor.execute(query, schema, table)
    columns = [
        {'name': row.COLUMN_NAME, 'type': row.DATA_TYPE}
        for row in cursor.fetchall()
    ]
    cursor.close()

    return columns


def should_skip_column(data_type: str) -> bool:
    """
    Determine if a column type should be skipped for search.
    Skip binary, image, and other non-searchable types.
    """
    skip_types = ['image', 'binary', 'varbinary', 'timestamp', 'rowversion', 'geography', 'geometry']
    return data_type.lower() in skip_types


def search_in_table(
    conn,
    schema: str,
    table: str,
    search_value: str,
    case_sensitive: bool = False,
    exact_match: bool = False
) -> List[Dict[str, Any]]:
    """
    Search for a value in all searchable columns of a table.

    Returns:
        List of matches with table, column, and sample matched values
    """
    results = []

    try:
        columns = get_table_columns(conn, schema, table)
        searchable_columns = [col for col in columns if not should_skip_column(col['type'])]

        if not searchable_columns:
            return results

        cursor = conn.cursor()
        full_table_name = f"[{schema}].[{table}]"

        for column in searchable_columns:
            col_name = column['name']

            # Build search query with CAST to handle different data types
            if exact_match:
                if case_sensitive:
                    where_clause = f"CAST([{col_name}] AS NVARCHAR(MAX)) = ?"
                else:
                    where_clause = f"CAST([{col_name}] AS NVARCHAR(MAX)) COLLATE Latin1_General_CI_AS = ?"
            else:
                if case_sensitive:
                    where_clause = f"CAST([{col_name}] AS NVARCHAR(MAX)) LIKE ?"
                    search_param = f"%{search_value}%"
                else:
                    where_clause = f"CAST([{col_name}] AS NVARCHAR(MAX)) COLLATE Latin1_General_CI_AS LIKE ?"
                    search_param = f"%{search_value}%"

            # First check if any rows match
            count_query = f"SELECT COUNT(*) FROM {full_table_name} WHERE {where_clause}"

            try:
                if exact_match:
                    cursor.execute(count_query, search_value)
                else:
                    cursor.execute(count_query, search_param)

                count = cursor.fetchone()[0]

                if count > 0:
                    # Get sample values (limit to 5 examples)
                    sample_query = f"SELECT TOP 5 [{col_name}] FROM {full_table_name} WHERE {where_clause}"

                    if exact_match:
                        cursor.execute(sample_query, search_value)
                    else:
                        cursor.execute(sample_query, search_param)

                    sample_values = [str(row[0]) if row[0] is not None else 'NULL' for row in cursor.fetchall()]

                    results.append({
                        'table': full_table_name,
                        'column': col_name,
                        'data_type': column['type'],
                        'match_count': count,
                        'sample_values': sample_values
                    })

            except pyodbc.Error as e:
                # Skip columns that cause errors (e.g., conversion issues)
                pass

        cursor.close()

    except pyodbc.Error as e:
        # Skip tables that cause errors
        pass

    return results


def format_results(results: List[Dict[str, Any]], search_value: str) -> str:
    """Format search results for console output."""
    if not results:
        return f"\nNo matches found for '{search_value}'"

    output = [f"\n{'='*80}"]
    output.append(f"Found {len(results)} column(s) containing '{search_value}'")
    output.append(f"{'='*80}\n")

    for i, result in enumerate(results, 1):
        output.append(f"{i}. {result['table']}.{result['column']}")
        output.append(f"   Data Type: {result['data_type']}")
        output.append(f"   Match Count: {result['match_count']}")
        output.append(f"   Sample Values:")
        for val in result['sample_values']:
            # Truncate long values
            display_val = val[:100] + '...' if len(val) > 100 else val
            output.append(f"     - {display_val}")
        output.append("")

    return "\n".join(output)


def save_results_to_file(results: List[Dict[str, Any]], output_file: str, search_value: str):
    """Save results to a JSON file."""
    output_data = {
        'search_value': search_value,
        'timestamp': datetime.now().isoformat(),
        'total_matches': len(results),
        'results': results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Search for a value across all tables in a SQL Server database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python table_finder.py "John Doe"
  python table_finder.py "12345" --exact
  python table_finder.py "test" --case-sensitive --table-pattern "ny%"
  python table_finder.py "value" --start-from "cmem" --skip-tables "cmlog"
  python table_finder.py "value" --stop-on-first
  python table_finder.py "value" --output results.json
        """
    )

    parser.add_argument('search_value', help='Value to search for')
    parser.add_argument('--exact', action='store_true', help='Search for exact matches only')
    parser.add_argument('--case-sensitive', action='store_true', help='Case-sensitive search')
    parser.add_argument('--table-pattern', help='SQL LIKE pattern to filter tables (e.g., "ny%%")')
    parser.add_argument('--start-from', help='Start searching from this table name, then continue with all others')
    parser.add_argument('--skip-tables', help='Comma-separated list of table names to skip (e.g., "cmlog,temp")')
    parser.add_argument('--stop-on-first', action='store_true', help='Stop searching after finding the first match')
    parser.add_argument('--output', help='Save results to JSON file')

    args = parser.parse_args()

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
        print(f"Found {len(tables)} tables to search\n")

        # Parse skip tables list
        skip_tables_list = []
        if args.skip_tables:
            skip_tables_list = [t.strip().lower() for t in args.skip_tables.split(',')]

        # Reorder tables based on start-from parameter and apply skip list
        if args.start_from:
            start_table = args.start_from.lower()
            start_index = None

            # Find the start table
            for i, table in enumerate(tables):
                table_name_only = table.split('.')[-1].lower()
                if table_name_only == start_table:
                    start_index = i
                    break

            if start_index is not None:
                # Reorder: start table first, then rest of tables, then tables before start
                reordered_tables = tables[start_index:] + tables[:start_index]
                tables = reordered_tables
                print(f"Starting with table '{args.start_from}', then continuing through all others")
            else:
                print(f"Warning: Table '{args.start_from}' not found. Searching in default order.")

        # Filter out skipped tables
        if skip_tables_list:
            original_count = len(tables)
            tables = [t for t in tables if t.split('.')[-1].lower() not in skip_tables_list]
            skipped_count = original_count - len(tables)
            print(f"Skipping {skipped_count} table(s): {', '.join(skip_tables_list)}")

        print(f"Searching {len(tables)} tables\n")

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
