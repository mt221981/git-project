"""Script to reset stuck verdicts back to a processable state."""

import sys
from app.database import SessionLocal
from app.models.verdict import Verdict, VerdictStatus

def reset_stuck_verdict(verdict_id: int):
    """Reset a stuck verdict back to extracted status."""
    db = SessionLocal()
    try:
        verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()

        if not verdict:
            print(f"ERROR: Verdict {verdict_id} not found")
            return False

        print(f"Verdict {verdict_id} - Case: {verdict.case_number}")
        print(f"Current status: {verdict.status.value if verdict.status else 'None'}")
        print(f"Progress: {verdict.processing_progress}%")

        # Reset to extracted if stuck in processing
        if verdict.status in [VerdictStatus.ANONYMIZING, VerdictStatus.ANALYZING]:
            verdict.status = VerdictStatus.EXTRACTED
            verdict.processing_progress = 0
            verdict.processing_message = ''
            verdict.review_notes = f'Reset from stuck {verdict.status.value} state'
            db.commit()
            print(f"SUCCESS: Reset to EXTRACTED status")
            return True
        else:
            print(f"INFO: Verdict not in stuck state (status: {verdict.status.value})")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def reset_all_stuck_verdicts():
    """Reset all verdicts stuck in processing states."""
    db = SessionLocal()
    try:
        stuck_verdicts = db.query(Verdict).filter(
            Verdict.status.in_([VerdictStatus.ANONYMIZING, VerdictStatus.ANALYZING])
        ).all()

        if not stuck_verdicts:
            print("No stuck verdicts found")
            return 0

        count = 0
        for verdict in stuck_verdicts:
            print(f"\nResetting verdict {verdict.id} (Case: {verdict.case_number})")
            verdict.status = VerdictStatus.EXTRACTED
            verdict.processing_progress = 0
            verdict.processing_message = ''
            verdict.review_notes = f'Auto-reset from stuck {verdict.status.value} state'
            count += 1

        db.commit()
        print(f"\nSUCCESS: Reset {count} stuck verdict(s)")
        return count

    except Exception as e:
        print(f"ERROR: {str(e)}")
        db.rollback()
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            verdict_id = int(sys.argv[1])
            reset_stuck_verdict(verdict_id)
        except ValueError:
            print("ERROR: Invalid verdict ID")
    else:
        print("Resetting all stuck verdicts...")
        reset_all_stuck_verdicts()
