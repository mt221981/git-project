"""E2E test for the full pipeline with new changes."""

import sys
import time
import re
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.database import SessionLocal
from app.models.verdict import Verdict, VerdictStatus
from app.services.analysis_service import AnalysisService
from app.services.article_service import ArticleService

print('=' * 80)
print('E2E TEST - Full Pipeline (Skip Anonymization)')
print('=' * 80)

verdict_id = 11
db = SessionLocal()

try:
    # Check initial state
    verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
    if not verdict:
        print(f'ERROR: Verdict {verdict_id} not found')
        sys.exit(1)

    print(f'\nStarting E2E test with Verdict {verdict_id}')
    print(f'Initial status: {verdict.status.value}')
    print(f'Case number: {verdict.case_number}')
    print(f'Has original_text: {bool(verdict.original_text)}')
    print(f'Has cleaned_text: {bool(verdict.cleaned_text)}')

    # STEP 1: Analysis (skip anonymization)
    print('\n' + '=' * 80)
    print('STEP 1: Analysis (directly from original text)')
    print('=' * 80)
    start_time = time.time()

    try:
        analysis_service = AnalysisService(db)
        analysis_service.analyze_verdict(verdict_id)
        analysis_time = time.time() - start_time

        # Refresh verdict
        db.refresh(verdict)
        print(f'✓ Analysis completed in {analysis_time:.1f} seconds')
        print(f'  Status: {verdict.status.value}')
        print(f'  Key facts: {len(verdict.key_facts or [])} items')
        print(f'  Legal questions: {len(verdict.legal_questions or [])} items')
        print(f'  Legal principles: {len(verdict.legal_principles or [])} items')

    except Exception as e:
        print(f'✗ Analysis failed: {str(e)}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # STEP 2: Article Generation
    print('\n' + '=' * 80)
    print('STEP 2: Article Generation (with new simple prompt)')
    print('=' * 80)
    start_time = time.time()

    try:
        article_service = ArticleService(db)
        article = article_service.generate_article_from_verdict(verdict_id)
        article_time = time.time() - start_time

        # Refresh verdict
        db.refresh(verdict)
        print(f'\n✓ Article generated in {article_time:.1f} seconds')
        print(f'  Status: {verdict.status.value}')
        print(f'  Article ID: {article.id}')
        print(f'  Title: {article.title}')
        print(f'  Word count: {article.word_count}')
        print(f'  Content score: {article.content_score}')
        print(f'  SEO score: {article.seo_score}')
        print(f'  Readability score: {article.readability_score}')
        print(f'  E-E-A-T score: {article.eeat_score}')

        # Check for case number citations in content
        print('\n' + '=' * 80)
        print('CITATION VALIDATION')
        print('=' * 80)

        content = article.content_html or ''

        # Check for problematic patterns
        case_patterns = [
            r'ע"א\s+\d+',  # ע"א 123
            r'ת"א\s+\d+',  # ת"א 123
            r'ע\.א\.\s+\d+',  # ע.א. 123
            r'ת\.א\.\s+\d+',  # ת.א. 123
            r'בג"ץ\s+\d+',  # בג"ץ 123
        ]

        found_citations = []
        for pattern in case_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_citations.extend(matches)

        if found_citations:
            print(f'⚠️  WARNING: Found {len(found_citations)} case number citations:')
            for citation in found_citations[:5]:  # Show first 5
                print(f'   - {citation}')
        else:
            print('✓ No problematic case number citations found')

        # Check for good patterns
        good_patterns = [
            'על פי הפסיקה',
            'ההלכה הפסוקה',
            'בפסיקה נקבע',
            'חוק'
        ]

        found_good = []
        for pattern in good_patterns:
            if pattern in content:
                found_good.append(pattern)

        if found_good:
            print(f'\n✓ Found {len(found_good)} good general references:')
            for ref in found_good:
                print(f'   - "{ref}"')

        # Summary
        print('\n' + '=' * 80)
        print('E2E TEST SUMMARY')
        print('=' * 80)
        total_time = analysis_time + article_time
        print(f'Total processing time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)')
        print(f'  - Analysis: {analysis_time:.1f}s')
        print(f'  - Article generation: {article_time:.1f}s')
        print(f'\nQuality Scores:')
        print(f'  - Content: {article.content_score}/100 (threshold: 85)')
        print(f'  - SEO: {article.seo_score}/100 (threshold: 85)')
        print(f'  - Readability: {article.readability_score}/100 (threshold: 85)')
        print(f'  - E-E-A-T: {article.eeat_score}/100 (threshold: 85)')

        all_passed = (
            article.content_score >= 85 and
            article.seo_score >= 85 and
            article.readability_score >= 85 and
            article.eeat_score >= 85
        )

        if all_passed:
            print('\n✓ ALL QUALITY THRESHOLDS MET!')
        else:
            print('\n⚠️  Some scores below threshold')
            failed = []
            if article.content_score < 85:
                failed.append(f'Content ({article.content_score})')
            if article.seo_score < 85:
                failed.append(f'SEO ({article.seo_score})')
            if article.readability_score < 85:
                failed.append(f'Readability ({article.readability_score})')
            if article.eeat_score < 85:
                failed.append(f'E-E-A-T ({article.eeat_score})')
            print(f'   Failed: {", ".join(failed)}')

        print(f'\nFinal status: {verdict.status.value}')
        print(f'Citation safety: {"✓ SAFE" if not found_citations else "⚠️ NEEDS REVIEW"}')

    except Exception as e:
        print(f'\n✗ Article generation failed: {str(e)}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

finally:
    db.close()

print('\n' + '=' * 80)
print('E2E TEST COMPLETED')
print('=' * 80)
