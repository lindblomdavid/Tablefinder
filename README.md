# Table Finder

A Python package to search for specific values across all tables and columns in a SQL Server database. Perfect for undocumented databases with hundreds or thousands of tables.

## Key Features

### Search Capabilities
- **Interactive Mode**: Run without arguments and get prompted for search value
- **Flexible Matching**: Case-sensitive/insensitive, exact or partial (LIKE) searches
- **Smart Type Handling**: Automatically converts all data types to strings for comparison
- **Binary Column Skip**: Automatically skips unsearchable types (images, timestamps, etc.)

### Performance & Control
- **Stop on First Match**: Quick exit when you find what you need
- **Table Filtering**: Use SQL LIKE patterns to search specific tables only
- **Table Reordering**: Start from any table and loop through all others
- **Skip Tables**: Exclude log, audit, or temporary tables from search
- **Progress Tracking**: Real-time progress indicator for large databases

### Output Options
- **Rich Console Output**: Shows table.column, data type, match count, and sample values
- **JSON Export**: Save results to file for further analysis
- **Sample Values**: View up to 5 example matches per column

### Architecture
- **Modular Design**: Clean separation of concerns (connection, search, utils)
- **Type Hints**: Full type annotations for better code quality
- **Error Handling**: Graceful handling of access errors and data type issues

## Project Structure

```
TableFinder/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point
├── db_connection.py     # Database connection utilities
├── search.py            # Search functionality
├── utils.py             # Utility functions (formatting, file I/O)
├── table_finder.py      # Standalone script (backwards compatibility)
├── setup.py             # Package installation configuration
├── requirements.txt     # Python dependencies
├── .env                 # Database configuration (not in version control)
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## Requirements

- **Python**: 3.8 or higher (tested on 3.8, 3.9, 3.10, 3.11, 3.12)
- **SQL Server ODBC Driver**: ODBC Driver 13+ for SQL Server (automatically detected)
- **Operating System**: Windows, Linux, or macOS

## Setup

### 1. Verify Python Version
```bash
python --version  # Should be 3.8 or higher
```

### 2. Install the Package

**Option A: Install as editable package (recommended for development)**
```bash
cd TableFinder
pip install -e .
```

After installation, you can run from anywhere:
```bash
table-finder "search_value"
```

**Option B: Install dependencies only**
```bash
pip install -r requirements.txt
```

Then run with:
```bash
python -m TableFinder "search_value"
```

**Dependencies:**
- `pyodbc>=5.0.0` - SQL Server connectivity
- `python-dotenv>=1.0.0` - Environment variable management

### 3. Install SQL Server ODBC Driver (if not already installed)

**Windows**: Usually pre-installed. If not:
- Download from [Microsoft ODBC Driver Downloads](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

**Linux/macOS**:
```bash
# Check available drivers
python -c "import pyodbc; print(pyodbc.drivers())"
```
If no drivers found, follow [Microsoft's installation guide](https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server).

### 4. Configure Database Connection
Create a `.env` file in the TableFinder directory:
```env
DATABASE__HOST=your_host
DATABASE__PORT=1433
DATABASE__USER=your_username
DATABASE__PASSWORD=your_password
DATABASE__DATABASE=your_database
```

**Security Note**: Never commit the `.env` file to version control!

## Usage

### Running the Package

**If installed with `pip install -e .`:**
```bash
table-finder [search_value] [options]
```

**If using without installation (module mode):**
```bash
python -m TableFinder [search_value] [options]
```

**Or using the standalone script (backwards compatibility):**
```bash
python table_finder.py [search_value] [options]
```

### Usage Examples

#### 1. Interactive Mode (Recommended for Ad-Hoc Searches)
```bash
python -m TableFinder
```
**Output:**
```
================================================================================
Database Table Value Finder - Interactive Mode
================================================================================

Enter the value to search for: your_search_value
```

This mode prompts you to enter the search value, making it perfect for quick, interactive searches.

#### 2. Basic Command-Line Search
```bash
python -m TableFinder "search_value"
```

#### 3. Exact Match (Faster)
```bash
python -m TableFinder "12345" --exact
```

#### 4. Case-Sensitive Search
```bash
python -m TableFinder "John" --case-sensitive
```

#### 5. Filter Tables by Pattern
Search only tables matching a SQL LIKE pattern:
```bash
python -m TableFinder "value" --table-pattern "ny%"
```

#### 6. Start from Specific Table + Skip Others
Start from table "cmem", then continue through all other tables, but skip "cmlog":
```bash
python -m TableFinder "value" --start-from "cmem" --skip-tables "cmlog"
```

#### 7. Stop on First Match (Fastest)
Perfect for large databases when you just need to find one occurrence:
```bash
python -m TableFinder "value" --stop-on-first
```

#### 8. Interactive Mode with Options
Run in interactive mode but with preset options:
```bash
python -m TableFinder --start-from "cmem" --skip-tables "cmlog" --stop-on-first
# Will prompt: Enter the value to search for:
```

#### 9. Export Results to JSON
```bash
python -m TableFinder "value" --output results.json
```

#### 10. Full Example with All Options
```bash
python -m TableFinder "John Doe" --exact --case-sensitive --start-from "cmem" --skip-tables "cmlog,audit_log" --stop-on-first --output search_results.json
```

### Command-Line Options

| Option | Description |
|--------|-------------|
| `search_value` | Value to search for (optional - prompts if not provided) |
| `--exact` | Search for exact matches only (faster than LIKE) |
| `--case-sensitive` | Perform case-sensitive search |
| `--table-pattern` | SQL LIKE pattern to filter tables (e.g., `"ny%"`) |
| `--start-from` | Start searching from this table, then loop through all others |
| `--skip-tables` | Comma-separated list of tables to skip (e.g., `"cmlog,temp"`) |
| `--stop-on-first` | Stop immediately after finding first match |
| `--output` | Save results to JSON file |

## Output

The tool displays:
- Total number of matching columns
- Table and column names where matches were found
- Data type of each column
- Count of matching rows
- Sample values (up to 5 examples per column)

Example output:
```
================================================================================
Found 3 column(s) containing 'John'
================================================================================

