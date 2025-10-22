"""Utility functions for formatting and file operations."""

import json
from datetime import datetime
from typing import List, Dict, Any


def format_results(results: List[Dict[str, Any]], search_value: str) -> str:
    """
    Format search results for console output.

    Args:
        results: List of search result dictionaries
        search_value: The value that was searched for

    Returns:
        Formatted string for display
    """
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


def save_results_to_file(results: List[Dict[str, Any]], output_file: str, search_value: str) -> None:
    """
    Save results to a JSON file.

    Args:
        results: List of search result dictionaries
        output_file: Path to output file
        search_value: The value that was searched for
    """
    output_data = {
        'search_value': search_value,
        'timestamp': datetime.now().isoformat(),
        'total_matches': len(results),
        'results': results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")


def filter_and_reorder_tables(
    tables: List[str],
    start_from: str = None,
    skip_tables: str = None
) -> tuple[List[str], Dict[str, Any]]:
    """
    Filter and reorder tables based on start-from and skip parameters.

    Args:
        tables: List of table names
        start_from: Table name to start from
        skip_tables: Comma-separated list of tables to skip

    Returns:
        Tuple of (filtered_tables, stats_dict)
    """
    stats = {
        'original_count': len(tables),
        'skipped_count': 0,
        'final_count': 0,
        'started_from': None,
        'skipped_tables': []
    }

    # Parse skip tables list
    skip_tables_list = []
    if skip_tables:
        skip_tables_list = [t.strip().lower() for t in skip_tables.split(',')]
        stats['skipped_tables'] = skip_tables_list

    # Reorder tables based on start-from parameter
    if start_from:
        start_table = start_from.lower()
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
            stats['started_from'] = start_from

    # Filter out skipped tables
    if skip_tables_list:
        original_count = len(tables)
        tables = [t for t in tables if t.split('.')[-1].lower() not in skip_tables_list]
        stats['skipped_count'] = original_count - len(tables)

    stats['final_count'] = len(tables)

    return tables, stats
