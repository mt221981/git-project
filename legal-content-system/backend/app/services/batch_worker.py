"""Background worker for batch processing."""

import asyncio
from datetime import datetime
from typing import Optional
import threading

from app.database import SessionLocal
from app.models.batch import Batch, BatchStatus
from app.models.verdict import Verdict, VerdictStatus
from app.services.batch_service import BatchService
from app.services.analysis_service import AnalysisService
from app.services.article_service import ArticleService


class BatchWorker:
    """
    Background worker for processing verdicts in batches.

    Runs as a singleton, processing verdicts from all active batches.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure only one worker exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize worker."""
        if self._initialized:
            return

        self.is_running = False
        self.max_concurrent = 3
        self.poll_interval = 5  # seconds
        self._task = None
        self._semaphore = None
        self._initialized = True

    async def start(self):
        """Start the worker."""
        if self.is_running:
            print("[BatchWorker] Worker is already running")
            return

        self.is_running = True
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        print(f"[BatchWorker] Starting worker with max {self.max_concurrent} concurrent tasks")

        self._task = asyncio.create_task(self._worker_loop())

    async def stop(self):
        """Stop the worker gracefully."""
        if not self.is_running:
            return

        print("[BatchWorker] Stopping worker...")
        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        print("[BatchWorker] Worker stopped")

    async def _worker_loop(self):
        """Main worker loop."""
        while self.is_running:
            try:
                # Find and process pending verdicts
                await self._process_pending_verdicts()

                # Update batch statuses
                self._update_batch_statuses()

                # Wait before next poll
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[BatchWorker] Error in worker loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _process_pending_verdicts(self):
        """Find and process pending verdicts."""
        db = SessionLocal()
        try:
            # Get processing batches
            batches = db.query(Batch).filter(
                Batch.status == BatchStatus.PROCESSING
            ).all()

            if not batches:
                return

            for batch in batches:
                # Get pending verdicts for this batch
                pending_verdicts = db.query(Verdict).filter(
                    Verdict.batch_id == batch.id,
                    Verdict.status == VerdictStatus.EXTRACTED
                ).order_by(Verdict.created_at.asc()).limit(self.max_concurrent).all()

                for verdict in pending_verdicts:
                    if not self.is_running:
                        return

                    # Process verdict with semaphore
                    async with self._semaphore:
                        await self._process_verdict(verdict.id, batch.id)

        finally:
            db.close()

    async def _process_verdict(self, verdict_id: int, batch_id: int):
        """
        Process a single verdict through the full pipeline.

        Args:
            verdict_id: Verdict ID
            batch_id: Batch ID for progress tracking
        """
        db = SessionLocal()
        try:
            print(f"[BatchWorker] Processing verdict {verdict_id} from batch {batch_id}")

            verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
            if not verdict:
                print(f"[BatchWorker] Verdict {verdict_id} not found")
                return

            # Update status to analyzing
            verdict.status = VerdictStatus.ANALYZING
            verdict.processing_progress = 10
            verdict.processing_message = "מתחיל ניתוח משפטי..."
            db.commit()

            # Run analysis
            try:
                analysis_service = AnalysisService(db)
                analysis_service.analyze_verdict(verdict_id)
            except Exception as e:
                print(f"[BatchWorker] Analysis failed for verdict {verdict_id}: {e}")
                verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
                if verdict:
                    verdict.status = VerdictStatus.FAILED
                    verdict.review_notes = f"Analysis failed: {str(e)}"
                    db.commit()

                # Update batch progress with failure
                batch_service = BatchService(db)
                batch_service.update_batch_progress(batch_id, success=False, error=str(e))
                return

            # Generate article
            try:
                article_service = ArticleService(db)
                article_service.generate_article_from_verdict(verdict_id)
            except Exception as e:
                print(f"[BatchWorker] Article generation failed for verdict {verdict_id}: {e}")
                verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
                if verdict:
                    verdict.status = VerdictStatus.FAILED
                    verdict.review_notes = f"Article generation failed: {str(e)}"
                    db.commit()

                # Update batch progress with failure
                batch_service = BatchService(db)
                batch_service.update_batch_progress(batch_id, success=False, error=str(e))
                return

            print(f"[BatchWorker] Successfully processed verdict {verdict_id}")

            # Update batch progress with success
            batch_service = BatchService(db)
            batch_service.update_batch_progress(batch_id, success=True)

        except Exception as e:
            print(f"[BatchWorker] Error processing verdict {verdict_id}: {e}")
            # Try to update batch progress
            try:
                batch_service = BatchService(db)
                batch_service.update_batch_progress(batch_id, success=False, error=str(e))
            except:
                pass
        finally:
            db.close()

    def _update_batch_statuses(self):
        """Check and update batch statuses."""
        db = SessionLocal()
        try:
            # Find processing batches that are complete
            processing_batches = db.query(Batch).filter(
                Batch.status == BatchStatus.PROCESSING
            ).all()

            for batch in processing_batches:
                # Count remaining verdicts to process
                remaining = db.query(Verdict).filter(
                    Verdict.batch_id == batch.id,
                    Verdict.status.in_([
                        VerdictStatus.EXTRACTED,
                        VerdictStatus.ANALYZING,
                        VerdictStatus.ARTICLE_CREATING
                    ])
                ).count()

                if remaining == 0:
                    # All verdicts processed
                    batch.status = BatchStatus.COMPLETED
                    batch.completed_at = datetime.utcnow()
                    print(f"[BatchWorker] Batch {batch.id} completed")

            db.commit()

        finally:
            db.close()


# Global worker instance
_worker: Optional[BatchWorker] = None


def get_worker() -> BatchWorker:
    """Get or create the batch worker instance."""
    global _worker
    if _worker is None:
        _worker = BatchWorker()
    return _worker


async def start_worker():
    """Start the batch worker."""
    worker = get_worker()
    await worker.start()


async def stop_worker():
    """Stop the batch worker."""
    worker = get_worker()
    await worker.stop()
