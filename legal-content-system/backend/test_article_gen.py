"""Test article generation with detailed error reporting."""

import sys
import io
import traceback

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.database import SessionLocal
from app.services.article_service import ArticleService

verdict_id = 15
db = SessionLocal()

try:
    print(f"Testing article generation for verdict {verdict_id}...")
    service = ArticleService(db)

    # Try to generate article
    article = service.generate_article_from_verdict(verdict_id)

    print(f"\n✅ Success!")
    print(f"Article ID: {article.id}")
    print(f"Scores: Content={article.content_score}, SEO={article.seo_score}, "
          f"Readability={article.readability_score}, E-E-A-T={article.eeat_score}")

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print(f"\nFull traceback:")
    traceback.print_exc()

finally:
    db.close()
