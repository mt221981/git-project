"""File storage service for uploaded verdict files."""

import os
from pathlib import Path
from typing import Optional
import shutil


class FileStorageService:
    """
    Service for managing uploaded verdict file storage.

    Stores original uploaded files on disk for backup/reference purposes.
    Files are organized by their hash to avoid duplicates.
    """

    def __init__(self, storage_dir: str = "./storage/verdicts"):
        """
        Initialize file storage service.

        Args:
            storage_dir: Base directory for file storage
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, file_hash: str, extension: str = "") -> Path:
        """
        Get storage path for a file based on its hash.

        Uses first 2 chars of hash as subdirectory for better organization.

        Args:
            file_hash: SHA-256 hash of the file
            extension: File extension (including dot)

        Returns:
            Path object for the file storage location
        """
        # Use first 2 chars of hash for subdirectory (256 possible dirs)
        subdir = file_hash[:2]
        dir_path = self.storage_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)

        filename = f"{file_hash}{extension}"
        return dir_path / filename

    def save_file(self, file_content: bytes, file_hash: str, original_filename: str) -> str:
        """
        Save uploaded file to storage.

        Args:
            file_content: File content as bytes
            file_hash: SHA-256 hash of the file
            original_filename: Original filename (used to preserve extension)

        Returns:
            Relative path to stored file

        Example:
            >>> service = FileStorageService()
            >>> path = service.save_file(b"content", "abc123...", "verdict.pdf")
            >>> print(path)
            'ab/abc123....pdf'
        """
        extension = Path(original_filename).suffix.lower()
        file_path = self._get_file_path(file_hash, extension)

        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Return relative path from storage_dir
        return str(file_path.relative_to(self.storage_dir))

    def get_file(self, file_hash: str, extension: str = "") -> Optional[bytes]:
        """
        Retrieve file content from storage.

        Args:
            file_hash: SHA-256 hash of the file
            extension: File extension (if known)

        Returns:
            File content as bytes, or None if not found
        """
        file_path = self._get_file_path(file_hash, extension)

        if not file_path.exists():
            # Try to find file with any extension if extension not provided
            if not extension:
                parent_dir = file_path.parent
                if parent_dir.exists():
                    for possible_file in parent_dir.glob(f"{file_hash}.*"):
                        with open(possible_file, 'rb') as f:
                            return f.read()
            return None

        with open(file_path, 'rb') as f:
            return f.read()

    def file_exists(self, file_hash: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_hash: SHA-256 hash of the file

        Returns:
            True if file exists, False otherwise
        """
        # Check if any file with this hash exists
        subdir = file_hash[:2]
        dir_path = self.storage_dir / subdir

        if not dir_path.exists():
            return False

        return any(dir_path.glob(f"{file_hash}.*"))

    def delete_file(self, file_hash: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_hash: SHA-256 hash of the file

        Returns:
            True if file was deleted, False if not found
        """
        subdir = file_hash[:2]
        dir_path = self.storage_dir / subdir

        if not dir_path.exists():
            return False

        deleted = False
        for file_path in dir_path.glob(f"{file_hash}.*"):
            file_path.unlink()
            deleted = True

        return deleted

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage stats (total_files, total_size_mb)
        """
        total_files = 0
        total_size = 0

        for file_path in self.storage_dir.rglob("*"):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size

        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_dir": str(self.storage_dir.absolute())
        }
