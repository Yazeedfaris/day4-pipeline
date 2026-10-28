```markdown
# Maintenance Assets CRUD API

A FastAPI-based CRUD API for managing maintenance assets with CSV storage.

## Features

- Create, read, update, and delete maintenance assets
- Filter assets by status, unit, and criticality
- Soft deletion support
- Input validation for asset IDs and criticality levels
- CSV-based data persistence

## Requirements

- Python 3.9+
- FastAPI
- Uvicorn
- Pydantic v2
- Pytest

## Installation

```bash
pip install fastapi uvicorn pydantic pytest
```

## Running the Application

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Endpoints

### POST /assets

Create a new asset.

**Request Body:**
```json
{
  "asset_id": "ABC-1234",
  "asset_type": "Pump",
  "unit": "Unit A",
  "location": "Building 1",
  "install_year": 2020,
  "last_inspection": "2023-01-15",
  "operating_hours": 1500.5,
  "status": "Active",
  "criticality": "High",
  "notes": "Regular maintenance required"
}
```

### GET /assets

List all assets with optional filters.

**Query Parameters:**
- `status` (optional): Filter by status
- `unit` (optional): Filter by unit
- `criticality` (optional): Filter by criticality

### GET /assets/{asset_id}

Retrieve a specific asset by ID.

### PUT /assets/{asset_id}

Update an existing asset.

**Request Body:**
```json
{
  "status": "Inactive",
  "operating_hours": 2000.0
}
```

### DELETE /assets/{asset_id}

Delete an asset (soft deletion).

## Data Validation

- `asset_id` must match the pattern `XXX-nnnn` (e.g., ABC-1234)
- `criticality` must be one of: High, Medium, Low
- Returns 404 when an asset is not found
- Changes to `asset_id` are rejected

## Testing

```bash
pytest -q
```

## Data Storage

Assets are stored in `maintenance_assets.csv` with the following fields:
- asset_id
- asset_type
- unit
- location
- install_year
- last_inspection
- operating_hours
- status
- criticality
- notes
- is_deleted
```