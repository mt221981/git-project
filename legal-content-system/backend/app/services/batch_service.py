"""Batch service for managing batch uploads and processing."""

import os
from typing import Optional, List, Tuple
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.batch import Batch, BatchStatus
from app.models.verdict import Verdict, VerdictStatus
from app.services.verdict_service import VerdictService
from app.services.file_processor import FileProcessor, FileProcessingError
from app.config import settings


class BatchService:
    """Service for managing batch uploads and processing."""

    # Maximum files per batch
    MAX_FILES_PER_BATCH = 50

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.doc', '.docx'}

    def __init__(self, db: Session):
        """
        Initialize batch service.

        Args:
            db: Database session
        """
        self.db = db
        self.verdict_service = VerdictService(db)
        self.file_processor = FileProcessor()

    def create_batch(self, name: Optional[str] = None) -> Batch:
        """
        Create a new batch.

        Args:
            name: Optional batch name

        Returns:
            Created batch instance
        """
        batch = Batch(
            name=name or f"Batch {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            status=BatchStatus.PENDING
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def get_batch(self, batch_id: int) -> Optional[Batch]:
        """Get batch by ID."""
        return self.db.query(Batch).filter(Batch.id == batch_id).first()

    def list_batches(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[BatchStatus] = None
    ) -> Tuple[List[Batch], int]:
        """
        List batches with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            Tuple of (list of batches, total count)
        """
        query = self.db.query(Batch)

        if status:
            query = query.filter(Batch.status == status)

        total = query.count()
        batches = query.order_by(Batch.created_at.desc()).offset(skip).limit(limit).all()

        return batches, total

    def add_files_to_batch(
        self,
        batch_id: int,
        files: List[Tuple[bytes, str]]  # List of (content, filename) tuples
    ) -> dict:
        """
        Add files to an existing batch.

        Args:
            batch_id: Batch ID
            files: List of (file_content, filename) tuples

        Returns:
            Dictionary with results for each file
        """
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")

        if batch.status != BatchStatus.PENDING:
            raise ValueError(f"Cannot add files to batch with status {batch.status}")

        results = {
            "accepted": [],
            "duplicate": [],
            "invalid": [],
            "error": []
        }

        # Check file limit
        current_count = batch.total_files
        remaining_slots = self.MAX_FILES_PER_BATCH - current_count

        if len(files) > remaining_slots:
            raise ValueError(
                f"Cannot add {len(files)} files. "
                f"Batch has {current_count} files, maximum is {self.MAX_FILES_PER_BATCH}. "
                f"Only {remaining_slots} slots remaining."
            )

        for file_content, filename in files:
            result = self._process_single_file(batch, file_content, filename)
            results[result["status"]].append(result)

        # Update batch totals
        batch.total_files = current_count + len(results["accepted"])
        batch.skipped_files = batch.skipped_files + len(results["duplicate"])
        self.db.commit()

        return results

    def _process_single_file(
        self,
        batch: Batch,
        file_content: bytes,
        filename: str
    ) -> dict:
        """
        Process a single file for batch upload.

        Args:
            batch: Batch instance
            file_content: File content
            filename: Original filename

        Returns:
            Result dictionary with status and details
        """
        result = {
            "filename": filename,
            "size": len(file_content),
            "verdict_id": None,
            "status": "error",
            "error": None
        }

        # Validate file extension
        file_extension = Path(filename).suffix.lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            result["status"] = "invalid"
            result["error"] = f"Unsupported file type: {file_extension}"
            return result

        # Validate file size
        file_size_mb = len(file_content) / (1024 * 1024)
        if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
            result["status"] = "invalid"
            result["error"] = f"File too large: {file_size_mb:.1f}MB (max {settings.MAX_UPLOAD_SIZE_MB}MB)"
            return result

        # Check for duplicate
        file_hash = self.file_processor.calculate_hash(file_content)
        existing = self.verdict_service.get_verdict_by_hash(file_hash)
        if existing:
            result["status"] = "duplicate"
            result["verdict_id"] = existing.id
            result["error"] = f"Duplicate file, exists as verdict {existing.id}"
            return result

        # Process the file
        try:
            verdict = self.verdict_service.process_file_upload(file_content, filename)
            verdict.batch_id = batch.id
            self.db.commit()

            result["status"] = "accepted"
            result["verdict_id"] = verdict.id
        except FileProcessingError as e:
            result["status"] = "error"
            result["error"] = f"Processing error: {str(e)}"
            self._add_error_to_batch(batch, filename, str(e))
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"Unexpected error: {str(e)}"
            self._add_error_to_batch(batch, filename, str(e))

        return result

    def create_batch_from_folder(self, folder_path: str, name: Optional[str] = None) -> dict:
        """
        Create a batch from files in a folder.

        Args:
            folder_path: Path to folder containing verdict files
            name: Optional batch name (defaults to folder name)

        Returns:
            Dictionary with batch info and file results
        """
        folder = Path(folder_path)

        if not folder.exists():
            raise ValueError(f"Folder not found: {folder_path}")

        if not folder.is_dir():
            raise ValueError(f"Not a directory: {folder_path}")

        # Find all valid files
        valid_files = []
        for ext in self.ALLOWED_EXTENSIONS:
            valid_files.extend(folder.glob(f"*{ext}"))
            valid_files.extend(folder.glob(f"*{ext.upper()}"))

        if not valid_files:
            raise ValueError(f"No valid files found in folder. Supported: {', '.join(self.ALLOWED_EXTENSIONS)}")

        if len(valid_files) > self.MAX_FILES_PER_BATCH:
            raise ValueError(
                f"Too many files ({len(valid_files)}). Maximum is {self.MAX_FILES_PER_BATCH} per batch."
            )

        # Create batch
        batch_name = name or folder.name
        batch = self.create_batch(batch_name)
        batch.source_folder = str(folder_path)
        self.db.commit()

        # Process files
        files = []
        for file_path in valid_files:
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                files.append((content, file_path.name))
            except Exception as e:
                self._add_error_to_batch(batch, file_path.name, f"Cannot read file: {str(e)}")

        results = self.add_files_to_batch(batch.id, files)

        return {
            "batch_id": batch.id,
            "batch_name": batch.name,
            "source_folder": str(folder_path),
            "results": results
        }

    def start_batch_processing(self, batch_id: int) -> Batch:
        """
        Start processing verdicts in a batch.

        Args:
            batch_id: Batch ID

        Returns:
            Updated batch
        """
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")

        if batch.status != BatchStatus.PENDING:
            raise ValueError(f"Cannot start batch with status {batch.status}")

        if batch.total_files == 0:
            raise ValueError("Cannot start empty batch")

        batch.status = BatchStatus.PROCESSING
        batch.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(batch)

        return batch

    def cancel_batch(self, batch_id: int) -> dict:
        """
        Cancel a batch, stopping processing of pending verdicts.

        Args:
            batch_id: Batch ID

        Returns:
            Cancellation result
        """
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")

        if batch.status not in [BatchStatus.PENDING, BatchStatus.PROCESSING]:
            raise ValueError(f"Cannot cancel batch with status {batch.status}")

        # Count pending verdicts
        pending_count = self.db.query(func.count(Verdict.id)).filter(
            Verdict.batch_id == batch_id,
            Verdict.status.in_([VerdictStatus.NEW, VerdictStatus.EXTRACTED])
        ).scalar()

        batch.status = BatchStatus.CANCELLED
        batch.completed_at = datetime.utcnow()
        self.db.commit()

        return {
            "batch_id": batch_id,
            "status": batch.status,
            "cancelled_verdicts": pending_count,
            "message": f"Batch cancelled. {pending_count} pending verdicts will not be processed."
        }

    def get_next_pending_verdict(self, batch_id: Optional[int] = None) -> Optional[Verdict]:
        """
        Get the next verdict to process.

        Args:
            batch_id: Optional batch ID to filter by

        Returns:
            Next pending verdict or None
        """
        query = self.db.query(Verdict).filter(
            Verdict.status == VerdictStatus.EXTRACTED
        )

        if batch_id:
            query = query.filter(Verdict.batch_id == batch_id)

        return query.order_by(Verdict.created_at.asc()).first()

    def update_batch_progress(self, batch_id: int, success: bool = True, error: Optional[str] = None):
        """
        Update batch progress after processing a verdict.

        Args:
            batch_id: Batch ID
            success: Whether processing was successful
            error: Error message if failed
        """
        batch = self.get_batch(batch_id)
        if not batch:
            return

        batch.processed_files += 1
        if success:
            batch.successful_files += 1
        else:
            batch.failed_files += 1
            if error:
                self._add_error_to_batch(batch, "verdict", error)

        # Check if batch is complete
        if batch.processed_files >= batch.total_files:
            batch.status = BatchStatus.COMPLETED
            batch.completed_at = datetime.utcnow()

        self.db.commit()

    def _add_error_to_batch(self, batch: Batch, filename: str, error: str):
        """Add error to batch error log."""
        if batch.error_log is None:
            batch.error_log = []

        error_entry = {
            "filename": filename,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Create new list to trigger SQLAlchemy change detection
        batch.error_log = batch.error_log + [error_entry]

    def get_batch_statistics(self) -> dict:
        """
        Get overall batch statistics.

        Returns:
            Dictionary with statistics
        """
        total = self.db.query(func.count(Batch.id)).scalar()

        status_counts = {}
        for status in BatchStatus:
            count = self.db.query(func.count(Batch.id)).filter(
                Batch.status == status
            ).scalar()
            status_counts[status.value] = count

        # Get processing statistics
        total_files = self.db.query(func.sum(Batch.total_files)).scalar() or 0
        processed_files = self.db.query(func.sum(Batch.processed_files)).scalar() or 0
        successful_files = self.db.query(func.sum(Batch.successful_files)).scalar() or 0
        failed_files = self.db.query(func.sum(Batch.failed_files)).scalar() or 0

        return {
            "total_batches": total,
            "by_status": status_counts,
            "total_files": total_files,
            "processed_files": processed_files,
            "successful_files": successful_files,
            "failed_files": failed_files
        }
