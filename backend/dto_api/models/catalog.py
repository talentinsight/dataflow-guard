"""Catalog Package and related models."""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Column(BaseModel):
    """Column definition in a dataset."""
    
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Column data type")
    nullable: bool = Field(default=True, description="Whether column can be null")
    description: Optional[str] = Field(None, description="Column description")


class ForeignKey(BaseModel):
    """Foreign key constraint definition."""
    
    columns: List[str] = Field(..., description="Local columns")
    ref: str = Field(..., description="Referenced table(column) e.g. 'DIM.CUSTOMER(CUSTOMER_ID)'")


class Dataset(BaseModel):
    """Dataset (table/view) definition."""
    
    name: str = Field(..., description="Fully qualified dataset name")
    kind: Literal["table", "view"] = Field(..., description="Dataset type")
    row_count_estimate: Optional[int] = Field(None, description="Estimated row count")
    columns: List[Column] = Field(..., description="Column definitions")
    primary_key: List[str] = Field(default_factory=list, description="Primary key columns")
    foreign_keys: List[ForeignKey] = Field(default_factory=list, description="Foreign key constraints")
    watermark_column: Optional[str] = Field(None, description="Watermark column for freshness")
    lineage: List[str] = Field(default_factory=list, description="Upstream dependencies")


class CatalogPackage(BaseModel):
    """Catalog Package - authoritative metadata for test builders."""
    
    version: str = Field(default="1.0", description="Catalog package version")
    generated_at: datetime = Field(..., description="Generation timestamp")
    environment: Literal["dev", "stage", "prod"] = Field(..., description="Environment")
    datasets: List[Dataset] = Field(..., description="Dataset definitions")
    signatures: Dict[str, str] = Field(
        default_factory=dict, 
        description="Dataset signatures (sha256 of column list)"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CatalogDiff(BaseModel):
    """Catalog diff between two versions."""
    
    added_datasets: List[str] = Field(default_factory=list)
    removed_datasets: List[str] = Field(default_factory=list)
    modified_datasets: List[str] = Field(default_factory=list)
    added_columns: Dict[str, List[str]] = Field(default_factory=dict)
    removed_columns: Dict[str, List[str]] = Field(default_factory=dict)
    type_changes: Dict[str, Dict[str, Dict[str, str]]] = Field(default_factory=dict)


class CatalogImportRequest(BaseModel):
    """Request to import catalog data."""
    
    source_type: Literal["catalog_package", "dbt_manifest", "dbt_catalog"] = Field(
        ..., description="Type of catalog source"
    )
    data: Dict = Field(..., description="Catalog data payload")
    environment: str = Field(default="dev", description="Target environment")


class CatalogImportResponse(BaseModel):
    """Response from catalog import."""
    
    catalog_id: str = Field(..., description="Generated catalog ID")
    datasets_imported: int = Field(..., description="Number of datasets imported")
    warnings: List[str] = Field(default_factory=list, description="Import warnings")
