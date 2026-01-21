"""Batch API endpoints for bulk verdict upload and processing."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.services.batch_service import BatchService
from app.models.batch import BatchStatus
from app.models.verdict import VerdictStatus
from app.schemas.batch import (
    BatchCreate,
    BatchFromFolderRequest,
    BatchUploadResponse,
    BatchResponse,
    BatchDetailResponse,
    BatchListResponse,
    BatchFileInfo,
    BatchVerdictInfo,
    BatchProcessRequest,
    BatchCancelResponse
)
from app.schemas.common import PaginatedResponse
from app.config import settings

router = APIRouter()


def get_batch_service(db: Session = Depends(get_db)) -> BatchService:
    """Dependency to get BatchService instance."""
    return BatchService(db)


@router.post("/upload", response_model=BatchUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_batch_files(
    files: List[UploadFile] = File(..., description="Verdict files to upload (max 50)"),
    name: Optional[str] = Query(None, description="Batch name"),
    service: BatchService = Depends(get_batch_service)
):
    """
    Upload multiple verdict files as a batch.

    Supported formats: PDF, TXT, DOC, DOCX
    Maximum files per batch: 50
    Maximum file size: 50MB per file

    The system will:
    1. Validate all files
    2. Create a batch record
    3. Process each file (extract text, check duplicates)
    4. Return batch status with details for each file

    Note: This only uploads and validates files.
    Use POST /batch/{batch_id}/process to start the analysis pipeline.
    """
    if len(files) > BatchService.MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum is {BatchService.MAX_FILES_PER_BATCH} per batch."
        )

    if len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )

    # Create batch
    batch = service.create_batch(name)

    # Read file contents
    file_data = []
    for upload_file in files:
        content = await upload_file.read()
        file_data.append((content, upload_file.filename))

    # Add files to batch
    try:
        results = service.add_files_to_batch(batch.id, file_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Build response
    all_files = []
    for category in ["accepted", "duplicate", "invalid", "error"]:
        for file_result in results.get(category, []):
            all_files.append(BatchFileInfo(
                filename=file_result["filename"],
                size=file_result["size"],
                verdict_id=file_result.get("verdict_id"),
                status=file_result.get("status", category),
                error=file_result.get("error")
            ))

    # Refresh batch to get updated totals
    batch = service.get_batch(batch.id)

    return BatchUploadResponse(
        batch_id=batch.id,
        batch_name=batch.name,
        total_files=len(files),
        accepted_files=len(results.get("accepted", [])),
        duplicate_files=len(results.get("duplicate", [])),
        invalid_files=len(results.get("invalid", [])),
        files=all_files,
        message=f"Batch created with {batch.total_files} files ready for processing"
    )


@router.post("/upload-from-folder", response_model=BatchUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_from_folder(
    request: BatchFromFolderRequest,
    service: BatchService = Depends(get_batch_service)
):
    """
    Create a batch from files in a server-side folder.

    This endpoint scans a folder on the server and adds all valid files to a new batch.
    Useful for processing large numbers of files already on the server.

    Note: The folder path must be accessible from the server.
    """
    try:
        result = service.create_batch_from_folder(request.folder_path, request.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    batch = service.get_batch(result["batch_id"])
    results = result["results"]

    # Build file info list
    all_files = []
    for category in ["accepted", "duplicate", "invalid", "error"]:
        for file_result in results.get(category, []):
            all_files.append(BatchFileInfo(
                filename=file_result["filename"],
                size=file_result["size"],
                verdict_id=file_result.get("verdict_id"),
                status=file_result.get("status"),
                error=file_result.get("error")
            ))

    return BatchUploadResponse(
        batch_id=batch.id,
        batch_name=batch.name,
        total_files=batch.total_files + batch.skipped_files,
        accepted_files=len(results.get("accepted", [])),
        duplicate_files=len(results.get("duplicate", [])),
        invalid_files=len(results.get("invalid", [])),
        files=all_files,
        message=f"Batch created from folder with {batch.total_files} files ready for processing"
    )


@router.get("/", response_model=PaginatedResponse[BatchListResponse])
async def list_batches(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    batch_status: Optional[BatchStatus] = Query(None, alias="status", description="Filter by status"),
    service: BatchService = Depends(get_batch_service)
):
    """
    List all batches with pagination.

    Optional filtering by status.
    """
    batches, total = service.list_batches(skip=skip, limit=limit, status=batch_status)

    return PaginatedResponse(
        items=[BatchListResponse(
            id=b.id,
            name=b.name,
            total_files=b.total_files,
            processed_files=b.processed_files,
            successful_files=b.successful_files,
            failed_files=b.failed_files,
            status=b.status,
            progress_percent=b.progress_percent,
            created_at=b.created_at,
            completed_at=b.completed_at
        ) for b in batches],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{batch_id}", response_model=BatchDetailResponse)
async def get_batch(
    batch_id: int,
    service: BatchService = Depends(get_batch_service)
):
    """
    Get detailed information about a specific batch.

    Includes list of verdicts in the batch with their statuses.
    """
    batch = service.get_batch(batch_id)

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID {batch_id} not found"
        )

    # Get verdict info
    verdicts = []
    for verdict in batch.verdicts:
        verdicts.append(BatchVerdictInfo(
            id=verdict.id,
            case_number=verdict.case_number,
            status=verdict.status.value,
            processing_progress=verdict.processing_progress or 0,
            processing_message=verdict.processing_message,
            error=verdict.review_notes if verdict.status == VerdictStatus.FAILED else None
        ))

    return BatchDetailResponse(
        id=batch.id,
        name=batch.name,
        source_folder=batch.source_folder,
        total_files=batch.total_files,
        processed_files=batch.processed_files,
        successful_files=batch.successful_files,
        failed_files=batch.failed_files,
        skipped_files=batch.skipped_files,
        status=batch.status,
        progress_percent=batch.progress_percent,
        error_log=batch.error_log or [],
        created_at=batch.created_at,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        verdicts=verdicts
    )


@router.post("/{batch_id}/process", response_model=BatchResponse)
async def start_batch_processing(
    batch_id: int,
    request: Optional[BatchProcessRequest] = None,
    service: BatchService = Depends(get_batch_service)
):
    """
    Start processing all verdicts in a batch.

    This will:
    1. Set batch status to 'processing'
    2. Background worker will pick up verdicts and run the full pipeline
    3. Each verdict goes through: analysis -> article generation

    Progress can be monitored via GET /batch/{batch_id}
    """
    try:
        batch = service.start_batch_processing(batch_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return BatchResponse(
        id=batch.id,
        name=batch.name,
        source_folder=batch.source_folder,
        total_files=batch.total_files,
        processed_files=batch.processed_files,
        successful_files=batch.successful_files,
        failed_files=batch.failed_files,
        skipped_files=batch.skipped_files,
        status=batch.status,
        progress_percent=batch.progress_percent,
        error_log=batch.error_log or [],
        created_at=batch.created_at,
        started_at=batch.started_at,
        completed_at=batch.completed_at
    )


@router.post("/{batch_id}/cancel", response_model=BatchCancelResponse)
async def cancel_batch(
    batch_id: int,
    service: BatchService = Depends(get_batch_service)
):
    """
    Cancel a batch, stopping processing of remaining verdicts.

    Verdicts that are already being processed will complete,
    but new verdicts will not be started.
    """
    try:
        result = service.cancel_batch(batch_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return BatchCancelResponse(
        batch_id=result["batch_id"],
        status=result["status"],
        cancelled_verdicts=result["cancelled_verdicts"],
        message=result["message"]
    )


@router.get("/statistics/overview", response_model=dict)
async def get_batch_statistics(
    service: BatchService = Depends(get_batch_service)
):
    """
    Get overall batch statistics.

    Returns counts by status and file processing statistics.
    """
    return service.get_batch_statistics()
