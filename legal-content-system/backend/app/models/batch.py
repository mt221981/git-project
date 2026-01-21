"""Batch model for managing multiple verdict uploads."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class BatchStatus(str, enum.Enum):
    """Status of a batch upload."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Batch(Base):
    """
    Batch model for managing multiple verdict uploads.

    A batch represents a group of verdicts uploaded together,
    either via multiple file upload or from a folder.
    """
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)

    # Batch identification
    name = Column(String(200), nullable=True)  # Folder name or user description
    source_folder = Column(String(500), nullable=True)  # Path if uploaded from folder

    # Progress tracking
    total_files = Column(Integer, default=0, nullable=False)
    processed_files = Column(Integer, default=0, nullable=False)
    successful_files = Column(Integer, default=0, nullable=False)
    failed_files = Column(Integer, default=0, nullable=False)
    skipped_files = Column(Integer, default=0, nullable=False)  # Duplicates

    # Status
    status = Column(Enum(BatchStatus), default=BatchStatus.PENDING, nullable=False, index=True)

    # Error tracking
    error_log = Column(JSON, default=list)  # List of {filename, error} dicts

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)  # When processing started
    completed_at = Column(DateTime, nullable=True)  # When processing finished

    # Relationships
    verdicts = relationship("Verdict", back_populates="batch")

    @property
    def progress_percent(self) -> int:
        """Calculate progress percentage."""
        if self.total_files == 0:
            return 0
        return int((self.processed_files / self.total_files) * 100)

    @property
    def is_complete(self) -> bool:
        """Check if batch processing is complete."""
        return self.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]
