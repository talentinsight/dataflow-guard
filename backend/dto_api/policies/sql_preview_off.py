"""SQL preview policy enforcement."""

from typing import Optional, Dict, Any
from enum import Enum

import structlog

logger = structlog.get_logger()


class SQLPreviewMode(Enum):
    """SQL preview modes."""
    DISABLED = "disabled"
    ADMIN_ONLY = "admin_only"
    READ_ONLY = "read_only"


class SQLPreviewPolicy:
    """Policy for controlling SQL preview visibility."""
    
    def __init__(
        self, 
        mode: SQLPreviewMode = SQLPreviewMode.DISABLED,
        admin_power_mode: bool = False
    ):
        self.mode = mode
        self.admin_power_mode = admin_power_mode
        
        # SQL sanitization patterns for admin mode
        self.sensitive_patterns = [
            "password", "secret", "key", "token", "credential"
        ]
    
    def can_view_sql_preview(self, user_role: str) -> bool:
        """Check if user can view SQL preview."""
        if self.mode == SQLPreviewMode.DISABLED:
            return False
        elif self.mode == SQLPreviewMode.ADMIN_ONLY:
            return user_role == "admin" and self.admin_power_mode
        elif self.mode == SQLPreviewMode.READ_ONLY:
            return user_role in ["admin", "maintainer"] and self.admin_power_mode
        
        return False
    
    def sanitize_sql_for_preview(self, sql: str, user_role: str) -> Optional[str]:
        """Sanitize SQL for preview based on user role and policy."""
        if not self.can_view_sql_preview(user_role):
            return None
        
        try:
            logger.debug("Sanitizing SQL for preview", user_role=user_role)
            
            # Basic sanitization - remove sensitive patterns
            sanitized_sql = sql
            for pattern in self.sensitive_patterns:
                # Replace sensitive values with placeholders
                import re
                sanitized_sql = re.sub(
                    rf"'{pattern}[^']*'", 
                    f"'[REDACTED_{pattern.upper()}]'", 
                    sanitized_sql, 
                    flags=re.IGNORECASE
                )
            
            # Add warning header
            warning_header = f"""
-- WARNING: SQL Preview Mode (Admin Power Mode)
-- This is a READ-ONLY preview for debugging purposes
-- User: {user_role}
-- Generated SQL below:

"""
            
            return warning_header + sanitized_sql
            
        except Exception as e:
            logger.error("SQL sanitization failed", exc_info=e)
            return None
    
    def validate_admin_sql_request(self, sql: str, user_role: str) -> Dict[str, Any]:
        """Validate admin SQL request in power mode."""
        if not self.admin_power_mode or user_role != "admin":
            return {
                "allowed": False,
                "reason": "Admin power mode disabled or insufficient privileges"
            }
        
        try:
            # Static analysis for safety
            sql_upper = sql.upper().strip()
            
            # Check for forbidden operations
            forbidden_keywords = [
                'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'TRUNCATE',
                'CREATE', 'ALTER', 'DROP', 'RENAME',
                'GRANT', 'REVOKE', 'SET', 'USE',
                'CALL', 'EXECUTE', 'COPY', 'BULK'
            ]
            
            for keyword in forbidden_keywords:
                if keyword in sql_upper:
                    return {
                        "allowed": False,
                        "reason": f"Forbidden keyword detected: {keyword}",
                        "requires_approval": True
                    }
            
            # Check for allowed operations only
            allowed_prefixes = ['SELECT', 'WITH', 'EXPLAIN', 'DESCRIBE', 'SHOW']
            
            if not any(sql_upper.startswith(prefix) for prefix in allowed_prefixes):
                return {
                    "allowed": False,
                    "reason": "Only SELECT, EXPLAIN, DESCRIBE, and SHOW statements allowed",
                    "requires_approval": True
                }
            
            # Additional safety checks
            warnings = []
            
            # Check for potential data exposure
            if 'SELECT *' in sql_upper:
                warnings.append("SELECT * detected - may expose sensitive columns")
            
            # Check for large result sets
            if 'LIMIT' not in sql_upper and 'TOP' not in sql_upper:
                warnings.append("No LIMIT clause - query may return large result set")
            
            return {
                "allowed": True,
                "warnings": warnings,
                "sandboxed": True,
                "max_rows": 1000  # Enforce result limit
            }
            
        except Exception as e:
            logger.error("Admin SQL validation failed", exc_info=e)
            return {
                "allowed": False,
                "reason": "SQL validation error"
            }
    
    def log_sql_preview_access(self, user_role: str, sql: str, approved: bool) -> None:
        """Log SQL preview access for audit."""
        logger.info(
            "SQL preview access",
            user_role=user_role,
            sql_hash=hash(sql),
            sql_preview=sql[:100],
            approved=approved,
            admin_power_mode=self.admin_power_mode
        )
    
    def get_policy_status(self) -> Dict[str, Any]:
        """Get current policy status."""
        return {
            "sql_preview_mode": self.mode.value,
            "admin_power_mode": self.admin_power_mode,
            "description": self._get_mode_description()
        }
    
    def _get_mode_description(self) -> str:
        """Get human-readable description of current mode."""
        if self.mode == SQLPreviewMode.DISABLED:
            return "SQL preview is completely disabled for all users"
        elif self.mode == SQLPreviewMode.ADMIN_ONLY:
            if self.admin_power_mode:
                return "SQL preview available to admins only (Power Mode enabled)"
            else:
                return "SQL preview disabled (Admin Power Mode required)"
        elif self.mode == SQLPreviewMode.READ_ONLY:
            if self.admin_power_mode:
                return "Read-only SQL preview available to admins and maintainers"
            else:
                return "SQL preview disabled (Admin Power Mode required)"
        
        return "Unknown mode"
