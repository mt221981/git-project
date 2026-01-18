"""Verdict service for business logic."""

from typing import Optional, List
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.verdict import Verdict, VerdictStatus, PrivacyRiskLevel
from app.models.article import Article
from app.schemas.verdict import VerdictCreate, VerdictUpdate
from app.utils import extract_metadata_patterns
from app.services.file_storage import FileStorageService
from app.services.file_processor import FileProcessor, FileProcessingError


class VerdictService:
    """Service for managing verdicts."""

    def __init__(
        self,
        db: Session,
        file_storage: Optional[FileStorageService] = None,
        file_processor: Optional[FileProcessor] = None
    ):
        """
        Initialize verdict service.

        Args:
            db: Database session
            file_storage: Optional file storage service (creates default if not provided)
            file_processor: Optional file processor service (creates default if not provided)
        """
        self.db = db
        self.file_storage = file_storage or FileStorageService()
        self.file_processor = file_processor or FileProcessor()

    def create_verdict(self, verdict_data: VerdictCreate) -> Verdict:
        """
        Create a new verdict in database.

        Args:
            verdict_data: Verdict creation data

        Returns:
            Created verdict instance
        """
        verdict = Verdict(**verdict_data.model_dump())
        self.db.add(verdict)
        self.db.commit()
        self.db.refresh(verdict)
        return verdict

    def get_verdict(self, verdict_id: int) -> Optional[Verdict]:
        """
        Get verdict by ID.

        Args:
            verdict_id: Verdict ID

        Returns:
            Verdict instance or None if not found
        """
        return self.db.query(Verdict).filter(Verdict.id == verdict_id).first()

    def get_verdict_by_hash(self, file_hash: str) -> Optional[Verdict]:
        """
        Get verdict by file hash.

        Args:
            file_hash: SHA-256 hash of the file

        Returns:
            Verdict instance or None if not found
        """
        return self.db.query(Verdict).filter(Verdict.file_hash == file_hash).first()

    def list_verdicts(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[VerdictStatus] = None
    ) -> tuple[List[Verdict], int]:
        """
        List verdicts with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            Tuple of (list of verdicts, total count)
        """
        query = self.db.query(Verdict)

        if status:
            query = query.filter(Verdict.status == status)

        total = query.count()
        verdicts = query.order_by(Verdict.created_at.desc()).offset(skip).limit(limit).all()

        return verdicts, total

    def update_verdict(self, verdict_id: int, update_data: VerdictUpdate) -> Optional[Verdict]:
        """
        Update verdict.

        Args:
            verdict_id: Verdict ID
            update_data: Update data

        Returns:
            Updated verdict or None if not found
        """
        verdict = self.get_verdict(verdict_id)
        if not verdict:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(verdict, field, value)

        self.db.commit()
        self.db.refresh(verdict)
        return verdict

    def update_verdict_status(self, verdict_id: int, status: VerdictStatus) -> Optional[Verdict]:
        """
        Update verdict status.

        Args:
            verdict_id: Verdict ID
            status: New status

        Returns:
            Updated verdict or None if not found
        """
        verdict = self.get_verdict(verdict_id)
        if not verdict:
            return None

        verdict.status = status
        self.db.commit()
        self.db.refresh(verdict)
        return verdict

    def delete_verdict(self, verdict_id: int) -> bool:
        """
        Delete verdict and associated file.

        Args:
            verdict_id: Verdict ID

        Returns:
            True if deleted, False if not found
        """
        verdict = self.get_verdict(verdict_id)
        if not verdict:
            return False

        # Delete file from storage
        self.file_storage.delete_file(verdict.file_hash)

        # Delete from database
        self.db.delete(verdict)
        self.db.commit()
        return True

    def process_file_upload(
        self,
        file_content: bytes,
        filename: str,
        overwrite: bool = False
    ) -> Verdict:
        """
        Process uploaded verdict file.

        This method:
        1. Calculates file hash
        2. Checks for duplicates (deletes if overwrite=True)
        3. Extracts text from file
        4. Cleans the text
        5. Extracts basic metadata
        6. Stores file
        7. Creates verdict record

        Args:
            file_content: Uploaded file content
            filename: Original filename
            overwrite: If True, delete existing verdict with same hash

        Returns:
            Created verdict instance

        Raises:
            FileProcessingError: If file processing fails
            ValueError: If file is a duplicate and overwrite=False
        """
        # Calculate file hash using new FileProcessor
        file_hash = self.file_processor.calculate_hash(file_content)

        # Check for duplicate
        existing = self.get_verdict_by_hash(file_hash)
        if existing:
            if overwrite:
                # Delete existing verdict and its file
                self.delete_verdict(existing.id)
            else:
                raise ValueError(
                    f"File already uploaded. Verdict ID: {existing.id}. "
                    f"Use the existing verdict instead of uploading duplicate."
                )

        # Extract file extension
        file_extension = Path(filename).suffix

        # Extract text from file using new FileProcessor
        try:
            raw_text = self.file_processor.extract_text(file_content, file_extension)
        except FileProcessingError as e:
            # Create verdict with failed status
            verdict = Verdict(
                file_hash=file_hash,
                original_text=f"[Text extraction failed: {str(e)}]",
                status=VerdictStatus.FAILED
            )
            self.db.add(verdict)
            self.db.commit()
            self.db.refresh(verdict)
            raise

        # Clean text using new FileProcessor
        cleaned_text = self.file_processor.clean_text(raw_text)

        # Get text statistics
        stats = self.file_processor.get_text_stats(cleaned_text)

        # Extract basic metadata from text (using existing util)
        metadata = extract_metadata_patterns(cleaned_text)

        # Store file
        self.file_storage.save_file(file_content, file_hash, filename)

        # Create verdict record
        verdict_data = VerdictCreate(
            file_hash=file_hash,
            original_text=raw_text,
            case_number=metadata.get('case_number'),
            case_number_display=metadata.get('case_number'),
            court_name=metadata.get('court_name'),
            judge_name=metadata.get('judge_name'),
        )

        verdict = self.create_verdict(verdict_data)

        # Update with cleaned text and mark as extracted
        verdict.cleaned_text = cleaned_text
        verdict.status = VerdictStatus.EXTRACTED

        self.db.commit()
        self.db.refresh(verdict)

        return verdict

    def get_statistics(self) -> dict:
        """
        Get verdict statistics.

        Returns:
            Dictionary with statistics
        """
        total = self.db.query(func.count(Verdict.id)).scalar()

        status_counts = {}
        for status in VerdictStatus:
            count = self.db.query(func.count(Verdict.id)).filter(
                Verdict.status == status
            ).scalar()
            status_counts[status.value] = count

        pending_review = self.db.query(func.count(Verdict.id)).filter(
            Verdict.requires_manual_review == True
        ).scalar()

        return {
            "total": total,
            "by_status": status_counts,
            "pending_review": pending_review,
            "storage": self.file_storage.get_storage_stats()
        }

    def reset_verdict(self, verdict_id: int, target_status: VerdictStatus = VerdictStatus.EXTRACTED) -> Optional[Verdict]:
        """
        Reset verdict to a specific stage, clearing downstream data.

        Args:
            verdict_id: Verdict ID
            target_status: Status to reset to (default: EXTRACTED)

        Returns:
            Reset verdict or None if not found
        """
        verdict = self.get_verdict(verdict_id)
        if not verdict:
            return None

        # Clear anonymization data if resetting to EXTRACTED
        if target_status == VerdictStatus.EXTRACTED:
            verdict.anonymized_text = None
            verdict.anonymization_report = None
            verdict.privacy_risk_level = PrivacyRiskLevel.LOW
            verdict.requires_manual_review = False

        # Clear analysis data if resetting to EXTRACTED or ANONYMIZED
        if target_status in [VerdictStatus.EXTRACTED, VerdictStatus.ANONYMIZED]:
            verdict.key_facts = None
            verdict.legal_questions = None
            verdict.legal_principles = None
            verdict.compensation_amount = None
            verdict.compensation_breakdown = None
            verdict.relevant_laws = None
            verdict.precedents_cited = None
            verdict.practical_insights = None

        # Delete associated articles
        articles = self.db.query(Article).filter(Article.verdict_id == verdict_id).all()
        for article in articles:
            self.db.delete(article)

        verdict.status = target_status
        verdict.review_notes = None
        self.db.commit()
        self.db.refresh(verdict)
        return verdict
