"""Test script for FileProcessor and Anonymizer services."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.file_processor import FileProcessor, FileProcessingError
from app.services.anonymizer import Anonymizer, AnonymizationError


def test_file_processor():
    """Test FileProcessor service."""
    print("=" * 60)
    print("Testing FileProcessor Service")
    print("=" * 60)

    processor = FileProcessor()

    # Test 1: Calculate hash
    print("\n1. Testing calculate_hash()...")
    test_content = "שלום עולם".encode('utf-8')
    hash_val = processor.calculate_hash(test_content)
    print(f"   ✓ Hash calculated: {hash_val[:16]}...")
    assert len(hash_val) == 64, "Hash should be 64 characters"

    # Test 2: Extract text from TXT
    print("\n2. Testing extract_text() with TXT...")
    txt_content = """פסק דין
בית המשפט המחוזי בתל אביב

תיק: 12345-01-20

התובע: ישראל ישראלי, ת.ז. 123456789
כתובת: רחוב הרצל 10, תל אביב
טלפון: 052-1234567

הנתבע: חברת XYZ בע"מ

פסק הדין:

עובדות: התובע עבד בחברה במשך 5 שנים...
""".encode('utf-8')

    extracted = processor.extract_text(txt_content, '.txt')
    print(f"   ✓ Text extracted: {len(extracted)} characters")
    assert "פסק דין" in extracted
    assert "תל אביב" in extracted

    # Test 3: Clean text
    print("\n3. Testing clean_text()...")
    dirty_text = """פסק דין


עמוד 1 מתוך 5

בית המשפט המחוזי    בתל  אביב

1

תיק: 12345-01-20


עובדות:  התובע  עבד  בחברה...
עמוד 2 מתוך 5
"""

    cleaned = processor.clean_text(dirty_text)
    print(f"   ✓ Text cleaned: {len(cleaned)} characters")
    # Should remove page numbers and normalize whitespace
    assert "עמוד 1 מתוך 5" not in cleaned
    assert "בתל  אביב" not in cleaned  # Should fix multiple spaces

    # Test 4: Get text stats
    print("\n4. Testing get_text_stats()...")
    stats = processor.get_text_stats(extracted)
    print(f"   ✓ Stats: {stats['word_count']} words, {stats['char_count']} chars")
    assert stats['has_hebrew'] == True
    assert stats['word_count'] > 0

    print("\n✅ FileProcessor tests passed!")


def test_anonymizer():
    """Test Anonymizer service."""
    print("\n" + "=" * 60)
    print("Testing Anonymizer Service")
    print("=" * 60)

    try:
        anonymizer = Anonymizer()
    except ValueError as e:
        print(f"\n⚠️  Skipping Anonymizer tests: {e}")
        print("   Set ANTHROPIC_API_KEY in .env file to test")
        return

    # Test with sample legal text
    print("\n1. Testing anonymize() with Hebrew legal text...")

    sample_text = """פסק דין

בית המשפט המחוזי בתל אביב

תובע: ישראל ישראלי, ת.ז. 123456789
כתובת: רחוב הרצל 10, תל אביב 12345
טלפון: 052-1234567
אימייל: israel@example.com

נתבע: דוד כהן, ת.ז. 987654321

העובדות:
1. התובע, מר ישראל ישראלי, עבד אצל הנתבע במשך 5 שנים
2. הנתבע, מר דוד כהן, פיטר את התובע ללא הודעה מוקדמת
3. התובע התגורר ברחוב הרצל 10 והיה נסע לעבודה מדי יום

פסק הדין:
אני קובע כי הנתבע חייב לשלם לתובע פיצוי בסך 50,000 ש"ח.

שופט: כבוד השופט משה לוי
עורך דין התובע: עו"ד רחל גולן
"""

    print(f"   Original text length: {len(sample_text)} characters")

    try:
        result = anonymizer.anonymize(sample_text)

        print(f"   ✓ Anonymization completed")
        print(f"   - Anonymized text length: {len(result['anonymized_text'])} characters")
        print(f"   - Items identified: {len(result['report'])}")
        print(f"   - Risk level: {result['risk_level']}")
        print(f"   - Requires review: {result['requires_review']}")

        # Show some identified items
        print("\n   Identified items:")
        for item in result['report'][:5]:  # Show first 5
            print(f"     - {item['category']}: '{item['original']}' → '{item['replacement']}' (confidence: {item['confidence']})")

        if len(result['report']) > 5:
            print(f"     ... and {len(result['report']) - 5} more items")

        # Verify anonymization worked
        anonymized = result['anonymized_text']

        # Should NOT contain original names
        assert "ישראל ישראלי" not in anonymized, "Original name should be anonymized"
        assert "דוד כהן" not in anonymized, "Original name should be anonymized"

        # Should still contain judge and lawyer names (public info)
        assert "משה לוי" in anonymized or "השופט" in anonymized, "Judge name should remain"

        # Should still contain case numbers and amounts
        assert "50,000" in anonymized, "Amounts should remain"

        print("\n2. Testing get_stats()...")
        stats = anonymizer.get_stats(result['report'])
        print(f"   ✓ Stats calculated:")
        print(f"     - Total items: {stats['total_items']}")
        print(f"     - By category: {stats['by_category']}")
        print(f"     - By confidence: {stats['by_confidence']}")
        print(f"     - High risk items: {stats['high_risk_count']}")

        print("\n✅ Anonymizer tests passed!")

    except AnonymizationError as e:
        print(f"\n❌ Anonymization failed: {e}")
        raise


def main():
    """Run all tests."""
    print("\n🧪 Testing File Processing and Anonymization Services\n")

    try:
        test_file_processor()
        test_anonymizer()

        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
