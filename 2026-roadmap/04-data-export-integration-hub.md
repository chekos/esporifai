# Data Export & Integration Hub

**Category:** New Feature | Integration
**Quarter:** Q2
**T-shirt Size:** L

## Why This Matters

esporifai currently outputs JSON to stdout or files. That's useful, but users don't want JSON—they want insights. Data analysts need their listening data in Pandas DataFrames, SQLite databases, or Google Sheets. Researchers want CSV files they can import into R or SPSS. Developers want to pipe data directly into their analytics pipelines.

By becoming a universal data export hub, esporifai transforms from "a CLI that fetches Spotify data" into "the bridge between Spotify and your entire data ecosystem." This is a significant value-add that differentiates esporifai from simple API wrappers.

## Current State

- **Output formats:** JSON only
- **Output destinations:** stdout (`-`) or local files
- **Data transformation:** None—raw API responses
- **Schema handling:** No schema documentation or validation
- **Piping capability:** JSON to stdout works but limited
- **Batch export:** Sequential file creation, one per ID

Current export limitations:
```bash
esporifai get-audio-features --id FILE.txt --output ./
# Creates: id1.json, id2.json, id3.json...
# No combined export, no format options
```

## Proposed Future State

A comprehensive data export system supporting multiple formats and destinations:

**Output Formats:**
- JSON (current, enhanced with pretty-printing options)
- CSV with proper escaping and headers
- Parquet for columnar analytics
- SQLite database with proper schema
- Excel (.xlsx) with formatting
- Pandas DataFrame (Python API)
- Arrow format for interoperability
- JSONL (newline-delimited) for streaming

**Destinations:**
- Local files (current)
- SQLite database with append/replace modes
- PostgreSQL/MySQL direct insert
- Google Sheets via API
- AWS S3/GCS bucket upload
- Webhook POST for integrations
- Stdout with format selection

**Data Enhancement:**
- Flattened/normalized schemas for SQL
- Automatic schema generation
- Data validation and cleaning
- Timestamp normalization (UTC/local)
- Field selection and renaming

## Key Deliverables

- [ ] Add `--format` flag: `json`, `csv`, `parquet`, `sqlite`, `xlsx`, `jsonl`
- [ ] Implement CSV export with proper escaping and header detection
- [ ] Implement Parquet export using `pyarrow` or `fastparquet`
- [ ] Implement SQLite export with schema auto-creation
- [ ] Add Excel export using `openpyxl`
- [ ] Create JSONL streaming output for large datasets
- [ ] Add `--fields` flag for selecting specific fields
- [ ] Implement data flattening for nested JSON structures
- [ ] Add `--output-db` flag for database connection strings
- [ ] Create schema documentation for all Spotify data types
- [ ] Implement Google Sheets integration via `gspread`
- [ ] Add S3/GCS upload with `boto3`/`google-cloud-storage`
- [ ] Create webhook output for real-time integrations
- [ ] Add `--append` mode for incremental exports
- [ ] Implement deduplication based on ID fields
- [ ] Add Python library API returning DataFrames directly
- [ ] Create export profiles (saved configurations)

## Prerequisites

- Initiative 03 (Async Architecture) enables efficient batch exports
- Initiative 01 (Testing) provides confidence for new features

## Risks & Open Questions

- How many output formats before we bloat the package? Start with core formats (CSV, SQLite, Parquet)?
- Optional dependencies vs. required—should Parquet/Excel be extras (`pip install esporifai[export]`)?
- Database schema: should we normalize (multiple tables) or denormalize (single table)?
- Google Sheets rate limits—how to handle large exports?
- How to handle schema changes when Spotify API evolves?
- Should export profiles be in config file or separate JSON?

## Notes

New dependencies to consider (as extras):
- `pyarrow` - Parquet support
- `openpyxl` - Excel export
- `gspread` - Google Sheets
- `boto3` - AWS S3
- `google-cloud-storage` - GCS
- `sqlalchemy` - Database abstractions

Data type mappings needed:
- Spotify track → normalized schema
- Audio features → flat numeric table
- Artist → normalized with genres array handling
- Recently played → time-series format

Files to modify:
- `esporifai/cli.py` - Add format flags to all commands
- New: `esporifai/exporters/` module with format-specific exporters
- New: `esporifai/schemas/` for data type definitions
- `setup.py` - Add optional dependencies
