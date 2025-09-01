"""Catalog management endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import structlog

from dto_api.models.catalog import (
    CatalogPackage, 
    CatalogDiff, 
    CatalogImportRequest, 
    CatalogImportResponse
)
from dto_api.services.catalog_import import CatalogImportService

router = APIRouter()
logger = structlog.get_logger()


def get_catalog_service() -> CatalogImportService:
    """Dependency to get catalog import service."""
    return CatalogImportService()


@router.post("/catalog/import", response_model=CatalogImportResponse)
async def import_catalog(
    request: CatalogImportRequest,
    service: CatalogImportService = Depends(get_catalog_service)
) -> CatalogImportResponse:
    """Import catalog data from various sources."""
    try:
        logger.info(
            "Importing catalog",
            source_type=request.source_type,
            environment=request.environment
        )
        
        result = await service.import_catalog(request)
        
        logger.info(
            "Catalog import completed",
            catalog_id=result.catalog_id,
            datasets_imported=result.datasets_imported
        )
        
        return result
        
    except Exception as e:
        logger.error("Catalog import failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/catalog/{catalog_id}", response_model=CatalogPackage)
async def get_catalog(
    catalog_id: str,
    service: CatalogImportService = Depends(get_catalog_service)
) -> CatalogPackage:
    """Get catalog by ID."""
    try:
        catalog = await service.get_catalog(catalog_id)
        if not catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")
        return catalog
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get catalog", catalog_id=catalog_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get catalog: {str(e)}")


@router.get("/catalog/{catalog_id}/diff/{prev_catalog_id}", response_model=CatalogDiff)
async def get_catalog_diff(
    catalog_id: str,
    prev_catalog_id: str,
    service: CatalogImportService = Depends(get_catalog_service)
) -> CatalogDiff:
    """Get diff between two catalog versions."""
    try:
        logger.info(
            "Computing catalog diff",
            current_catalog=catalog_id,
            previous_catalog=prev_catalog_id
        )
        
        diff = await service.compute_diff(catalog_id, prev_catalog_id)
        
        return diff
        
    except Exception as e:
        logger.error(
            "Failed to compute catalog diff",
            current_catalog=catalog_id,
            previous_catalog=prev_catalog_id,
            exc_info=e
        )
        raise HTTPException(status_code=500, detail=f"Failed to compute diff: {str(e)}")


class CatalogListResponse(BaseModel):
    """Response for catalog listing."""
    
    catalogs: list[dict]
    total: int


@router.get("/catalog", response_model=CatalogListResponse)
async def list_catalogs(
    environment: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: CatalogImportService = Depends(get_catalog_service)
) -> CatalogListResponse:
    """List available catalogs."""
    try:
        catalogs = await service.list_catalogs(
            environment=environment,
            limit=limit,
            offset=offset
        )
        
        return CatalogListResponse(
            catalogs=catalogs["items"],
            total=catalogs["total"]
        )
        
    except Exception as e:
        logger.error("Failed to list catalogs", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to list catalogs: {str(e)}")
