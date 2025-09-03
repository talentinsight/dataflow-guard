"""Artifact storage service using MinIO/S3."""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import structlog

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from dto_api.db.models import Artifact, get_db_manager

logger = structlog.get_logger()


class ArtifactService:
    """Service for managing run artifacts in MinIO/S3."""
    
    def __init__(self):
        self.endpoint_url = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET", "dataflow-guard")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        self.s3_client = None
        self._bucket_exists = False
        
        if BOTO3_AVAILABLE:
            try:
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name='us-east-1'  # MinIO doesn't care about region
                )
                self._ensure_bucket_exists()
            except Exception as e:
                logger.warning("Failed to initialize MinIO client", error=str(e))
                self.s3_client = None
        else:
            logger.warning("boto3 not available, artifact storage disabled")
    
    def _ensure_bucket_exists(self):
        """Ensure the MinIO bucket exists."""
        if not self.s3_client or self._bucket_exists:
            return
            
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self._bucket_exists = True
            logger.info("MinIO bucket verified", bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    self._bucket_exists = True
                    logger.info("MinIO bucket created", bucket=self.bucket_name)
                except Exception as create_error:
                    logger.error("Failed to create MinIO bucket", error=str(create_error))
            else:
                logger.error("MinIO bucket check failed", error=str(e))
    
    async def store_run_report(self, run_id: str, report_data: Dict[str, Any]) -> Optional[str]:
        """Store run report as JSON artifact."""
        if not self.s3_client:
            logger.warning("MinIO client not available, skipping artifact storage")
            return None
            
        try:
            # Generate artifact path
            timestamp = datetime.utcnow().strftime("%Y/%m/%d")
            artifact_path = f"runs/{timestamp}/{run_id}/report.json"
            
            # Convert report to JSON
            report_json = json.dumps(report_data, indent=2, default=str)
            
            # Upload to MinIO
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=artifact_path,
                Body=report_json.encode('utf-8'),
                ContentType='application/json'
            )
            
            # Generate pre-signed URL (valid for 7 days)
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': artifact_path},
                ExpiresIn=7 * 24 * 3600  # 7 days
            )
            
            # Store artifact record in database
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                artifact = Artifact(
                    run_id=run_id,
                    kind="report",
                    path=artifact_path,
                    url=presigned_url,
                    size_bytes=len(report_json.encode('utf-8')),
                    content_type="application/json",
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                session.add(artifact)
                session.commit()
                
                logger.info(
                    "Run report stored",
                    run_id=run_id,
                    path=artifact_path,
                    size_bytes=artifact.size_bytes
                )
                
                return presigned_url
                
        except Exception as e:
            logger.error("Failed to store run report", run_id=run_id, error=str(e))
            return None
    
    async def store_logs(self, run_id: str, logs: List[str]) -> Optional[str]:
        """Store execution logs as text artifact."""
        if not self.s3_client:
            return None
            
        try:
            timestamp = datetime.utcnow().strftime("%Y/%m/%d")
            artifact_path = f"runs/{timestamp}/{run_id}/logs.txt"
            
            logs_text = "\n".join(logs)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=artifact_path,
                Body=logs_text.encode('utf-8'),
                ContentType='text/plain'
            )
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': artifact_path},
                ExpiresIn=7 * 24 * 3600
            )
            
            # Store artifact record
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                artifact = Artifact(
                    run_id=run_id,
                    kind="logs",
                    path=artifact_path,
                    url=presigned_url,
                    size_bytes=len(logs_text.encode('utf-8')),
                    content_type="text/plain",
                    expires_at=datetime.utcnow() + timedelta(days=7)
                )
                session.add(artifact)
                session.commit()
                
                return presigned_url
                
        except Exception as e:
            logger.error("Failed to store logs", run_id=run_id, error=str(e))
            return None
    
    async def get_run_artifacts(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all artifacts for a run."""
        try:
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                artifacts = session.query(Artifact).filter(
                    Artifact.run_id == run_id
                ).all()
                
                return [artifact.to_dict() for artifact in artifacts]
                
        except Exception as e:
            logger.error("Failed to get run artifacts", run_id=run_id, error=str(e))
            return []
    
    def health_check(self) -> bool:
        """Check if MinIO is accessible."""
        if not self.s3_client:
            return False
            
        try:
            # Try to list buckets as a health check
            self.s3_client.list_buckets()
            return True
        except Exception as e:
            logger.error("MinIO health check failed", error=str(e))
            return False


# Global service instance
artifact_service = ArtifactService()
