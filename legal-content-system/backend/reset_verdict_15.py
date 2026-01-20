"""Reset verdict 15 to analyzed status for testing."""

import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.database import SessionLocal
from app.models.verdict import Verdict, VerdictStatus

db = SessionLocal()

try:
    verdict = db.query(Verdict).filter(Verdict.id == 15).first()

    if not verdict:
        print("❌ Verdict 15 not found")
        sys.exit(1)

    print(f"Current status: {verdict.status.value}")
    print(f"Current progress: {verdict.processing_progress}%")

    # Reset to analyzed status
    verdict.status = VerdictStatus.ANALYZED
    verdict.processing_progress = 50
    verdict.processing_message = "מוכן ליצירת מאמר"
    verdict.review_notes = None

    db.commit()

    print(f"\n✅ Verdict 15 reset to ANALYZED status")
    print(f"New status: {verdict.status.value}")
    print(f"New progress: {verdict.processing_progress}%")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
