"""Verdict API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, SessionLocal
from app.services.verdict_service import VerdictService
from app.services.anonymization_service import AnonymizationService, AnonymizationError
from app.services.analysis_service import AnalysisService
from app.services.article_service import ArticleService
from app.services.file_processor import FileProcessingError
from app.schemas.verdict import (
    VerdictResponse,
    VerdictListResponse,
    VerdictUpdate,
    VerdictStatusUpdate,
    FileUploadResponse
)
from app.schemas.common import PaginatedResponse
from app.models.verdict import VerdictStatus
from app.config import settings

router = APIRouter()


def get_verdict_service(db: Session = Depends(get_db)) -> VerdictService:
    """Dependency to get VerdictService instance."""
    return VerdictService(db)


def get_anonymization_service(db: Session = Depends(get_db)) -> AnonymizationService:
    """Dependency to get AnonymizationService instance."""
    return AnonymizationService(db)


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_verdict_file(
    file: UploadFile = File(...),
    overwrite: bool = Query(False, description="Overwrite existing file if duplicate"),
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Upload a verdict file for processing.

    Supported formats: PDF, TXT, DOC, DOCX

    The system will:
    1. Extract text from the file
    2. Clean and normalize the text
    3. Extract basic metadata (case number, court, judge)
    4. Store the file and create a verdict record

    Args:
        file: The verdict file to upload
        overwrite: If True, replace existing verdict with same file hash

    Returns:
        FileUploadResponse with verdict ID and status
    """
    # Validate file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)

    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    # Validate file extension
    file_extension = file.filename.split('.')[-1].lower()
    allowed_extensions = [ext.lstrip('.') for ext in settings.ALLOWED_FILE_EXTENSIONS]

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Process file
    try:
        verdict = service.process_file_upload(file_content, file.filename, overwrite=overwrite)
    except ValueError as e:
        # Duplicate file
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )

    return FileUploadResponse(
        message="File uploaded and processed successfully",
        verdict_id=verdict.id,
        file_hash=verdict.file_hash,
        status=verdict.status
    )


