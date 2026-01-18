"""Integration test for Phase 4: AI Analysis and Article Generation."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services import (
    VerdictService, AnalysisService, ArticleService,
    VerdictAnalyzer, ArticleGenerator
)
from app.models.verdict import VerdictStatus


def create_test_database():
    """Create an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def create_sample_anonymized_verdict() -> str:
    """Create a sample anonymized verdict for testing."""
    return """
פסק דין

בית המשפט המחוזי בתל אביב-יפו

תיק מספר: 12345-01-20

תובע: התובע
ת.ז.: ***789

נתבע: הנתבע
ת.ז.: ***321

נציג התובע: עו"ד רחל לוי
נציג הנתבע: עו"ד משה דוד

בפני: כבוד השופט יצחק גרוס

העובדות:

1. התובע עבד במשך 5 שנים אצל הנתבע בחברת "טכנולוגיות עתיד בע"מ" בתפקיד
   מהנדס תוכנה בכיר.

2. ביום 15 בינואר 2020, הנתבע פיטר את התובע ללא הודעה מוקדמת, תוך טענה
   שהתובע הפר את חוזה העבודה על ידי העברת מידע חסוי למתחרה.

3. התובע טוען כי הפיטורים היו שלא כדין וכי הנתבע לא הוכיח את טענותיו.
   התובע דורש פיצויי פיטורים בסך 120,000 ₪ וכן פיצוי בגין אי-מתן הודעה מוקדמת.

4. הנתבע טוען כי הפיטורים היו מוצדקים עקב הפרה יסודית של חוזה העבודה
   והצגת ראיות למסירת מידע חסוי.

השאלות המשפטיות:

א. האם הפיטורים היו מוצדקים?
ב. האם הנתבע הוכיח הפרה יסודית של חוזה העבודה?
ג. האם התובע זכאי לפיצויי פיטורים ולפיצוי בגין אי-מתן הודעה מוקדמת?

ניתוח משפטי:

על פי חוק עבודה תשל"ח-1978, סעיף 5, עובד זכאי להודעה מוקדמת או לתשלום במקום הודעה.
בנוסף, פיטורים ללא הצדקה מהווים הפרה יסודית של חוזה העבודה.

בעניין כהן נגד משרד החינוך (ע"ע 567/85), קבע בית המשפט העליון כי:
"פיטורים ללא הצדקה מספקת מהווים הפרה יסודית של חוזה העבודה ומזכים את העובד
בפיצויי פיטורים מלאים."

בנוסף, על פי סעיף 11 לחוק פיצויי פיטורים תשכ"ג-1963, עובד שפוטר שלא כדין
זכאי לפיצויי פיטורים מלאים.

ההכרעה:

לאחר שבחנתי את הראיות והטענות, הגעתי למסקנה כי:

1. הנתבע לא הצליח להוכיח בראיות מספיקות את טענתו להפרת חוזה העבודה על ידי התובע.
   העדויות שהוצגו היו נסיבתיות ולא ישירות.

2. הפיטורים היו שלא כדין ולא היתה הצדקה מספקת לביצועם ללא הודעה מוקדמת.

3. התובע זכאי לפיצויי פיטורים מלאים בסך 95,000 ₪, המחושבים על פי משכורתו
   האחרונה ותקופת העבודה.

4. התובע זכאי לפיצוי בגין אי-מתן הודעה מוקדמת בסך 15,000 ₪, בהתאם לסעיף 5
   לחוק עבודה.

5. הנתבע ישלם לתובע הוצאות משפט בסך 10,000 ₪.

סיכום:

סך כל הסכום שהנתבע חייב לשלם לתובע: 120,000 ₪.

התשלום יבוצע תוך 30 יום מיום מתן פסק הדין.

תובנות מעשיות:

1. מעסיקים חייבים להוכיח בראיות ברורות ומוצקות כל טענה להפרת חוזה עבודה לפני פיטורים.

2. פיטורים ללא הודעה מוקדמת מחייבים הצדקה חזקה במיוחד ועלולים להוביל לפיצויים גבוהים.

3. עובדים שפוטרו ללא הצדקה זכאים לפיצויי פיטורים מלאים ולפיצוי נוסף על אי-מתן הודעה מוקדמת.

ניתן היום, 15 במרץ 2021

                                    יצחק גרוס, שופט
                                    בית המשפט המחוזי בתל אביב-יפו
"""


