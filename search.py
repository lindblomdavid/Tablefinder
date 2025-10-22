"""Search functionality for finding values across database tables."""

import pyodbc
from typing import List, Dict, Any, Optional


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

    Args:
        conn: Database connection
        schema: Table schema name
        table: Table name

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

    Args:
        data_type: SQL data type name

    Returns:
        True if column should be skipped, False otherwise
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

    Args:
        conn: Database connection
        schema: Table schema name
        table: Table name
        search_value: Value to search for
        case_sensitive: Whether to perform case-sensitive search
        exact_match: Whether to search for exact matches only

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

            except pyodbc.Error:
                # Skip columns that cause errors (e.g., conversion issues)
                pass

        cursor.close()

    except pyodbc.Error:
        # Skip tables that cause errors
        pass

    return results
