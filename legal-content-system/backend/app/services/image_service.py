"""Image service for fetching featured images from Pexels API."""

import os
import re
import time
import requests
from typing import Optional, Dict, Any, Tuple
from urllib.parse import quote
from loguru import logger


class ImageServiceError(Exception):
    """Exception raised when image fetching fails."""
    pass


# Simple in-memory cache with TTL
class ImageCache:
    """Simple cache for image search results with TTL."""

    def __init__(self, ttl_seconds: int = 86400):  # 24 hours default
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                logger.debug(f"[ImageCache] Cache hit for: {key[:30]}")
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set cache value with current timestamp."""
        self._cache[key] = (value, time.time())
        logger.debug(f"[ImageCache] Cached: {key[:30]}")

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()


# Global cache instance
_image_cache = ImageCache(ttl_seconds=86400)  # 24 hours


class PexelsImageService:
    """
    Service for fetching relevant stock images from Pexels API.

    Pexels provides free high-quality stock photos.
    API documentation: https://www.pexels.com/api/documentation/

    Features:
    - HTTP Session reuse for better performance
    - In-memory caching with 24-hour TTL
    """

    BASE_URL = "https://api.pexels.com/v1"

    # Legal-themed search terms - ONLY for tort law (נזיקין) and insurance (ביטוח)
    # DO NOT add family law, divorce, criminal, or other unrelated legal areas
    LEGAL_SEARCH_TERMS = {
        "default": ["lawyer office", "legal document", "law books", "justice scale", "court gavel"],
        "tort": ["court gavel", "legal settlement", "compensation claim", "injury claim", "lawsuit"],
        "insurance": ["insurance claim", "insurance policy", "legal document signing", "compensation"],
        "car_accident": ["car accident damage", "vehicle collision", "traffic accident", "auto insurance"],
        "medical_negligence": ["hospital corridor", "medical records", "stethoscope", "healthcare"],
        "property_damage": ["property damage", "home damage", "flood damage", "fire damage"],
        "personal_injury": ["injury compensation", "disability claim", "rehabilitation"],
        "workplace_injury": ["workplace safety", "industrial accident", "work injury", "safety equipment"],
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Pexels image service.

        Args:
            api_key: Pexels API key (optional, will try env var PEXELS_API_KEY)
        """
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        if not self.api_key:
            raise ImageServiceError(
                "Pexels API key not provided. "
                "Set PEXELS_API_KEY environment variable or pass api_key parameter."
            )

        # Create session for connection reuse
        self._session = requests.Session()
        self._session.headers.update({"Authorization": self.api_key})

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "Authorization": self.api_key
        }

    def _extract_keywords_from_prompt(self, prompt: str) -> str:
        """
        Extract search keywords from image prompt.

        Args:
            prompt: Featured image prompt (usually in Hebrew)

        Returns:
            Search query string
        """
        # Hebrew legal terms to English mappings - ONLY for tort law and insurance
        # Focused on: נזיקין (torts), ביטוח (insurance), תאונות (accidents), פיצויים (compensation)
        hebrew_to_english = {
            # Core tort/insurance terms
            "נזיקין": "legal compensation claim",
            "ביטוח": "insurance policy document",
            "פיצויים": "compensation settlement",
            "תביעה": "lawsuit court",
            "נזק": "damage claim",
            # Accident types
            "תאונה": "accident injury",
            "תאונת דרכים": "car accident damage",
            "תאונת עבודה": "workplace injury",
            "רכב": "car accident",
            # Medical/injury
            "רשלנות רפואית": "medical stethoscope hospital",
            "רשלנות": "legal negligence claim",
            "רפואה": "medical records hospital",
            "נכות": "disability rehabilitation",
            "פציעה": "personal injury",
            # Property
            "רכוש": "property damage",
            "נזקי רכוש": "property damage claim",
            # Legal general
            "משפט": "court gavel law",
            "עורך דין": "lawyer office",
            "בית משפט": "courtroom judge",
            "שופט": "judge gavel",
            "פסק דין": "legal verdict document",
        }

        # Try to extract keywords
        keywords = []
        prompt_lower = prompt.lower()

        for hebrew, english in hebrew_to_english.items():
            if hebrew in prompt:
                keywords.append(english)

        # If we found keywords, use them
        if keywords:
            return " ".join(keywords[:3])  # Limit to 3 keywords

        # Default to generic legal image
        return "lawyer office"

    def _determine_category(self, legal_area: Optional[str], prompt: str) -> str:
        """
        Determine image category based on legal area.

        Args:
            legal_area: Legal area of the article
            prompt: Image prompt

        Returns:
            Category key
        """
        if not legal_area:
            return "default"

        legal_area_lower = legal_area.lower()

        # Category mappings - ONLY for tort law and insurance
        category_mappings = {
            # Tort law (נזיקין)
            "נזיקין": "tort",
            "נזק": "tort",
            "פיצויים": "tort",
            # Insurance (ביטוח)
            "ביטוח": "insurance",
            "פוליסה": "insurance",
            "תגמולי ביטוח": "insurance",
            # Accidents
            "תאונת דרכים": "car_accident",
            "תאונה": "car_accident",
            "תעבורה": "car_accident",
            # Medical negligence
            "רשלנות רפואית": "medical_negligence",
            "רפואי": "medical_negligence",
            # Property damage
            "נזקי רכוש": "property_damage",
            "רכוש": "property_damage",
            # Personal injury
            "נזקי גוף": "personal_injury",
            "פציעה": "personal_injury",
            "נכות": "personal_injury",
            # Workplace injury
            "תאונת עבודה": "workplace_injury",
            "בטיחות בעבודה": "workplace_injury",
        }

        for keyword, category in category_mappings.items():
            if keyword in legal_area_lower:
                return category

        return "default"

    def search_images(
        self,
        query: str,
        per_page: int = 5,
        orientation: str = "landscape"
    ) -> Dict[str, Any]:
        """
        Search for images on Pexels.

        Args:
            query: Search query
            per_page: Number of results (1-80)
            orientation: Image orientation (landscape, portrait, square)

        Returns:
            Pexels API response
        """
        # Check cache first
        cache_key = f"{query}:{per_page}:{orientation}"
        cached = _image_cache.get(cache_key)
        if cached:
            return cached

        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation
        }

        try:
            response = self._session.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()

            # Cache the result
            _image_cache.set(cache_key, result)
            return result
        except requests.RequestException as e:
            raise ImageServiceError(f"Pexels API request failed: {str(e)}")

    def get_featured_image(
        self,
        prompt: str,
        legal_area: Optional[str] = None,
        preferred_size: str = "large"
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Get a featured image based on article prompt and legal area.

        Args:
            prompt: Featured image prompt from article
            legal_area: Legal area for category-specific search
            preferred_size: Size preference (small, medium, large, original)

        Returns:
            Tuple of (image_url, photographer_credit, full_metadata)
        """
        # Try prompt-based search first
        query = self._extract_keywords_from_prompt(prompt)

        try:
            result = self.search_images(query, per_page=5, orientation="landscape")

            # If no results, try category-based search
            if not result.get("photos"):
                category = self._determine_category(legal_area, prompt)
                fallback_terms = self.LEGAL_SEARCH_TERMS.get(category, self.LEGAL_SEARCH_TERMS["default"])

                for term in fallback_terms:
                    result = self.search_images(term, per_page=3, orientation="landscape")
                    if result.get("photos"):
                        break

            # Still no results - use generic legal image
            if not result.get("photos"):
                result = self.search_images("law office", per_page=3, orientation="landscape")

            if not result.get("photos"):
                return None, None, None

            # Get first photo
            photo = result["photos"][0]

            # Get image URL based on preferred size
            size_map = {
                "small": "small",
                "medium": "medium",
                "large": "large",
                "large2x": "large2x",
                "original": "original"
            }

            src = photo.get("src", {})
            image_url = src.get(size_map.get(preferred_size, "large")) or src.get("large") or src.get("original")

            # Build photographer credit
            photographer = photo.get("photographer", "Unknown")
            photographer_url = photo.get("photographer_url", "")
            credit = f"Photo by {photographer} on Pexels"

            metadata = {
                "pexels_id": photo.get("id"),
                "photographer": photographer,
                "photographer_url": photographer_url,
                "pexels_url": photo.get("url"),
                "alt": photo.get("alt", ""),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "avg_color": photo.get("avg_color"),
                "src": src
            }

            return image_url, credit, metadata

        except ImageServiceError:
            raise
        except Exception as e:
            raise ImageServiceError(f"Failed to get featured image: {str(e)}")

    def download_image(self, image_url: str) -> Tuple[bytes, str]:
        """
        Download image from URL.

        Args:
            image_url: URL of the image

        Returns:
            Tuple of (image_bytes, content_type)
        """
        try:
            response = self._session.get(image_url, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "image/jpeg")

            return response.content, content_type

        except requests.RequestException as e:
            raise ImageServiceError(f"Failed to download image: {str(e)}")


# Singleton instance
_image_service: Optional[PexelsImageService] = None


def get_image_service() -> PexelsImageService:
    """Get or create image service instance."""
    global _image_service

    if _image_service is None:
        api_key = os.getenv("PEXELS_API_KEY")
        if api_key:
            _image_service = PexelsImageService(api_key)
        else:
            raise ImageServiceError(
                "PEXELS_API_KEY environment variable not set. "
                "Get a free API key at https://www.pexels.com/api/"
            )

    return _image_service