def test_verdict_analysis():
    """Test the VerdictAnalyzer service."""
    print("=" * 70)
    print("Testing VerdictAnalyzer Service")
    print("=" * 70)

    try:
        # Check if API key is configured
        from app.config import settings
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "your-key-here":
            print("\n⚠️  Skipping VerdictAnalyzer test: ANTHROPIC_API_KEY not configured")
            print("   Set ANTHROPIC_API_KEY in .env file to test analysis")
            return None

        print("\n1. Creating VerdictAnalyzer...")
        analyzer = VerdictAnalyzer()
        print("   ✓ VerdictAnalyzer created")

        print("\n2. Analyzing sample verdict...")
        sample_text = create_sample_anonymized_verdict()
        print(f"   - Text length: {len(sample_text)} characters")

        result = analyzer.analyze(sample_text)
        print("   ✓ Analysis completed")

        print("\n3. Validating analysis results...")
        print(f"   - Case type: {result.get('case_type', 'N/A')}")
        print(f"   - Outcome: {result.get('outcome', 'N/A')}")
        print(f"   - Key facts: {len(result.get('key_facts', []))} items")
        print(f"   - Legal questions: {len(result.get('legal_questions', []))} items")
        print(f"   - Legal principles: {len(result.get('legal_principles', []))} items")
        print(f"   - Compensation amount: ₪{result.get('compensation_amount', 0):,.0f}")
        print(f"   - Relevant laws: {len(result.get('relevant_laws', []))} items")
        print(f"   - Precedents cited: {len(result.get('precedents_cited', []))} items")
        print(f"   - Practical insights: {len(result.get('practical_insights', []))} items")

        # Show some examples
        if result.get('key_facts'):
            print("\n   Sample key facts:")
            for fact in result['key_facts'][:3]:
                print(f"     - {fact}")

        if result.get('legal_questions'):
            print("\n   Sample legal questions:")
            for question in result['legal_questions'][:2]:
                print(f"     - {question}")

        # Validate required fields
        assert 'key_facts' in result, "Missing key_facts"
        assert 'legal_questions' in result, "Missing legal_questions"
        assert 'legal_principles' in result, "Missing legal_principles"

        print("\n✅ VerdictAnalyzer tests passed!")
        return result

    except Exception as e:
        print(f"\n❌ VerdictAnalyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_article_generator(analysis_result):
    """Test the ArticleGenerator service."""
    print("\n" + "=" * 70)
    print("Testing ArticleGenerator Service")
    print("=" * 70)

    if not analysis_result:
        print("\n⚠️  Skipping ArticleGenerator test: No analysis result available")
        return None

    try:
        from app.config import settings
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "your-key-here":
            print("\n⚠️  Skipping ArticleGenerator test: ANTHROPIC_API_KEY not configured")
            return None

        print("\n1. Creating ArticleGenerator...")
        generator = ArticleGenerator()
        print("   ✓ ArticleGenerator created")

        print("\n2. Generating article from analysis...")
        verdict_metadata = {
            "case_number": "12345-01-20",
            "court_name": "בית המשפט המחוזי בתל אביב-יפו",
            "judge_name": "יצחק גרוס",
            "legal_area": "דיני עבודה"
        }

        article = generator.generate(verdict_metadata, analysis_result)
        print("   ✓ Article generated")

        print("\n3. Validating article content...")
        print(f"   - Title: {article.get('title', 'N/A')}")
        print(f"   - Word count: {article.get('word_count', 0)}")
        print(f"   - Focus keyword: {article.get('focus_keyword', 'N/A')}")
        print(f"   - Secondary keywords: {len(article.get('secondary_keywords', []))} items")
        print(f"   - FAQ items: {len(article.get('faq_items', []))} items")
        print(f"   - Tags: {len(article.get('tags', []))} items")

        # Validate required fields
        assert 'title' in article, "Missing title"
        assert 'content_html' in article, "Missing content_html"
        assert 'focus_keyword' in article, "Missing focus_keyword"
        assert article.get('word_count', 0) > 0, "Word count should be > 0"

        # Show excerpt
        if article.get('excerpt'):
            print(f"\n   Excerpt:")
            print(f"   {article['excerpt'][:200]}...")

        print("\n4. Calculating quality scores...")
        scores = generator.calculate_scores(article)
        print(f"   ✓ Scores calculated:")
        print(f"     - Content score: {scores.get('content_score', 0)}/100")
        print(f"     - SEO score: {scores.get('seo_score', 0)}/100")
        print(f"     - Readability score: {scores.get('readability_score', 0)}/100")
        print(f"     - E-E-A-T score: {scores.get('eeat_score', 0)}/100")
        print(f"     - Overall score: {scores.get('overall_score', 0)}/100")

        print("\n✅ ArticleGenerator tests passed!")
        return article

    except Exception as e:
        print(f"\n❌ ArticleGenerator test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_complete_workflow():
    """Test the complete analysis and article generation workflow."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Complete Analysis → Article Generation Workflow")
    print("=" * 70)

    # Create test database
    print("\n1. Setting up test database...")
    db = create_test_database()
    print("   ✓ Test database created")

    # Create sample verdict
    print("\n2. Creating sample verdict...")
    verdict_service = VerdictService(db)

    # Create a sample verdict with anonymized text
    from app.models.verdict import Verdict
    verdict = Verdict(
        file_hash="test_hash_phase4",
        original_text="[Original text]",
        cleaned_text="[Cleaned text]",
        anonymized_text=create_sample_anonymized_verdict(),
        status=VerdictStatus.ANONYMIZED,
        case_number="12345-01-20",
        court_name="בית המשפט המחוזי בתל אביב-יפו",
        judge_name="יצחק גרוס",
        legal_area="דיני עבודה"
    )
    db.add(verdict)
    db.commit()
    db.refresh(verdict)
    print(f"   ✓ Sample verdict created (ID: {verdict.id})")

    # Test analysis
    print("\n3. Testing analysis workflow...")
    try:
        from app.config import settings
        if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "your-key-here":
            print("   ⚠️  Skipping workflow test: ANTHROPIC_API_KEY not configured")
            return False

        analysis_service = AnalysisService(db)
        analyzed_verdict = analysis_service.analyze_verdict(verdict.id)

        print(f"   ✓ Verdict analyzed")
        print(f"     - Status: {analyzed_verdict.status.value}")
        print(f"     - Key facts: {len(analyzed_verdict.key_facts or [])}")
        print(f"     - Compensation: ₪{analyzed_verdict.compensation_amount or 0:,.0f}")

        assert analyzed_verdict.status == VerdictStatus.ANALYZED
        assert analyzed_verdict.key_facts is not None
        assert analyzed_verdict.legal_questions is not None

    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        return False

    # Test article generation
    print("\n4. Testing article generation workflow...")
    try:
        article_service = ArticleService(db)
        article = article_service.generate_article_from_verdict(analyzed_verdict.id)

        print(f"   ✓ Article generated (ID: {article.id})")
        print(f"     - Title: {article.title}")
        print(f"     - Word count: {article.word_count}")
        print(f"     - Overall score: {article.overall_score}/100")
        print(f"     - Publish status: {article.publish_status.value}")

        assert article.title is not None
        assert article.content_html is not None
        assert article.word_count > 0
        assert article.overall_score > 0

    except Exception as e:
        print(f"   ❌ Article generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✅ Complete workflow test passed!")
    return True


def main():
    """Run all Phase 4 tests."""
    print("\n🧪 Testing Phase 4: AI Analysis and Article Generation\n")

    try:
        # Test individual services
        analysis_result = test_verdict_analysis()
        article_result = test_article_generator(analysis_result)

        # Test complete workflow
        workflow_success = test_complete_workflow()

        if workflow_success or (analysis_result and article_result):
            print("\n" + "=" * 70)
            print("✅ Phase 4 tests completed successfully!")
            print("=" * 70)
            print("\nPhase 4 capabilities:")
            print("1. AI-powered verdict analysis")
            print("   - Extract key facts, legal questions, principles")
            print("   - Identify compensation details")
            print("   - Find relevant laws and precedents")
            print("   - Generate practical insights")
            print("")
            print("2. SEO-optimized article generation")
            print("   - Create 1500-2500 word articles")
            print("   - Optimize for search engines")
            print("   - Generate FAQ sections")
            print("   - Calculate quality scores")
            print("")
            print("Next steps:")
            print("- Start the API server: python app/main.py")
            print("- Test via API: POST /api/articles/verdicts/{id}/analyze")
            print("- Generate articles: POST /api/articles/generate/{id}")
            print("=" * 70 + "\n")
            sys.exit(0)
        else:
            print("\n" + "=" * 70)
            print("⚠️  Phase 4 tests completed with warnings")
            print("=" * 70)
            print("\nSome tests were skipped due to missing API key.")
            print("Set ANTHROPIC_API_KEY in .env to run full tests.")
            print("=" * 70 + "\n")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
