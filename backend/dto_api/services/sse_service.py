"""Server-Sent Events service for live run updates."""

import json
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import structlog

from dto_api.db.models import Run, RunTest, get_db_manager

logger = structlog.get_logger()


class SSEService:
    """Service for streaming live run updates via Server-Sent Events."""
    
    def __init__(self):
        # Store active connections per run_id
        self._connections: Dict[str, List[asyncio.Queue]] = {}
    
    async def stream_run_updates(self, run_id: str) -> AsyncGenerator[str, None]:
        """Stream live updates for a specific run."""
        # Create a queue for this connection
        queue = asyncio.Queue()
        
        # Add to connections for this run
        if run_id not in self._connections:
            self._connections[run_id] = []
        self._connections[run_id].append(queue)
        
        try:
            logger.info("SSE connection established", run_id=run_id)
            
            # Send initial run state
            initial_state = await self._get_run_state(run_id)
            if initial_state:
                yield self._format_sse_message("run_state", initial_state)
            
            # Stream updates from queue
            while True:
                try:
                    # Wait for updates with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message
                    
                    # If run is completed, send final state and close
                    if message and "run_completed" in message:
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield self._format_sse_message("heartbeat", {"timestamp": datetime.utcnow().isoformat()})
                    
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled", run_id=run_id)
            
        finally:
            # Clean up connection
            if run_id in self._connections and queue in self._connections[run_id]:
                self._connections[run_id].remove(queue)
                if not self._connections[run_id]:
                    del self._connections[run_id]
            
            logger.info("SSE connection closed", run_id=run_id)
    
    async def broadcast_run_update(self, run_id: str, event_type: str, data: Dict[str, Any]):
        """Broadcast an update to all connections for a run."""
        if run_id not in self._connections:
            return
        
        message = self._format_sse_message(event_type, data)
        
        # Send to all connections for this run
        for queue in self._connections[run_id]:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("SSE queue full, dropping message", run_id=run_id)
    
    async def broadcast_test_result(self, run_id: str, test_result: Dict[str, Any]):
        """Broadcast a test result update."""
        await self.broadcast_run_update(run_id, "test_result", test_result)
    
    async def broadcast_run_status(self, run_id: str, status: str, **kwargs):
        """Broadcast a run status change."""
        data = {"status": status, "timestamp": datetime.utcnow().isoformat()}
        data.update(kwargs)
        await self.broadcast_run_update(run_id, "run_status", data)
    
    async def broadcast_run_completed(self, run_id: str, final_state: Dict[str, Any]):
        """Broadcast run completion."""
        await self.broadcast_run_update(run_id, "run_completed", final_state)
    
    def _format_sse_message(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Events message."""
        json_data = json.dumps(data, default=str)
        return f"event: {event_type}\ndata: {json_data}\n\n"
    
    async def _get_run_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get current run state from database."""
        try:
            db_manager = get_db_manager()
            with db_manager.get_session() as session:
                run_record = session.query(Run).filter(Run.id == run_id).first()
                if not run_record:
                    return None
                
                # Get test results
                test_results = session.query(RunTest).filter(RunTest.run_id == run_id).all()
                
                return {
                    "run": run_record.to_dict(),
                    "tests": [test.to_dict() for test in test_results],
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to get run state", run_id=run_id, error=str(e))
            return None
    
    def get_active_connections_count(self, run_id: str) -> int:
        """Get number of active connections for a run."""
        return len(self._connections.get(run_id, []))


# Global service instance
sse_service = SSEService()
