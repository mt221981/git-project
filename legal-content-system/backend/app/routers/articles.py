"""Article API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, SessionLocal
from app.services.analysis_service import AnalysisService, AnalysisError
from app.services.article_service import ArticleService, ArticleGenerationError
from app.services.verdict_service import VerdictService
from app.schemas.article import (
    ArticleResponse,
    ArticleListResponse,
    ArticleGenerationResponse
)
from app.schemas.verdict import VerdictResponse
from app.schemas.common import PaginatedResponse
from app.models.article import PublishStatus
from app.models.verdict import Verdict, VerdictStatus

router = APIRouter()


def get_analysis_service(db: Session = Depends(get_db)) -> AnalysisService:
    """Dependency to get AnalysisService instance."""
    return AnalysisService(db)


def get_article_service(db: Session = Depends(get_db)) -> ArticleService:
    """Dependency to get ArticleService instance."""
    return ArticleService(db)


def get_verdict_service(db: Session = Depends(get_db)) -> VerdictService:
    """Dependency to get VerdictService instance."""
    return VerdictService(db)


def run_analysis_background(verdict_id: int):
    """Run analysis in background with its own database session."""
    db = SessionLocal()
    try:
        analysis_service = AnalysisService(db)
        analysis_service.analyze_verdict(verdict_id)
    except Exception as e:
        print(f"[Background] Analysis failed for verdict {verdict_id}: {str(e)}")
        verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
        if verdict:
            verdict.status = VerdictStatus.FAILED
            verdict.review_notes = f"Analysis failed: {str(e)}"
            db.commit()
    finally:
        db.close()


def run_article_generation_background(verdict_id: int):
    """Run article generation in background with its own database session."""
    db = SessionLocal()
    try:
        article_service = ArticleService(db)
        article_service.generate_article_from_verdict(verdict_id)
    except Exception as e:
        print(f"[Background] Article generation failed for verdict {verdict_id}: {str(e)}")
        verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
        if verdict:
            verdict.status = VerdictStatus.FAILED
            verdict.review_notes = f"Article generation failed: {str(e)}"
            db.commit()
    finally:
        db.close()


@router.post("/generate/{verdict_id}", response_model=VerdictResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_article(
    verdict_id: int,
    background_tasks: BackgroundTasks,
    verdict_service: VerdictService = Depends(get_verdict_service),
    article_service: ArticleService = Depends(get_article_service)
):
    """
    Generate an SEO-optimized article from an analyzed verdict.

    This endpoint will:
    1. Validate the verdict exists and is analyzed
    2. Check if article already exists
    3. Start background processing
    4. Return immediately (client should poll for verdict status change to 'article_created')

    The verdict must be in 'analyzed' status before article generation.

    Returns:
        Verdict (client should poll until status is 'article_created')
    """
    verdict = verdict_service.get_verdict(verdict_id)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict with ID {verdict_id} not found"
        )

    if verdict.status not in [VerdictStatus.ANALYZED, VerdictStatus.ARTICLE_CREATED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verdict must be analyzed before article generation. Current status: {verdict.status}"
        )

    # Check if article already exists
    from app.models.article import Article
    existing_article = article_service.db.query(Article).filter(
        Article.verdict_id == verdict_id
    ).first()

    if existing_article:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Article already exists for this verdict (ID: {existing_article.id})"
        )

    # Start background task
    background_tasks.add_task(run_article_generation_background, verdict_id)

    return VerdictResponse.model_validate(verdict)


@router.get("", response_model=PaginatedResponse[ArticleListResponse])
@router.get("/", response_model=PaginatedResponse[ArticleListResponse])
async def list_articles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    status: Optional[PublishStatus] = Query(None, description="Filter by publish status"),
    service: ArticleService = Depends(get_article_service)
):
    """
    List all articles with pagination.

    Optional filtering by publish status.
    """
    articles, total = service.list_articles(skip=skip, limit=limit, status=status)

    return PaginatedResponse(
        items=[ArticleListResponse.model_validate(a) for a in articles],
        total=total,
        skip=skip,
        limit=limit
    )


def _normalize_quality_issues(quality_issues):
    """Convert old string format to new dict format for backward compatibility."""
    if quality_issues is None:
        return None
    result = []
    for item in quality_issues:
        if isinstance(item, str):
            result.append({"type": "warning", "message": item})
        elif isinstance(item, dict):
            result.append(item)
    return result


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    service: ArticleService = Depends(get_article_service)
):
    """
    Get detailed information about a specific article.
    """
    article = service.get_article(article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found"
        )

    # Normalize quality_issues for backward compatibility
    article.quality_issues = _normalize_quality_issues(article.quality_issues)

    return ArticleResponse.model_validate(article)


@router.get("/by-verdict/{verdict_id}", response_model=ArticleResponse)
async def get_article_by_verdict(
    verdict_id: int,
    service: ArticleService = Depends(get_article_service)
):
    """
    Get article for a specific verdict.
    """
    from app.models.article import Article

    article = service.db.query(Article).filter(Article.verdict_id == verdict_id).first()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No article found for verdict ID {verdict_id}"
        )

    # Normalize quality_issues for backward compatibility
    article.quality_issues = _normalize_quality_issues(article.quality_issues)

    return ArticleResponse.model_validate(article)


@router.get("/statistics/overview", response_model=dict)
async def get_article_statistics(
    service: ArticleService = Depends(get_article_service)
):
    """
    Get article statistics.

    Returns counts by status and average quality scores.
    """
    return service.get_article_stats()


# Verdict analysis endpoints (part of article generation workflow)

@router.post("/verdicts/{verdict_id}/analyze", response_model=VerdictResponse)
async def analyze_verdict(
    verdict_id: int,
    background_tasks: BackgroundTasks,
    service: VerdictService = Depends(get_verdict_service)
):
    """
    Analyze a verdict to extract structured information.

    This endpoint will:
    1. Validate the verdict exists and is in correct status
    2. Set status to 'analyzing'
    3. Start background processing
    4. Return immediately (client should poll for updates)

    The verdict must be in 'anonymized' status before analysis.

    Returns:
        Verdict with status 'analyzing'
    """
    verdict = service.get_verdict(verdict_id)

    if not verdict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verdict with ID {verdict_id} not found"
        )

    # Check if verdict has been anonymized
    if verdict.status not in [VerdictStatus.ANONYMIZED, VerdictStatus.ANALYZED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Verdict must be anonymized before analysis. Current status: {verdict.status}"
        )

    if verdict.status == VerdictStatus.ANALYZING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verdict is already being analyzed"
        )

    # Set status to analyzing
    verdict = service.update_verdict_status(verdict_id, VerdictStatus.ANALYZING)

    # Start background task
    background_tasks.add_task(run_analysis_background, verdict_id)

    return VerdictResponse.model_validate(verdict)


@router.post("/verdicts/{verdict_id}/re-analyze", response_model=VerdictResponse)
async def re_analyze_verdict(
    verdict_id: int,
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Re-analyze a verdict.

    Useful if the previous analysis needs updating or was incorrect.
    This will clear the previous analysis and perform it again.

    Returns:
        Updated verdict with new analysis data
    """
    try:
        verdict = analysis_service.re_analyze_verdict(verdict_id)
        return VerdictResponse.model_validate(verdict)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AnalysisError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to re-analyze verdict: {str(e)}"
        )


@router.get("/verdicts/statistics/analysis", response_model=dict)
async def get_analysis_statistics(
    analysis_service: AnalysisService = Depends(get_analysis_service)
):
    """
    Get verdict analysis statistics.

    Returns counts and averages for analyzed verdicts.
    """
    return analysis_service.get_analysis_stats()
