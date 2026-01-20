"""Monitor verdict processing in real-time."""

import sys
import time
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.database import SessionLocal
from app.models.verdict import Verdict
from app.models.article import Article

def monitor_verdict(verdict_id: int, check_interval: int = 5):
    """Monitor a verdict's processing status."""
    db = SessionLocal()

    print(f"🔍 Monitoring Verdict {verdict_id}...")
    print(f"Checking every {check_interval} seconds. Press Ctrl+C to stop.\n")

    previous_status = None
    previous_progress = None

    try:
        while True:
            verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()

            if not verdict:
                print(f"❌ Verdict {verdict_id} not found")
                break

            status = verdict.status.value
            progress = verdict.processing_progress
            message = verdict.processing_message or 'N/A'

            # Print update if status or progress changed
            if status != previous_status or progress != previous_progress:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Status: {status} | Progress: {progress}% | {message}")

                previous_status = status
                previous_progress = progress

            # Check if done
            if status in ['article_created', 'failed']:
                print(f"\n{'='*80}")
                print(f"✅ PROCESSING COMPLETE!" if status == 'article_created' else "❌ PROCESSING FAILED!")
                print(f"{'='*80}\n")

                if status == 'article_created':
                    article = db.query(Article).filter(Article.verdict_id == verdict_id).first()
                    if article:
                        print(f"📊 Quality Scores:")
                        print(f"  - Content: {article.content_score}/100")
                        print(f"  - SEO: {article.seo_score}/100")
                        print(f"  - Readability: {article.readability_score}/100")
                        print(f"  - E-E-A-T: {article.eeat_score}/100")

                        all_passed = (
                            article.content_score >= 85 and
                            article.seo_score >= 85 and
                            article.readability_score >= 85 and
                            article.eeat_score >= 85
                        )

                        if all_passed:
                            print("\n✅ ALL QUALITY THRESHOLDS MET (85+)!")
                        else:
                            print("\n⚠️  Some scores below 85:")
                            if article.content_score < 85:
                                print(f"   - Content: {article.content_score}")
                            if article.seo_score < 85:
                                print(f"   - SEO: {article.seo_score}")
                            if article.readability_score < 85:
                                print(f"   - Readability: {article.readability_score}")
                            if article.eeat_score < 85:
                                print(f"   - E-E-A-T: {article.eeat_score}")

                elif status == 'failed':
                    print(f"Reason: {verdict.review_notes or 'No reason provided'}")

                break

            # Wait before next check
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring stopped by user")
    finally:
        db.close()

if __name__ == "__main__":
    verdict_id = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    monitor_verdict(verdict_id)
