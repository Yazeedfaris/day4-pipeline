from pydantic import BaseModel, field_validator
from typing import Optional

VALID_CRITICALITY = {'High', 'Medium', 'Low'}

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
        import re
        if not re.match(r'^[A-Z]{3}-\d{4}$', v):
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
        import re
        if not re.match(r'^[A-Z]{3}-\d{4}$', v):
            raise ValueError('asset_id must match pattern XXX-nnnn')
        return v