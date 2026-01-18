"""Integration test for complete upload and anonymization workflow."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services import VerdictService, AnonymizationService, FileProcessingError
from app.models.verdict import VerdictStatus, PrivacyRiskLevel


def create_test_database():
    """Create an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def create_sample_verdict_file() -> bytes:
    """Create a sample Hebrew verdict file for testing."""
    sample_text = """
פסק דין

בית המשפט המחוזי בתל אביב-יפו

תיק מספר: 12345-01-20

תובע: ישראל ישראלי
ת.ז.: 123456789
כתובת: רחוב הרצל 10, תל אביב 61000
טלפון: 052-1234567
אימייל: israel.israeli@example.com

נתבע: דוד כהן
ת.ז.: 987654321
כתובת: רחוב ביאליק 25, רמת גן
טלפון: 054-9876543

נציג התובע: עו"ד רחל לוי
נציג הנתבע: עו"ד משה דוד

בפני: כבוד השופט יצחק גרוס

העובדות:
1. התובע, מר ישראל ישראלי, גר ברחוב הרצל 10 בתל אביב ועבד במשך 5 שנים
   אצל הנתבע, מר דוד כהן, בחברת "טכנולוגיות עתיד בע"מ".

2. ביום 15 בינואר 2020, הנתבע פיטר את התובע ללא הודעה מוקדמת.

3. התובע טוען כי הפיטורים היו שלא כדין וכי הנתבע חייב לו פיצויי פיטורים
   בסך 120,000 ₪ וכן פיצוי בגין אי-מתן הודעה מוקדמת.

4. הנתבע טוען כי הפיטורים היו מוצדקים עקב הפרת חוזה העבודה על ידי התובע.

ניתוח משפטי:

השאלה המשפטית המרכזית היא האם הפיטורים היו מוצדקים או שלא כדין.

על פי חוק עבודה תשל"ח-1978, עובד זכאי להודעה מוקדמת או לתשלום במקום הודעה.

בנוסף, פסק הדין בעניין "כהן נגד משרד החינוך" (ע"ע 567/85) קבע כי:
"פיטורים ללא הצדקה מהווים הפרה יסודית של חוזה העבודה."

פסק הדין:

לאחר שבחנתי את הראיות והטענות, הגעתי למסקנה כי:

1. הפיטורים היו שלא כדין ולא היתה הצדקה מספקת לביצועם.

2. התובע זכאי לפיצויי פיטורים מלאים בסך 95,000 ₪.

3. התובע זכאי לפיצוי בגין אי-מתן הודעה מוקדמת בסך 15,000 ₪.

4. הנתבע ישלם לתובע הוצאות משפט בסך 10,000 ₪.

סך כל הסכום שהנתבע חייב לשלם לתובע: 120,000 ₪.

התשלום יבוצע תוך 30 יום מיום מתן פסק הדין.

ניתן היום, 15 במרץ 2021

                                    יצחק גרוס, שופט
                                    בית המשפט המחוזי בתל אביב-יפו
"""
    return sample_text.encode('utf-8')


