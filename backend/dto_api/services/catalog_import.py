"""Catalog import service for handling various catalog sources."""

import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

import structlog

from dto_api.models.catalog import (
    CatalogPackage,
    CatalogImportRequest,
    CatalogImportResponse,
    CatalogDiff,
    Dataset,
    Column
)

logger = structlog.get_logger()


class CatalogImportService:
    """Service for importing and managing catalog data."""
    
    def __init__(self):
        # TODO: Initialize database connection
        self._catalogs: Dict[str, CatalogPackage] = {}
    
    async def import_catalog(self, request: CatalogImportRequest) -> CatalogImportResponse:
        """Import catalog from various sources."""
        try:
            catalog_id = str(uuid.uuid4())
            
            if request.source_type == "catalog_package":
                catalog = await self._import_catalog_package(request.data, request.environment)
            elif request.source_type == "dbt_manifest":
                catalog = await self._import_dbt_manifest(request.data, request.environment)
            elif request.source_type == "dbt_catalog":
                catalog = await self._import_dbt_catalog(request.data, request.environment)
            else:
                raise ValueError(f"Unsupported source type: {request.source_type}")
            
            # Generate signatures for datasets
            catalog.signatures = self._generate_signatures(catalog.datasets)
            
            # Store catalog (stub - would persist to database)
            self._catalogs[catalog_id] = catalog
            
            logger.info(
                "Catalog imported successfully",
                catalog_id=catalog_id,
                source_type=request.source_type,
                datasets_count=len(catalog.datasets)
            )
            
            return CatalogImportResponse(
                catalog_id=catalog_id,
                datasets_imported=len(catalog.datasets),
                warnings=[]
            )
            
        except Exception as e:
            logger.error("Catalog import failed", exc_info=e)
            raise
    
    async def get_catalog(self, catalog_id: str) -> Optional[CatalogPackage]:
        """Get catalog by ID."""
        # TODO: Retrieve from database
        return self._catalogs.get(catalog_id)
    
    async def compute_diff(self, catalog_id: str, prev_catalog_id: str) -> CatalogDiff:
        """Compute diff between two catalog versions."""
        current = await self.get_catalog(catalog_id)
        previous = await self.get_catalog(prev_catalog_id)
        
        if not current or not previous:
            raise ValueError("One or both catalogs not found")
        
        diff = CatalogDiff()
        
        # Get dataset names
        current_names = {ds.name for ds in current.datasets}
        previous_names = {ds.name for ds in previous.datasets}
        
        # Find added/removed datasets
        diff.added_datasets = list(current_names - previous_names)
        diff.removed_datasets = list(previous_names - current_names)
        
        # Find modified datasets
        common_names = current_names & previous_names
        current_by_name = {ds.name: ds for ds in current.datasets}
        previous_by_name = {ds.name: ds for ds in previous.datasets}
        
        for name in common_names:
            current_ds = current_by_name[name]
            previous_ds = previous_by_name[name]
            
            # Compare signatures
            current_sig = self._generate_dataset_signature(current_ds)
            previous_sig = self._generate_dataset_signature(previous_ds)
            
            if current_sig != previous_sig:
                diff.modified_datasets.append(name)
                
                # Detailed column diff
                current_cols = {col.name: col for col in current_ds.columns}
                previous_cols = {col.name: col for col in previous_ds.columns}
                
                added_cols = list(set(current_cols.keys()) - set(previous_cols.keys()))
                removed_cols = list(set(previous_cols.keys()) - set(current_cols.keys()))
                
                if added_cols:
                    diff.added_columns[name] = added_cols
                if removed_cols:
                    diff.removed_columns[name] = removed_cols
                
                # Type changes
                type_changes = {}
                for col_name in set(current_cols.keys()) & set(previous_cols.keys()):
                    if current_cols[col_name].type != previous_cols[col_name].type:
                        type_changes[col_name] = {
                            "from": previous_cols[col_name].type,
                            "to": current_cols[col_name].type
                        }
                
                if type_changes:
                    diff.type_changes[name] = type_changes
        
        return diff
    
    async def list_catalogs(
        self, 
        environment: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """List available catalogs."""
        # TODO: Implement database query with filters
        catalogs = []
        for catalog_id, catalog in self._catalogs.items():
            if environment and catalog.environment != environment:
                continue
            
            catalogs.append({
                "id": catalog_id,
                "version": catalog.version,
                "generated_at": catalog.generated_at.isoformat(),
                "environment": catalog.environment,
                "dataset_count": len(catalog.datasets)
            })
        
        # Apply pagination
        total = len(catalogs)
        paginated = catalogs[offset:offset + limit]
        
        return {
            "items": paginated,
            "total": total
        }
    
    async def _import_catalog_package(self, data: Dict, environment: str) -> CatalogPackage:
        """Import from Catalog Package JSON."""
        # Validate and parse catalog package
        catalog = CatalogPackage(**data)
        catalog.environment = environment
        return catalog
    
    async def _import_dbt_manifest(self, data: Dict, environment: str) -> CatalogPackage:
        """Import from dbt manifest.json."""
        datasets = []
        
        # Extract models from dbt manifest
        nodes = data.get("nodes", {})
        for node_id, node in nodes.items():
            if node.get("resource_type") == "model":
                # Convert dbt model to Dataset
                columns = []
                for col_name, col_info in node.get("columns", {}).items():
                    columns.append(Column(
                        name=col_name,
                        type=col_info.get("data_type", "STRING"),
                        nullable=True,  # Default assumption
                        description=col_info.get("description")
                    ))
                
                dataset = Dataset(
                    name=node.get("name", ""),
                    kind="view",  # dbt models are typically views
                    columns=columns,
                    lineage=list(node.get("depends_on", {}).get("nodes", []))
                )
                datasets.append(dataset)
        
        return CatalogPackage(
            generated_at=datetime.utcnow(),
            environment=environment,
            datasets=datasets
        )
    
    async def _import_dbt_catalog(self, data: Dict, environment: str) -> CatalogPackage:
        """Import from dbt catalog.json."""
        datasets = []
        
        # Extract tables from dbt catalog
        nodes = data.get("nodes", {})
        for node_id, node in nodes.items():
            columns = []
            for col_name, col_info in node.get("columns", {}).items():
                columns.append(Column(
                    name=col_name,
                    type=col_info.get("type", "STRING"),
                    nullable=True,  # Would need additional logic to determine
                    description=col_info.get("comment")
                ))
            
            dataset = Dataset(
                name=node.get("metadata", {}).get("name", ""),
                kind=node.get("metadata", {}).get("type", "table"),
                row_count_estimate=node.get("stats", {}).get("row_count", {}).get("value"),
                columns=columns
            )
            datasets.append(dataset)
        
        return CatalogPackage(
            generated_at=datetime.utcnow(),
            environment=environment,
            datasets=datasets
        )
    
    def _generate_signatures(self, datasets: List[Dataset]) -> Dict[str, str]:
        """Generate SHA256 signatures for datasets based on column list."""
        signatures = {}
        for dataset in datasets:
            signatures[dataset.name] = self._generate_dataset_signature(dataset)
        return signatures
    
    def _generate_dataset_signature(self, dataset: Dataset) -> str:
        """Generate SHA256 signature for a single dataset."""
        # Create deterministic string from columns
        column_info = []
        for col in sorted(dataset.columns, key=lambda x: x.name):
            column_info.append(f"{col.name}:{col.type}:{col.nullable}")
        
        signature_string = "|".join(column_info)
        return hashlib.sha256(signature_string.encode()).hexdigest()
