"""PII redaction policies and utilities."""

import re
from typing import Dict, List, Any, Optional

import structlog

logger = structlog.get_logger()


class PIIRedactionPolicy:
    """Policy for redacting PII from data samples and AI context."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        
        # PII patterns (basic set - would be configurable in production)
        self.pii_patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
            "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
        }
        
        # PII column name patterns
        self.pii_column_patterns = [
            re.compile(r'.*email.*', re.IGNORECASE),
            re.compile(r'.*phone.*', re.IGNORECASE),
            re.compile(r'.*ssn.*', re.IGNORECASE),
            re.compile(r'.*social.*security.*', re.IGNORECASE),
            re.compile(r'.*credit.*card.*', re.IGNORECASE),
            re.compile(r'.*address.*', re.IGNORECASE),
            re.compile(r'.*name.*', re.IGNORECASE),
            re.compile(r'.*dob.*', re.IGNORECASE),
            re.compile(r'.*birth.*date.*', re.IGNORECASE)
        ]
    
    def redact_sample_data(self, sample_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Redact PII from sample data rows."""
        if not self.enabled:
            return sample_data
        
        try:
            logger.debug("Applying PII redaction to sample data", rows=len(sample_data))
            
            redacted_data = []
            for row in sample_data:
                redacted_row = {}
                for column, value in row.items():
                    redacted_row[column] = self._redact_column_value(column, value)
                redacted_data.append(redacted_row)
            
            return redacted_data
            
        except Exception as e:
            logger.error("PII redaction failed", exc_info=e)
            # Return empty data rather than risk PII exposure
            return []
    
    def redact_ai_context(self, context: str) -> str:
        """Redact PII from AI context strings."""
        if not self.enabled:
            return context
        
        try:
            redacted_context = context
            
            # Apply pattern-based redaction
            for pii_type, pattern in self.pii_patterns.items():
                redacted_context = pattern.sub(f"[REDACTED_{pii_type.upper()}]", redacted_context)
            
            logger.debug("Applied PII redaction to AI context")
            return redacted_context
            
        except Exception as e:
            logger.error("AI context PII redaction failed", exc_info=e)
            # Return generic message rather than risk PII exposure
            return "[CONTEXT_REDACTED_DUE_TO_ERROR]"
    
    def _redact_column_value(self, column_name: str, value: Any) -> Any:
        """Redact value based on column name and content patterns."""
        if value is None:
            return None
        
        # Convert to string for pattern matching
        str_value = str(value)
        
        # Check if column name suggests PII
        if self._is_pii_column(column_name):
            return self._mask_value(str_value)
        
        # Check value content for PII patterns
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(str_value):
                return pattern.sub(f"[REDACTED_{pii_type.upper()}]", str_value)
        
        return value
    
    def _is_pii_column(self, column_name: str) -> bool:
        """Check if column name suggests PII content."""
        return any(pattern.match(column_name) for pattern in self.pii_column_patterns)
    
    def _mask_value(self, value: str) -> str:
        """Mask a value while preserving some structure."""
        if len(value) <= 4:
            return "*" * len(value)
        elif len(value) <= 8:
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
        else:
            return value[:3] + "*" * (len(value) - 6) + value[-3:]
    
    def get_redacted_column_list(self, columns: List[str]) -> List[str]:
        """Get list of columns that would be redacted."""
        if not self.enabled:
            return []
        
        return [col for col in columns if self._is_pii_column(col)]
    
    def validate_query_for_pii(self, sql: str, table_columns: Optional[Dict[str, List[str]]] = None) -> List[str]:
        """Validate query doesn't explicitly select PII columns."""
        if not self.enabled or not table_columns:
            return []
        
        warnings = []
        sql_upper = sql.upper()
        
        # Check for SELECT * which might expose PII
        if re.search(r'\bSELECT\s+\*\b', sql_upper):
            warnings.append("SELECT * detected - may expose PII columns")
        
        # Check for explicit PII column selection
        for table, columns in table_columns.items():
            pii_columns = self.get_redacted_column_list(columns)
            for pii_col in pii_columns:
                if re.search(rf'\b{pii_col.upper()}\b', sql_upper):
                    warnings.append(f"PII column {pii_col} selected from {table}")
        
        return warnings