1. dbo.customers.first_name
   Data Type: varchar
   Match Count: 15
   Sample Values:
     - John
     - Johnny
     - Johnson

2. dbo.employees.full_name
   Data Type: nvarchar
   Match Count: 3
   Sample Values:
     - John Smith
     - John Doe
     - Mary Johnson
```

## Performance Tips

### For Fastest Results
1. **`--stop-on-first`** - Stops immediately after finding first match (recommended for large databases)
2. **`--exact`** - Uses `=` instead of `LIKE` (faster than partial matching)
3. **`--skip-tables`** - Exclude large log/audit tables (e.g., `"cmlog,audit_log,temp_*"`)

### For Efficient Searches
4. **`--table-pattern`** - Limit search to specific table patterns (e.g., `"ny%"` for tables starting with "ny")
5. **`--start-from`** - Resume from a specific table if previous search was interrupted
6. **Interactive Mode** - Use for ad-hoc searches without typing long commands

### General Notes
- Tool automatically skips binary columns (images, timestamps, varbinary, etc.)
- Typical performance: ~10-50 tables/second depending on table size and complexity
- For 1300+ table databases: expect 1-5 minutes for full scan (or seconds with `--stop-on-first`)

## How It Works

1. Connects to the SQL Server database using credentials from `.env`
2. Queries `INFORMATION_SCHEMA.TABLES` to get all table names
3. Optionally reorders tables based on `--start-from` parameter
4. Filters out tables specified in `--skip-tables`
5. For each table, queries `INFORMATION_SCHEMA.COLUMNS` to get column information
6. Searches each column by casting values to string and using SQL LIKE or = operators
7. Collects and displays all matches with sample values
8. Optionally stops after first match if `--stop-on-first` is set

## Module Structure

The package follows Python best practices with a modular architecture:

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| **`db_connection.py`** | Database connectivity | `get_connection()`, ODBC driver detection |
| **`search.py`** | Search operations | `get_all_tables()`, `search_in_table()`, `get_table_columns()` |
| **`utils.py`** | Utilities & formatting | `format_results()`, `save_results_to_file()`, `filter_and_reorder_tables()` |
| **`__main__.py`** | CLI entry point | `main()`, argument parsing, interactive mode |
| **`__init__.py`** | Package initialization | Version info, package metadata |

### Why This Structure?
- **Separation of Concerns**: Each module has a single, clear responsibility
- **Testability**: Easy to unit test individual modules
- **Maintainability**: Changes to one area don't affect others
- **Reusability**: Can import modules independently for custom scripts

## Error Handling

The package handles errors gracefully:

- **Connection Errors**: Clear messages with available ODBC drivers listed
- **Access Errors**: Automatically skips tables/columns with permission issues
- **Type Conversion**: Handles all data types by casting to NVARCHAR
- **Partial Failures**: Continues searching even if individual queries fail
- **Empty Input**: Validates search value is not empty in interactive mode

## Advanced Use Cases

### Scenario 1: Finding Unknown Customer Data
```bash
# You have a customer ID but don't know which table it's in
python -m TableFinder "CUST-12345" --exact --stop-on-first
```

### Scenario 2: Searching Recent Tables Only
```bash
# Search only tables that match a pattern
python -m TableFinder "John Doe" --table-pattern "2024%" --stop-on-first
```

### Scenario 3: Resuming Interrupted Search
```bash
# Start from where you left off, skip problematic tables
python -m TableFinder "value" --start-from "customers" --skip-tables "large_log_table"
```

### Scenario 4: Documenting Database Schema
```bash
# Find all tables containing a specific foreign key
python -m TableFinder "user_id" --output schema_analysis.json
```

## Backwards Compatibility

For users of the original script, backwards compatibility is maintained:
```bash
python table_finder.py "search_value"
```

**Recommendation**: Migrate to the module approach for better Python integration:
```bash
python -m TableFinder "search_value"
```

## Contributing & Extending

The modular design makes it easy to extend functionality:

1. **Custom Search Logic**: Modify `search.py`
2. **New Output Formats**: Add functions to `utils.py`
3. **Additional Database Types**: Extend `db_connection.py`
4. **New CLI Options**: Update `__main__.py`

Example: Adding CSV export support would only require changes to `utils.py` and a new argument in `__main__.py`.
