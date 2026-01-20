"""Quick script to check verdict and article status."""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.database import SessionLocal
from app.models.verdict import Verdict
from app.models.article import Article

db = SessionLocal()
try:
    # Get latest verdict
    verdict = db.query(Verdict).order_by(Verdict.id.desc()).first()

    if not verdict:
        print("No verdicts found")
        sys.exit(1)

    print(f"Latest Verdict (ID {verdict.id}):")
    print(f"  Status: {verdict.status.value}")
    print(f"  Progress: {verdict.processing_progress}%")
    print(f"  Message: {verdict.processing_message or 'N/A'}")
    print(f"  Case: {verdict.case_number or 'N/A'}")

    if verdict.status.value == 'failed':
        print(f"\n❌ FAILED!")
        print(f"  Reason: {verdict.review_notes or 'No reason provided'}")

    elif verdict.status.value == 'article_created':
        print(f"\n✓ Article created successfully!")
        article = db.query(Article).filter(Article.verdict_id == verdict.id).first()
        if article:
            print(f"  Article ID: {article.id}")
            print(f"  Title: {article.title}")
            print(f"  Word count: {article.word_count}")
            print(f"  Content: {article.content_score}/100")
            print(f"  SEO: {article.seo_score}/100")
            print(f"  Readability: {article.readability_score}/100")
            print(f"  E-E-A-T: {article.eeat_score}/100")

            all_passed = (
                article.content_score >= 85 and
                article.seo_score >= 85 and
                article.readability_score >= 85 and
                article.eeat_score >= 85
            )

            if all_passed:
                print("\n✓ All quality thresholds met (85+)!")
            else:
                print("\n⚠ Some scores below 85:")
                if article.content_score < 85:
                    print(f"  - Content: {article.content_score}")
                if article.seo_score < 85:
                    print(f"  - SEO: {article.seo_score}")
                if article.readability_score < 85:
                    print(f"  - Readability: {article.readability_score}")
                if article.eeat_score < 85:
                    print(f"  - E-E-A-T: {article.eeat_score}")

    elif verdict.status.value in ['analyzing', 'article_creating']:
        print(f"\n⏳ Processing... please wait")
        print(f"   Current stage: {verdict.status.value}")

    print()

finally:
    db.close()
