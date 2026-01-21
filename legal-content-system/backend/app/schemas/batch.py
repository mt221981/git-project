"""Pydantic schemas for batch operations."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.batch import BatchStatus


class BatchCreate(BaseModel):
    """Schema for creating a batch."""
    name: Optional[str] = Field(None, description="Batch name or description")


class BatchFromFolderRequest(BaseModel):
    """Schema for creating a batch from a folder."""
    folder_path: str = Field(..., description="Path to folder containing verdict files")
    name: Optional[str] = Field(None, description="Batch name (defaults to folder name)")


class BatchFileInfo(BaseModel):
    """Information about a file in a batch."""
    filename: str
    size: int
    verdict_id: Optional[int] = None
    status: str  # "accepted", "duplicate", "invalid", "error"
    error: Optional[str] = None


class BatchUploadResponse(BaseModel):
    """Response after uploading files to a batch."""
    batch_id: int
    batch_name: Optional[str] = None
    total_files: int
    accepted_files: int
    duplicate_files: int
    invalid_files: int
    files: List[BatchFileInfo]
    message: str


class BatchVerdictInfo(BaseModel):
    """Brief verdict info for batch listing."""
    id: int
    case_number: Optional[str] = None
    status: str
    processing_progress: int = 0
    processing_message: Optional[str] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BatchResponse(BaseModel):
    """Schema for batch response."""
    id: int
    name: Optional[str] = None
    source_folder: Optional[str] = None
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    skipped_files: int
    status: BatchStatus
    progress_percent: int
    error_log: List[Dict[str, Any]] = []
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BatchDetailResponse(BatchResponse):
    """Detailed batch response including verdicts."""
    verdicts: List[BatchVerdictInfo] = []


class BatchListResponse(BaseModel):
    """Schema for batch list response."""
    id: int
    name: Optional[str] = None
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    status: BatchStatus
    progress_percent: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BatchProcessRequest(BaseModel):
    """Request to start processing a batch."""
    max_concurrent: int = Field(default=3, ge=1, le=5, description="Maximum concurrent processing")


class BatchCancelResponse(BaseModel):
    """Response after cancelling a batch."""
    batch_id: int
    status: BatchStatus
    cancelled_verdicts: int
    message: str
