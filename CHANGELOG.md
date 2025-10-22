# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### Added
- Initial release of TableFinder
- Interactive mode for search value input
- Search across all tables and columns in SQL Server databases
- Case-sensitive and case-insensitive search options
- Exact match and partial match (LIKE) search modes
- Table filtering with SQL LIKE patterns
- Start from specific table and loop through all others
- Skip specific tables functionality
- Stop on first match option for faster searches
- Progress tracking for large databases
- Sample values display (up to 5 per column)
- JSON export functionality
- Automatic skipping of binary/unsearchable column types
- Modular package structure with proper Python best practices
- Type hints throughout codebase
- Comprehensive error handling
- Console script entry point (`table-finder` command)
- Support for Python 3.8+
- Cross-platform support (Windows, Linux, macOS)

### Documentation
- Comprehensive README with usage examples
- Setup instructions for all platforms
- ODBC driver installation guide
- Advanced use case scenarios
- Module structure documentation
- Performance tips and optimization guide

### Infrastructure
- `.gitignore` for Python projects
- `setup.py` for package installation
- `requirements.txt` for dependencies
- MIT License
