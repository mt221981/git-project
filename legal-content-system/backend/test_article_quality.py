"""Test article generation with improved prompts to verify quality scores."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.article_generator import ArticleGenerator
from app.services.quality_checker import QualityChecker
from app.config import settings


def test_article_generation():
    """Generate a test article and check its quality scores."""
    print("=" * 70)
    print("ARTICLE QUALITY TEST: Testing Improved Prompts")
    print("=" * 70)

    # Check API key
    if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "your-key-here":
        print("\n❌ Error: ANTHROPIC_API_KEY not configured")
        print("Set ANTHROPIC_API_KEY in .env file to run this test")
        return False

    # Sample verdict data
    sample_verdict = {
        "case_number": "12345-01-20",
        "court_name": "בית המשפט המחוזי בתל אביב-יפו",
        "judge_name": "יצחק גרוס",
        "verdict_date": "2021-03-15",
        "legal_area": "דיני עבודה",
        "parties": {
            "plaintiff": "ישראל ישראלי",
            "defendant": "דוד כהן"
        },
        "summary": """התובע, עובד שפוטר ללא הודעה מוקדמת, תבע פיצויי פיטורים ופיצוי בגין אי-מתן הודעה מוקדמת.
        בית המשפט קבע כי הפיטורים היו שלא כדין וחייב את הנתבע לשלם סך 120,000 ₪.""",
        "legal_issues": [
            "פיטורים שלא כדין",
            "זכאות לפיצויי פיטורים",
            "הודעה מוקדמת"
        ],
        "legal_citations": [
            "חוק עבודה תשל\"ח-1978",
            "סעיף 11 לחוק פיצויי פיטורים",
            "סעיף 2 לחוק הודעה מוקדמת"
        ],
        "precedents": [
            {
                "case_name": "כהן נגד משרד החינוך",
                "citation": "ע\"ע 567/85",
                "principle": "פיטורים ללא הצדקה מהווים הפרה יסודית של חוזה העבודה"
            }
        ],
        "decision": """בית המשפט קבע כי הפיטורים היו שלא כדין וחייב את הנתבע לשלם:
        1. פיצויי פיטורים בסך 95,000 ₪
        2. פיצוי בגין אי-מתן הודעה מוקדמת בסך 15,000 ₪
        3. הוצאות משפט בסך 10,000 ₪"""
    }

    # Initialize services
    print("\n1. Initializing services...")
    try:
        generator = ArticleGenerator()
        quality_checker = QualityChecker()
        print("   ✓ Services initialized")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Generate article
    print("\n2. Generating article with improved prompts...")
    print("   (This may take 30-60 seconds...)")
    try:
        article_data = generator.generate(sample_verdict)
        print("   ✓ Article generated successfully")
        print(f"   - Word count: {article_data['word_count']}")
        print(f"   - Reading time: {article_data['reading_time_minutes']} minutes")
        print(f"   - FAQ items: {len(article_data.get('faq_items', []))}")
        print(f"   - Common mistakes: {len(article_data.get('common_mistakes', []))}")
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check quality
    print("\n3. Checking article quality...")
    try:
        quality_result = quality_checker.check_quality(
            content_html=article_data['content_html'],
            title=article_data['title'],
            meta_description=article_data['meta_description'],
            focus_keyword=article_data['focus_keyword'],
            secondary_keywords=article_data.get('secondary_keywords', [])
        )

        print("   ✓ Quality check completed")
        print("\n" + "=" * 70)
        print("QUALITY SCORES:")
        print("=" * 70)

        # Overall score
        overall = quality_result['overall_score']
        print(f"\n📊 Overall Score: {overall:.1f}/100")

        # Category scores
        scores = quality_result['category_scores']
        print(f"\n📝 Content Score: {scores['content']:.1f}/100")
        print(f"🔍 SEO Score: {scores['seo']:.1f}/100")
        print(f"📖 Readability Score: {scores['readability']:.1f}/100")
        print(f"🎯 E-E-A-T Score: {scores['eeat']:.1f}/100")

        # Detailed breakdown
        print("\n" + "-" * 70)
        print("DETAILED BREAKDOWN:")
        print("-" * 70)

        details = quality_result['details']

        # Content details
        if 'content' in details:
            content = details['content']
            print(f"\n📝 Content:")
            print(f"   - Word count: {content.get('word_count', 0)} (target: 1800+)")
            print(f"   - H2 headings: {content.get('h2_count', 0)} (target: 7-8)")
            print(f"   - H3 headings: {content.get('h3_count', 0)} (target: 10-12)")
            print(f"   - Paragraphs: {content.get('paragraph_count', 0)}")
            print(f"   - FAQ items: {content.get('faq_count', 0)} (target: 8-10)")
            print(f"   - Lists: {content.get('list_count', 0)} (target: 5-6)")

        # SEO details
        if 'seo' in details:
            seo = details['seo']
            print(f"\n🔍 SEO:")
            print(f"   - Title length: {seo.get('title_length', 0)} chars (target: 50-60)")
            print(f"   - Meta desc length: {seo.get('meta_description_length', 0)} chars (target: 150-155)")
            print(f"   - Keyword density: {seo.get('keyword_density', 0):.2f}% (target: 1.0-1.2%)")
            print(f"   - Keyword in title: {seo.get('keyword_in_title', False)}")
            print(f"   - Secondary keywords found: {seo.get('secondary_keywords_found', 0)}/{seo.get('secondary_keywords_total', 0)}")

        # Readability details
        if 'readability' in details:
            read = details['readability']
            print(f"\n📖 Readability:")
            print(f"   - Avg sentence length: {read.get('avg_sentence_length', 0):.1f} words (target: 15-18)")
            print(f"   - Avg paragraph length: {read.get('avg_paragraph_length', 0):.1f} words")
            print(f"   - Transition words: {read.get('transition_word_count', 0)} (target: 10-12)")

        # E-E-A-T details
        if 'eeat' in details:
            eeat = details['eeat']
            print(f"\n🎯 E-E-A-T:")
            print(f"   - Legal citations: {eeat.get('citation_count', 0)} (target: 6-8)")
            print(f"   - Precedent citations: {eeat.get('precedent_count', 0)} (target: 2-3)")
            print(f"   - Has disclaimer: {eeat.get('has_disclaimer', False)}")
            print(f"   - Has CTA: {eeat.get('has_cta', False)}")
            print(f"   - Legal terms: {eeat.get('legal_term_count', 0)} (target: 12+)")

        # Recommendations
        if quality_result.get('recommendations'):
            print("\n" + "-" * 70)
            print("RECOMMENDATIONS:")
            print("-" * 70)
            for rec in quality_result['recommendations']:
                print(f"   • {rec}")

        # Success criteria
        print("\n" + "=" * 70)
        if overall >= 95:
            print("✅ EXCELLENT! Article reached target score of 95+")
        elif overall >= 90:
            print("🟢 VERY GOOD! Article scored 90+ (close to target)")
        elif overall >= 80:
            print("🟡 GOOD! Article scored 80+ (needs minor improvements)")
        elif overall >= 70:
            print("🟠 ACCEPTABLE! Article scored 70+ (needs improvements)")
        else:
            print("🔴 NEEDS WORK! Article scored below 70")
        print("=" * 70)

        return overall >= 95

    except Exception as e:
        print(f"   ❌ Quality check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    print("\n🧪 Testing Article Generation with Improved Prompts\n")

    try:
        success = test_article_generation()

        if success:
            print("\n✅ Test passed! Articles now achieve 95+ scores.")
            sys.exit(0)
        else:
            print("\n⚠️  Test completed but scores need improvement.")
            print("Review the detailed breakdown above for areas to enhance.")
            sys.exit(0)  # Exit 0 even if not perfect, to see results

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
