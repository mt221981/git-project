"""Script to add featured images to all existing articles."""

import os
import sys
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app.models.article import Article
from app.services.image_service import PexelsImageService, ImageServiceError


def get_default_prompt_for_legal_area(legal_area: str, title: str) -> str:
    """Generate a default image prompt based on legal area.

    IMPORTANT: This system handles ONLY tort law (נזיקין) and insurance (ביטוח) cases.
    All prompts should relate to these areas - NOT family law, divorce, criminal, etc.
    """
    prompts = {
        # Core tort/insurance categories
        "נזיקין": "תמונה של פטיש שופט ומאזניים, משרד עורכי דין, תביעת פיצויים",
        "ביטוח": "תמונה של מסמך ביטוח, תביעת ביטוח, פיצוי כספי",
        "פיצויים": "תמונה של פטיש שופט, פיצוי כספי, בית משפט",
        # Accident types
        "תאונת דרכים": "תמונה של תאונת רכב, נזק לרכב, כביש",
        "תעבורה": "תמונה של תאונת רכב, נזק לרכב, תאונת דרכים",
        "תאונת עבודה": "תמונה של בטיחות בעבודה, ציוד מגן, מפעל",
        # Medical
        "רפואי": "תמונה של סטטוסקופ, מסמכים רפואיים, בית חולים",
        "רשלנות רפואית": "תמונה של מסמכים רפואיים, בית חולים, רופא",
        # Property damage
        "נזקי רכוש": "תמונה של נזק לרכוש, ביטוח, בית",
        "רכוש": "תמונה של נזק לבית, פיצוי, ביטוח רכוש",
        # General legal (fallback - still tort/insurance themed)
        "משפט אזרחי": "תמונה של בית משפט, פטיש שופט, מסמכים משפטיים",
    }

    # Try to match legal area
    if legal_area:
        for key, prompt in prompts.items():
            if key in legal_area:
                return prompt

    # Check title for hints
    title_lower = title.lower() if title else ""
    if "נזק" in title_lower or "פיצוי" in title_lower:
        return prompts["נזיקין"]
    if "עבודה" in title_lower or "פיטורים" in title_lower:
        return prompts["עבודה"]
    if "דירה" in title_lower or "בית" in title_lower or "שכירות" in title_lower:
        return prompts["מקרקעין"]
    if "בניה" in title_lower or "ליקויי" in title_lower:
        return prompts["בניה"]
    if "תאונה" in title_lower:
        return prompts["תעבורה"]

    # Default legal image
    return "תמונה של משרד עורכי דין, ספרי משפט, פטיש שופט"


def add_images_to_articles():
    """Add featured images to all articles that don't have one."""

    # Check API key
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("ERROR: PEXELS_API_KEY not set in environment")
        sys.exit(1)

    print(f"Using Pexels API key: {api_key[:10]}...")

    # Initialize services
    db = SessionLocal()
    image_service = PexelsImageService(api_key)

    try:
        # Get all articles without featured image
        articles = db.query(Article).filter(
            Article.featured_image_url == None
        ).all()

        print(f"\nFound {len(articles)} articles without featured images\n")

        success_count = 0
        fail_count = 0

        for i, article in enumerate(articles, 1):
            print(f"[{i}/{len(articles)}] Processing article {article.id}: {article.title[:50]}...")

            # Get prompt - use existing or generate default
            prompt = article.featured_image_prompt
            if not prompt:
                # Get legal area from verdict
                legal_area = None
                if article.verdict:
                    legal_area = article.verdict.legal_area
                prompt = get_default_prompt_for_legal_area(legal_area, article.title)
                print(f"  Generated prompt: {prompt[:50]}...")
            else:
                print(f"  Using existing prompt: {prompt[:50]}...")

            try:
                # Fetch image from Pexels
                image_url, credit, metadata = image_service.get_featured_image(
                    prompt=prompt,
                    legal_area=article.category_primary,
                    preferred_size="large"
                )

                if image_url:
                    article.featured_image_url = image_url
                    article.featured_image_credit = credit
                    if not article.featured_image_prompt:
                        article.featured_image_prompt = prompt

                    db.commit()
                    print(f"  SUCCESS: {image_url[:60]}...")
                    success_count += 1
                else:
                    print(f"  SKIP: No suitable image found")
                    fail_count += 1

            except Exception as e:
                print(f"  ERROR: {str(e)}")
                fail_count += 1

            # Rate limiting - Pexels allows 200 requests/hour
            time.sleep(0.5)

        print(f"\n{'='*50}")
        print(f"Completed!")
        print(f"  Success: {success_count}")
        print(f"  Failed/Skipped: {fail_count}")
        print(f"{'='*50}")

    finally:
        db.close()


if __name__ == "__main__":
    add_images_to_articles()