@router.get("/", response_model=PaginatedResponse[VerdictListResponse])
async def list_verdicts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    status: Optional[VerdictStatus] = Query(None, description="Filter by status"),
    service: VerdictService = Depends(get_verdict_service)
):
    """
    List all verdicts with pagination.

    Optional filtering by status.
    """
    verdicts, total = service.list_verdicts(skip=skip, limit=limit, status=status)

    return PaginatedResponse(
        items=[VerdictListResponse.model_validate(v) for v in verdicts],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{verdict_id}", response_model=VerdictResponse)
async def get_verdict(
    verdict_id: int,
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Get detailed information about a specific verdict.
    """
    verdict = service.get_verdict(verdict_id)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict with ID {verdict_id} not found"
        )

    return VerdictResponse.model_validate(verdict)


@router.patch("/{verdict_id}", response_model=VerdictResponse)
async def update_verdict(
    verdict_id: int,
    update_data: VerdictUpdate,
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Update verdict information.

    Allows updating metadata and analysis fields.
    """
    verdict = service.update_verdict(verdict_id, update_data)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict with ID {verdict_id} not found"
        )

    return VerdictResponse.model_validate(verdict)


@router.patch("/{verdict_id}/status", response_model=VerdictResponse)
async def update_verdict_status(
    verdict_id: int,
    status_update: VerdictStatusUpdate,
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Update verdict processing status.
    """
    verdict = service.update_verdict_status(verdict_id, status_update.status)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict with ID {verdict_id} not found"
        )

    return VerdictResponse.model_validate(verdict)


@router.delete("/{verdict_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_verdict(
    verdict_id: int,
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Delete a verdict and its associated file.

    WARNING: This action cannot be undone.
    """
    success = service.delete_verdict(verdict_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict with ID {verdict_id} not found"
        )

    return None


# Anonymization endpoints

def run_anonymization_background(verdict_id: int):
    """Run anonymization in background with its own database session."""
    db = SessionLocal()
    try:
        anon_service = AnonymizationService(db)
        anon_service.anonymize_verdict(verdict_id)
    except Exception as e:
        # Log error and update verdict status to failed
        print(f"[Background] Anonymization failed for verdict {verdict_id}: {str(e)}")
        from app.models.verdict import Verdict, VerdictStatus
        verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
        if verdict:
            verdict.status = VerdictStatus.FAILED
            verdict.review_notes = f"Anonymization failed: {str(e)}"
            db.commit()
    finally:
        db.close()


def run_full_pipeline_background(verdict_id: int):
    """Run full processing pipeline: anonymize → analyze → generate article."""
    db = SessionLocal()
    try:
        from app.models.verdict import Verdict

        # Step 1: Anonymize
        print(f"[Background] Starting anonymization for verdict {verdict_id}")
        anon_service = AnonymizationService(db)
        anon_service.anonymize_verdict(verdict_id)

        # Step 2: Analyze
        print(f"[Background] Starting analysis for verdict {verdict_id}")
        analysis_service = AnalysisService(db)
        analysis_service.analyze_verdict(verdict_id)

        # Step 3: Generate Article
        print(f"[Background] Starting article generation for verdict {verdict_id}")
        article_service = ArticleService(db)
        article_service.generate_article_from_verdict(verdict_id)

        print(f"[Background] Full pipeline completed for verdict {verdict_id}")

    except Exception as e:
        print(f"[Background] Pipeline failed for verdict {verdict_id}: {str(e)}")
        from app.models.verdict import Verdict
        verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
        if verdict:
            verdict.status = VerdictStatus.FAILED
            verdict.review_notes = f"Pipeline failed: {str(e)}"
            db.commit()
    finally:
        db.close()


@router.post("/{verdict_id}/anonymize", response_model=VerdictResponse)
async def anonymize_verdict(
    verdict_id: int,
    background_tasks: BackgroundTasks,
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Anonymize a verdict using Claude API.

    This endpoint will:
    1. Validate the verdict exists and is in correct status
    2. Set status to 'anonymizing'
    3. Start background processing
    4. Return immediately (client should poll for updates)

    The verdict must be in 'extracted' status before anonymization.

    Returns:
        Verdict with status 'anonymizing'
    """
    verdict = service.get_verdict(verdict_id)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict with ID {verdict_id} not found"
        )

    # Check if verdict has been extracted
    if verdict.status == VerdictStatus.NEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verdict must be extracted before anonymization"
        )

    if verdict.status in [VerdictStatus.ANONYMIZING, VerdictStatus.ANONYMIZED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verdict is already anonymized or being anonymized"
        )

    # Set status to anonymizing
    verdict = service.update_verdict_status(verdict_id, VerdictStatus.ANONYMIZING)

    # Start background task
    background_tasks.add_task(run_anonymization_background, verdict_id)

    return VerdictResponse.model_validate(verdict)


@router.post("/{verdict_id}/re-anonymize", response_model=VerdictResponse)
async def re_anonymize_verdict(
    verdict_id: int,
    anon_service: AnonymizationService = Depends(get_anonymization_service)
):
    """
    Re-anonymize a verdict.

    Useful if the previous anonymization was incorrect or needs updating.
    This will clear the previous anonymization and perform it again.

    Returns:
        Updated verdict with new anonymized text and report
    """
    try:
        verdict = anon_service.re_anonymize_verdict(verdict_id)
        return VerdictResponse.model_validate(verdict)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AnonymizationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-anonymize verdict: {str(e)}"
        )


@router.get("/statistics/anonymization", response_model=dict)
async def get_anonymization_statistics(
    anon_service: AnonymizationService = Depends(get_anonymization_service)
):
    """
    Get anonymization statistics.

    Returns:
        Statistics about anonymized verdicts, risk levels, and pending reviews
    """
    return anon_service.get_anonymization_stats()


@router.get("/statistics/overview", response_model=dict)
async def get_statistics(
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Get system statistics.

    Returns counts by status, pending reviews, and storage info.
    """
    return service.get_statistics()


@router.post("/{verdict_id}/reprocess", response_model=VerdictResponse)
async def reprocess_verdict(
    verdict_id: int,
    background_tasks: BackgroundTasks,
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Reset verdict and trigger full reprocessing pipeline.

    This endpoint will:
    1. Reset verdict to 'extracted' status, clearing all downstream data
    2. Delete any associated articles
    3. Run the full pipeline: anonymize → analyze → generate article

    Useful for reprocessing verdicts that failed or need to be updated.

    Returns:
        Verdict with status 'extracted' (processing begins in background)
    """
    verdict = service.get_verdict(verdict_id)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict with ID {verdict_id} not found"
        )

    # Check if verdict has original text (was extracted successfully)
    if not verdict.original_text or verdict.status == VerdictStatus.NEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verdict must have been extracted before reprocessing"
        )

    # Reset verdict to EXTRACTED status
    verdict = service.reset_verdict(verdict_id, VerdictStatus.EXTRACTED)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset verdict"
        )

    # Start full pipeline in background
    background_tasks.add_task(run_full_pipeline_background, verdict_id)

    return VerdictResponse.model_validate(verdict)
