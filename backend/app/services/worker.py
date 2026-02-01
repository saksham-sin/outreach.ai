"""Background worker for processing scheduled email jobs."""

import asyncio
import logging
from datetime import datetime, timezone

from app.infrastructure.database import async_session_factory
from app.services.job_service import JobService
from app.services.campaign_service import CampaignService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailWorker:
    """Background worker that processes scheduled email jobs."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the background worker."""
        if self._running:
            logger.warning("Worker is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Email worker started")

    async def stop(self):
        """Stop the background worker gracefully."""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Email worker stopped")

    async def _run_loop(self):
        """Main worker loop - runs every poll interval."""
        while self._running:
            try:
                await self._process_pending_jobs()
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}", exc_info=True)
            
            # Wait for next poll interval
            await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)

    async def _process_pending_jobs(self):
        """Process all pending jobs that are due."""
        async with async_session_factory() as session:
            job_service = JobService(session)
            campaign_service = CampaignService(session)
            
            # Get pending jobs
            jobs = await job_service.get_pending_jobs()
            
            if not jobs:
                return
            
            logger.info(f"Processing {len(jobs)} pending jobs")
            
            # Track campaigns that might need completion check
            campaign_ids_to_check = set()
            
            # Process each job
            for job in jobs:
                try:
                    success = await job_service.execute_job(job)
                    campaign_ids_to_check.add(job.campaign_id)
                except Exception as e:
                    logger.error(
                        f"Error executing job {job.id}: {str(e)}",
                        exc_info=True
                    )
            
            # Commit all changes
            await session.commit()
            
            # Check for campaign completion
            for campaign_id in campaign_ids_to_check:
                try:
                    await campaign_service.check_campaign_completion(campaign_id)
                    await session.commit()
                except Exception as e:
                    logger.error(
                        f"Error checking campaign completion for {campaign_id}: {str(e)}"
                    )


# Singleton instance
_worker: EmailWorker | None = None


def get_worker() -> EmailWorker:
    """Get or create worker instance."""
    global _worker
    if _worker is None:
        _worker = EmailWorker()
    return _worker