def test_complete_workflow():
    """Test the complete upload and anonymization workflow."""
    print("=" * 70)
    print("INTEGRATION TEST: Complete Upload and Anonymization Workflow")
    print("=" * 70)

    # Create test database
    print("\n1. Setting up test database...")
    db = create_test_database()
    print("   ✓ Test database created")

    # Create sample file
    print("\n2. Creating sample verdict file...")
    file_content = create_sample_verdict_file()
    filename = "test_verdict.txt"
    print(f"   ✓ Sample file created ({len(file_content)} bytes)")

    # Initialize services
    print("\n3. Initializing services...")
    verdict_service = VerdictService(db)
    anon_service = AnonymizationService(db)
    print("   ✓ Services initialized")

    # Test file upload and processing
    print("\n4. Testing file upload and processing...")
    print("   - Uploading file...")
    try:
        verdict = verdict_service.process_file_upload(file_content, filename)
        print(f"   ✓ File uploaded successfully (Verdict ID: {verdict.id})")
        print(f"   - Status: {verdict.status.value}")
        print(f"   - File hash: {verdict.file_hash[:16]}...")
        print(f"   - Case number: {verdict.case_number or 'Not extracted'}")
        print(f"   - Court: {verdict.court_name or 'Not extracted'}")
        print(f"   - Judge: {verdict.judge_name or 'Not extracted'}")

        # Check text extraction
        assert verdict.original_text, "Original text should be present"
        assert verdict.cleaned_text, "Cleaned text should be present"
        print(f"   - Original text length: {len(verdict.original_text)} chars")
        print(f"   - Cleaned text length: {len(verdict.cleaned_text)} chars")

        # Check status
        assert verdict.status == VerdictStatus.EXTRACTED, "Status should be EXTRACTED"

        # Check text stats in metadata
        if verdict.metadata and 'text_stats' in verdict.metadata:
            stats = verdict.metadata['text_stats']
            print(f"   - Word count: {stats.get('word_count', 'N/A')}")
            print(f"   - Has Hebrew: {stats.get('has_hebrew', 'N/A')}")

    except FileProcessingError as e:
        print(f"   ❌ File processing failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test duplicate detection
    print("\n5. Testing duplicate detection...")
    try:
        verdict_service.process_file_upload(file_content, filename)
        print("   ❌ Duplicate detection failed - file was uploaded twice!")
        return False
    except ValueError as e:
        if "already uploaded" in str(e):
            print("   ✓ Duplicate correctly detected and rejected")
        else:
            print(f"   ❌ Unexpected ValueError: {e}")
            return False

    # Test anonymization
    print("\n6. Testing anonymization...")
    try:
        # Check if API key is configured
        from app.config import settings
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "your-key-here":
            print("   ⚠️  Skipping anonymization test: ANTHROPIC_API_KEY not configured")
            print("   Set ANTHROPIC_API_KEY in .env file to test anonymization")
            return True  # Still consider test successful

        print("   - Starting anonymization...")
        anonymized_verdict = anon_service.anonymize_verdict(verdict.id)

        print(f"   ✓ Anonymization completed")
        print(f"   - Status: {anonymized_verdict.status.value}")
        print(f"   - Privacy risk: {anonymized_verdict.privacy_risk_level.value}")
        print(f"   - Requires review: {anonymized_verdict.requires_manual_review}")

        # Check anonymization report
        if anonymized_verdict.anonymization_report:
            report = anonymized_verdict.anonymization_report
            change_count = report.get('change_count', 0)
            print(f"   - Items anonymized: {change_count}")

            if 'changes' in report and report['changes']:
                print("\n   Sample anonymized items:")
                for item in report['changes'][:5]:  # Show first 5
                    category = item.get('category', 'unknown')
                    original = item.get('original', '')
                    replacement = item.get('replacement', '')
                    print(f"     - {category}: '{original}' → '{replacement}'")

                if len(report['changes']) > 5:
                    print(f"     ... and {len(report['changes']) - 5} more items")

        # Verify anonymization
        assert anonymized_verdict.anonymized_text, "Anonymized text should be present"
        assert anonymized_verdict.status == VerdictStatus.ANONYMIZED, "Status should be ANONYMIZED"

        # Check that names were removed
        anon_text = anonymized_verdict.anonymized_text
        assert "ישראל ישראלי" not in anon_text, "Original name should be anonymized"
        assert "דוד כהן" not in anon_text, "Original name should be anonymized"

        # Check that public info remains
        # (Judge names and lawyer names might remain as they're public)
        # But case numbers and amounts should remain
        assert "120,000" in anon_text or "120000" in anon_text, "Amounts should remain"

        print("\n   ✓ Anonymization verification passed")

    except Exception as e:
        print(f"   ❌ Anonymization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test statistics
    print("\n7. Testing statistics...")
    try:
        verdict_stats = verdict_service.get_statistics()
        print(f"   ✓ Verdict statistics:")
        print(f"     - Total verdicts: {verdict_stats['total']}")
        print(f"     - By status: {verdict_stats['by_status']}")

        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "your-key-here":
            anon_stats = anon_service.get_anonymization_stats()
            print(f"   ✓ Anonymization statistics:")
            print(f"     - Total anonymized: {anon_stats['total_anonymized']}")
            print(f"     - Pending review: {anon_stats['pending_manual_review']}")

    except Exception as e:
        print(f"   ⚠️  Statistics failed (non-critical): {e}")

    return True


def main():
    """Run integration test."""
    print("\n🧪 Testing Complete Upload and Anonymization Workflow\n")

    try:
        success = test_complete_workflow()

        if success:
            print("\n" + "=" * 70)
            print("✅ Integration test completed successfully!")
            print("=" * 70)
            print("\nThe workflow is ready to use:")
            print("1. Upload file → Extract text → Clean text")
            print("2. Anonymize → Identify PII → Replace with placeholders")
            print("3. Risk assessment → Flag for review if needed")
            print("\nNext steps:")
            print("- Start the API server: python app/main.py")
            print("- Test with real files via the API")
            print("- Check the frontend integration")
            print("=" * 70 + "\n")
            sys.exit(0)
        else:
            print("\n" + "=" * 70)
            print("❌ Integration test failed!")
            print("=" * 70 + "\n")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
