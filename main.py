from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator, Field
from typing import Optional, List
import csv
import os
import re

app = FastAPI()

# Constants
CSV_FILE = 'maintenance_assets.csv'
ASSET_ID_PATTERN = re.compile(r'^[A-Z]{3}-\d{4}$')
VALID_CRITICALITY = {'High', 'Medium', 'Low'}

# Pydantic Models
class AssetBase(BaseModel):
    asset_type: str
    unit: str
    location: str
    install_year: int
    last_inspection: str
    operating_hours: float
    status: str
    criticality: str
    notes: Optional[str] = None

    @field_validator('criticality')
    @classmethod
    def validate_criticality(cls, v):
        if v not in VALID_CRITICALITY:
            raise ValueError('criticality must be one of: High, Medium, Low')
        return v

class AssetCreate(AssetBase):
    asset_id: str

    @field_validator('asset_id')
    @classmethod
    def validate_asset_id(cls, v):
        if not ASSET_ID_PATTERN.match(v):
            raise ValueError('asset_id must match pattern XXX-nnnn')
        return v

class AssetUpdate(BaseModel):
    asset_type: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    install_year: Optional[int] = None
    last_inspection: Optional[str] = None
    operating_hours: Optional[float] = None
    status: Optional[str] = None
    criticality: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('criticality')
    @classmethod
    def validate_criticality(cls, v):
        if v is not None and v not in VALID_CRITICALITY:
            raise ValueError('criticality must be one of: High, Medium, Low')
        return v

class Asset(AssetBase):
    asset_id: str
    is_deleted: bool = False

    @field_validator('asset_id')
    @classmethod
    def validate_asset_id(cls, v):
        if not ASSET_ID_PATTERN.match(v):
            raise ValueError('asset_id must match pattern XXX-nnnn')
        return v

# CSV Operations
def load_assets() -> List[dict]:
    assets = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                row['install_year'] = int(row['install_year'])
                row['operating_hours'] = float(row['operating_hours'])
                row['is_deleted'] = row.get('is_deleted', 'False') == 'True'
                assets.append(row)
    return assets

def save_assets(assets: List[dict]):
    if not assets:
        return
    fieldnames = list(assets[0].keys())
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for asset in assets:
            writer.writerow(asset)

# Initialize data
assets_db = load_assets()

@app.on_event('startup')
def startup_event():
    global assets_db
    assets_db = load_assets()

# Endpoints
@app.post('/assets', response_model=Asset, status_code=201)
async def create_asset(asset: AssetCreate):
    for existing in assets_db:
        if existing['asset_id'] == asset.asset_id and not existing['is_deleted']:
            raise HTTPException(status_code=400, detail='Asset with this ID already exists')
    new_asset = asset.model_dump()
    new_asset['is_deleted'] = False
    assets_db.append(new_asset)
    save_assets(assets_db)
    return new_asset

@app.get('/assets', response_model=List[Asset])
async def list_assets(
    asset_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    unit: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None)
):
    """Return non-deleted assets, optionally filtered by status, unit, or criticality."""
    result = [a for a in assets_db if not a['is_deleted']]
    if status:
        result = [a for a in result if a['status'] == status]
    if unit:
        result = [a for a in result if a['unit'] == unit]
    if criticality:
        result = [a for a in result if a['criticality'] == criticality]
    if asset_type:
        result = [a for a in result if a['asset_type'] == asset_type]
    
    return result

@app.get('/assets/{asset_id}', response_model=Asset)
async def get_asset(asset_id: str):
    for asset in assets_db:
        if asset['asset_id'] == asset_id and not asset['is_deleted']:
            return asset
    raise HTTPException(status_code=404, detail='Asset not found')

@app.put('/assets/{asset_id}', response_model=Asset)
async def update_asset(asset_id: str, asset_update: AssetUpdate):
    for asset in assets_db:
        if asset['asset_id'] == asset_id and not asset['is_deleted']:
            update_data = asset_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                asset[key] = value
            save_assets(assets_db)
            return asset
    raise HTTPException(status_code=404, detail='Asset not found')

@app.delete('/assets/{asset_id}', response_model=dict)
async def delete_asset(asset_id: str):
    for asset in assets_db:
        if asset['asset_id'] == asset_id and not asset['is_deleted']:
            asset['is_deleted'] = True
            save_assets(assets_db)
            return {'message': 'Asset deleted successfully'}
    raise HTTPException(status_code=404, detail='Asset not found')