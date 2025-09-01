"""Test planning and proposal service."""

from typing import List, Dict, Any

import structlog

from dto_api.models.tests import (
    ProposeRequest,
    ProposeResponse,
    TestProposal,
    TestDefinition
)

logger = structlog.get_logger()


class TestPlannerService:
    """Service for test planning and AI-powered test proposals."""
    
    def __init__(self):
        # TODO: Initialize AI adapter and catalog service dependencies
        pass
    
    async def propose_tests(self, request: ProposeRequest) -> ProposeResponse:
        """Generate AI-proposed tests for datasets."""
        try:
            logger.info(
                "Generating test proposals",
                datasets=request.datasets,
                profile=request.profile,
                layers=request.layers
            )
            
            proposals = []
            
            for dataset in request.datasets:
                dataset_proposals = await self._propose_for_dataset(
                    dataset, request.profile, request.catalog_id
                )
                proposals.extend(dataset_proposals)
            
            # Count auto-approvable proposals
            auto_approvable_count = sum(1 for p in proposals if p.auto_approvable)
            
            logger.info(
                "Test proposals generated",
                total_proposals=len(proposals),
                auto_approvable=auto_approvable_count
            )
            
            return ProposeResponse(
                proposals=proposals,
                total_proposed=len(proposals),
                auto_approvable_count=auto_approvable_count
            )
            
        except Exception as e:
            logger.error("Test proposal failed", exc_info=e)
            raise
    
    async def _propose_for_dataset(
        self, 
        dataset: str, 
        profile: str, 
        catalog_id: str
    ) -> List[TestProposal]:
        """Propose tests for a single dataset."""
        proposals = []
        
        # TODO: Get dataset schema from catalog service
        # For now, use mock logic based on dataset name patterns
        
        layer = self._detect_layer(dataset)
        
        if layer == "RAW":
            proposals.extend(await self._propose_raw_tests(dataset, profile))
        elif layer == "PREP":
            proposals.extend(await self._propose_prep_tests(dataset, profile))
        elif layer == "MART":
            proposals.extend(await self._propose_mart_tests(dataset, profile))
        
        return proposals
    
    def _detect_layer(self, dataset: str) -> str:
        """Detect dataset layer from name."""
        dataset_upper = dataset.upper()
        if dataset_upper.startswith("RAW."):
            return "RAW"
        elif dataset_upper.startswith("PREP.") or dataset_upper.startswith("STAGE."):
            return "PREP"
        elif dataset_upper.startswith("MART.") or dataset_upper.startswith("DIM.") or dataset_upper.startswith("FACT."):
            return "MART"
        else:
            return "UNKNOWN"
    
    async def _propose_raw_tests(self, dataset: str, profile: str) -> List[TestProposal]:
        """Propose tests for RAW layer datasets."""
        proposals = []
        
        # Primary key uniqueness (high confidence, auto-approvable for standard+)
        proposals.append(TestProposal(
            test_def=TestDefinition(
                name=f"pk_uniqueness_{dataset.lower().replace('.', '_')}",
                type="uniqueness",
                dataset=dataset,
                keys=["ORDER_ID"],  # TODO: Get from schema
                tolerance={"dup_rows": 0},
                severity="blocker",
                gate="fail"
            ),
            rationale="Primary key uniqueness is critical for data integrity",
            confidence=0.95,
            auto_approvable=profile in ["standard", "deep"]
        ))
        
        # Not null checks for key columns
        proposals.append(TestProposal(
            test_def=TestDefinition(
                name=f"not_null_key_{dataset.lower().replace('.', '_')}",
                type="not_null",
                dataset=dataset,
                keys=["ORDER_ID"],
                severity="blocker",
                gate="fail"
            ),
            rationale="Key columns should never be null",
            confidence=0.90,
            auto_approvable=profile in ["standard", "deep"]
        ))
        
        # Freshness check (if profile includes it)
        if profile in ["standard", "deep"]:
            proposals.append(TestProposal(
                test_def=TestDefinition(
                    name=f"freshness_{dataset.lower().replace('.', '_')}",
                    type="freshness",
                    dataset=dataset,
                    window={"last_hours": 24},
                    severity="major",
                    gate="warn"
                ),
                rationale="Data should be fresh within SLA",
                confidence=0.80,
                auto_approvable=False  # Requires SLA validation
            ))
        
        # Row count stability (deep profile)
        if profile == "deep":
            proposals.append(TestProposal(
                test_def=TestDefinition(
                    name=f"row_count_stability_{dataset.lower().replace('.', '_')}",
                    type="row_count",
                    dataset=dataset,
                    tolerance={"pct": 10.0},
                    severity="major",
                    gate="warn"
                ),
                rationale="Row count should be stable within expected range",
                confidence=0.70,
                auto_approvable=False  # Requires historical analysis
            ))
        
        return proposals
    
    async def _propose_prep_tests(self, dataset: str, profile: str) -> List[TestProposal]:
        """Propose tests for PREP layer datasets."""
        proposals = []
        
        # Schema contract tests
        proposals.append(TestProposal(
            test_def=TestDefinition(
                name=f"schema_contract_{dataset.lower().replace('.', '_')}",
                type="schema",
                dataset=dataset,
                severity="blocker",
                gate="fail"
            ),
            rationale="Schema should match expected contract",
            confidence=0.95,
            auto_approvable=True
        ))
        
        # Business rule consistency (if dataset suggests calculations)
        if "ORDER" in dataset.upper():
            proposals.append(TestProposal(
                test_def=TestDefinition(
                    name=f"total_consistency_{dataset.lower().replace('.', '_')}",
                    type="rule",
                    expression="order_total == items_total + tax + shipping",
                    dataset=dataset,
                    tolerance={"abs": 0.01},
                    severity="major",
                    gate="fail"
                ),
                rationale="Order totals should equal sum of components",
                confidence=0.85,
                auto_approvable=profile in ["deep"]
            ))
        
        # Foreign key integrity
        proposals.append(TestProposal(
            test_def=TestDefinition(
                name=f"fk_integrity_{dataset.lower().replace('.', '_')}",
                type="reconciliation",
                dataset=dataset,
                expression="customer_id references DIM.CUSTOMER",
                severity="major",
                gate="fail"
            ),
            rationale="Foreign key references should be valid",
            confidence=0.80,
            auto_approvable=False  # Requires schema analysis
        ))
        
        return proposals
    
    async def _propose_mart_tests(self, dataset: str, profile: str) -> List[TestProposal]:
        """Propose tests for MART layer datasets."""
        proposals = []
        
        # Dimension completeness
        if "DIM." in dataset.upper():
            proposals.append(TestProposal(
                test_def=TestDefinition(
                    name=f"dim_completeness_{dataset.lower().replace('.', '_')}",
                    type="not_null",
                    dataset=dataset,
                    keys=["business_key"],  # TODO: Get from schema
                    severity="major",
                    gate="fail"
                ),
                rationale="Dimension business keys should be complete",
                confidence=0.90,
                auto_approvable=True
            ))
        
        # Fact-dimension coverage
        if "FACT." in dataset.upper():
            proposals.append(TestProposal(
                test_def=TestDefinition(
                    name=f"fact_dim_coverage_{dataset.lower().replace('.', '_')}",
                    type="reconciliation",
                    dataset=dataset,
                    expression="All dimension keys exist in dimension tables",
                    severity="major",
                    gate="fail"
                ),
                rationale="Fact records should have valid dimension references",
                confidence=0.85,
                auto_approvable=False  # Requires cross-table analysis
            ))
        
        # Aggregation consistency (deep profile)
        if profile == "deep":
            proposals.append(TestProposal(
                test_def=TestDefinition(
                    name=f"agg_consistency_{dataset.lower().replace('.', '_')}",
                    type="reconciliation",
                    dataset=dataset,
                    expression="SUM(amount) matches source totals",
                    tolerance={"abs": 0.01},
                    severity="major",
                    gate="fail"
                ),
                rationale="Aggregated values should match source totals",
                confidence=0.75,
                auto_approvable=False  # Requires source comparison
            ))
        
        return proposals
