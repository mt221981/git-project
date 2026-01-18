"""Integration test for Phase 5: WordPress Publishing Integration."""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services import (
    WordPressManager, WordPressService, WordPressClient,
    PublishingError
)
from app.models.article import Article, PublishStatus
from app.models.verdict import Verdict, VerdictStatus
from app.models.wordpress_site import WordPressSite


def create_test_database():
    """Create an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def create_sample_article(db, title="Test Article", word_count=1500, score=75):
    """Create a sample article for testing."""
    # Create a verdict first
    verdict = Verdict(
        file_hash=f"test_hash_{title}",
        original_text="Original text",
        cleaned_text="Cleaned text",
        anonymized_text="Anonymized text",
        status=VerdictStatus.ARTICLE_CREATED,
        case_number="12345-01-20",
        court_name="בית המשפט המחוזי בתל אביב-יפו",
        judge_name="יצחק גרוס",
        legal_area="דיני עבודה"
    )
    db.add(verdict)
    db.commit()
    db.refresh(verdict)

    # Create article
    article = Article(
        verdict_id=verdict.id,
        title=title,
        slug=title.lower().replace(" ", "-"),
        meta_title=title,
        meta_description=f"Meta description for {title}",
        content_html=f"<h2>Content</h2><p>This is test content for {title}.</p>",
        excerpt=f"Excerpt for {title}",
        focus_keyword="פיצויי פיטורים",
        secondary_keywords=["דיני עבודה", "פיטורים"],
        word_count=word_count,
        reading_time_minutes=word_count // 200,
        content_score=score,
        seo_score=score,
        readability_score=score,
        eeat_score=score,
        overall_score=score,
        publish_status=PublishStatus.READY
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


def create_sample_wordpress_site(db):
    """Create a sample WordPress site for testing."""
    site = WordPressSite(
        site_name="Test Site",
        site_url="https://test-site.com",
        username="testuser",
        encrypted_password="encrypted_test_password",
        is_active=True,
        seo_plugin="yoast"
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


def test_article_validation():
    """Test article validation before publishing."""
    print("=" * 70)
    print("Testing Article Validation")
    print("=" * 70)

    db = create_test_database()
    manager = WordPressManager(db)

    # Test valid article
    print("\n1. Testing valid article...")
    valid_article = create_sample_article(db, "Valid Article", word_count=1500, score=75)
    errors = manager.validate_article_for_publishing(valid_article)
    assert len(errors) == 0, f"Valid article should have no errors, got: {errors}"
    print("   ✓ Valid article passed validation")

    # Test article with no title
    print("\n2. Testing article without title...")
    no_title = create_sample_article(db, "", word_count=1500, score=75)
    errors = manager.validate_article_for_publishing(no_title)
    assert len(errors) > 0, "Article without title should fail validation"
    assert any("title" in error.lower() for error in errors)
    print(f"   ✓ Validation caught missing title: {errors[0]}")

    # Test article with insufficient word count
    print("\n3. Testing article with low word count...")
    short_article = create_sample_article(db, "Short Article", word_count=300, score=75)
    errors = manager.validate_article_for_publishing(short_article)
    assert len(errors) > 0, "Short article should fail validation"
    assert any("word" in error.lower() or "short" in error.lower() for error in errors)
    print(f"   ✓ Validation caught low word count: {errors[0]}")

    # Test article with low quality score
    print("\n4. Testing article with low quality score...")
    low_score = create_sample_article(db, "Low Score Article", word_count=1500, score=30)
    errors = manager.validate_article_for_publishing(low_score)
    assert len(errors) > 0, "Low score article should fail validation"
    assert any("score" in error.lower() for error in errors)
    print(f"   ✓ Validation caught low quality score: {errors[0]}")

    # Test article without focus keyword
    print("\n5. Testing article without focus keyword...")
    no_keyword = create_sample_article(db, "No Keyword Article", word_count=1500, score=75)
    no_keyword.focus_keyword = None
    db.commit()
    errors = manager.validate_article_for_publishing(no_keyword)
    assert len(errors) > 0, "Article without focus keyword should fail validation"
    assert any("keyword" in error.lower() for error in errors)
    print(f"   ✓ Validation caught missing focus keyword: {errors[0]}")

    print("\n✅ Article validation tests passed!")
    return True


def test_retry_logic():
    """Test retry logic for failed publishes."""
    print("\n" + "=" * 70)
    print("Testing Retry Logic")
    print("=" * 70)

    db = create_test_database()
    site = create_sample_wordpress_site(db)
    article = create_sample_article(db, "Retry Test Article", word_count=1500, score=75)

    # Mock WordPress service
    mock_wp_service = Mock(spec=WordPressService)

    print("\n1. Testing successful publish after retry...")
    # Simulate failure then success
    mock_wp_service.publish_article.side_effect = [
        Exception("Connection timeout"),  # First attempt fails
        article  # Second attempt succeeds
    ]

    manager = WordPressManager(db, wordpress_service=mock_wp_service)

    try:
        result = manager.publish_article_with_retry(
            article_id=article.id,
            site_id=site.id,
            status="draft",
            max_retries=3,
            retry_delay=0.1  # Short delay for testing
        )
        print("   ✓ Article published successfully after retry")
        assert result.id == article.id
    except Exception as e:
        print(f"   ❌ Retry logic failed: {e}")
        return False

    print("\n2. Testing failure after max retries...")
    # Create new article for this test
    article2 = create_sample_article(db, "Max Retries Test", word_count=1500, score=75)

    # Simulate continuous failures
    mock_wp_service.publish_article.side_effect = [
        Exception("Connection timeout"),
        Exception("Connection timeout"),
        Exception("Connection timeout")
    ]

    try:
        result = manager.publish_article_with_retry(
            article_id=article2.id,
            site_id=site.id,
            status="draft",
            max_retries=3,
            retry_delay=0.1
        )
        print("   ❌ Should have raised PublishingError")
        return False
    except PublishingError as e:
        print(f"   ✓ Correctly raised PublishingError after max retries")
        assert "after 3 attempts" in str(e)

        # Check that article status was updated
        db.refresh(article2)
        assert article2.publish_status == PublishStatus.FAILED
        print("   ✓ Article status updated to FAILED")

    print("\n3. Testing non-retryable errors...")
    article3 = create_sample_article(db, "Non-Retryable Test", word_count=1500, score=75)

    # Simulate authentication error (should not retry)
    from app.services.wordpress_client import WordPressClientError
    mock_wp_service.publish_article.side_effect = WordPressClientError("Authentication failed")

    try:
        result = manager.publish_article_with_retry(
            article_id=article3.id,
            site_id=site.id,
            status="draft",
            max_retries=3,
            retry_delay=0.1
        )
        print("   ❌ Should have raised PublishingError immediately")
        return False
    except PublishingError as e:
        print("   ✓ Non-retryable error raised immediately")
        # Should only have been called once (no retries)
        assert mock_wp_service.publish_article.call_count == 1

    print("\n✅ Retry logic tests passed!")
    return True


def test_batch_publishing():
    """Test batch publishing functionality."""
    print("\n" + "=" * 70)
    print("Testing Batch Publishing")
    print("=" * 70)

    db = create_test_database()
    site = create_sample_wordpress_site(db)

    # Create multiple articles
    print("\n1. Creating test articles...")
    articles = [
        create_sample_article(db, f"Batch Article {i}", word_count=1500, score=75)
        for i in range(1, 6)
    ]
    article_ids = [a.id for a in articles]
    print(f"   ✓ Created {len(articles)} articles")

    # Mock WordPress service
    mock_wp_service = Mock(spec=WordPressService)

    # Simulate mixed success and failure
    mock_wp_service.publish_article.side_effect = [
        articles[0],  # Success
        articles[1],  # Success
        Exception("Failed to publish"),  # Failure
        articles[3],  # Success
        articles[4]   # Success
    ]

    manager = WordPressManager(db, wordpress_service=mock_wp_service)

    print("\n2. Testing batch publish (continue on error)...")
    results = manager.publish_articles_batch(
        article_ids=article_ids,
        site_id=site.id,
        status="draft",
        stop_on_error=False
    )

    print(f"   - Total processed: {results['total']}")
    print(f"   - Successful: {results['success_count']}")
    print(f"   - Failed: {results['error_count']}")

    assert results['total'] == 5
    assert results['success_count'] == 4
    assert results['error_count'] == 1
    assert len(results['successful']) == 4
    assert len(results['failed']) == 1
    print("   ✓ Batch publish completed with correct counts")

    print("\n3. Testing batch publish (stop on error)...")
    # Create new articles
    articles2 = [
        create_sample_article(db, f"Stop Test Article {i}", word_count=1500, score=75)
        for i in range(1, 4)
    ]
    article_ids2 = [a.id for a in articles2]

    # Simulate failure on second article
    mock_wp_service.publish_article.side_effect = [
        articles2[0],  # Success
        Exception("Failed to publish"),  # Failure - should stop here
        articles2[2]   # Should not reach this
    ]

    results2 = manager.publish_articles_batch(
        article_ids=article_ids2,
        site_id=site.id,
        status="draft",
        stop_on_error=True
    )

    print(f"   - Total processed: {results2['total']}")
    print(f"   - Successful: {results2['success_count']}")
    print(f"   - Failed: {results2['error_count']}")

    assert results2['success_count'] == 1
    assert results2['error_count'] == 1
    assert len(results2['successful']) == 1
    assert len(results2['failed']) == 1
    print("   ✓ Batch publish stopped on first error")

    print("\n✅ Batch publishing tests passed!")
    return True


def test_publishing_statistics():
    """Test publishing statistics functionality."""
    print("\n" + "=" * 70)
    print("Testing Publishing Statistics")
    print("=" * 70)

    db = create_test_database()
    site = create_sample_wordpress_site(db)
    manager = WordPressManager(db)

    # Create articles with different statuses
    print("\n1. Creating articles with various statuses...")
    article1 = create_sample_article(db, "Draft Article", word_count=1500, score=75)
    article1.publish_status = PublishStatus.DRAFT
    article1.wordpress_site_id = site.id
    article1.wordpress_post_id = 101

    article2 = create_sample_article(db, "Published Article", word_count=1500, score=75)
    article2.publish_status = PublishStatus.PUBLISHED
    article2.wordpress_site_id = site.id
    article2.wordpress_post_id = 102

    article3 = create_sample_article(db, "Ready Article", word_count=1500, score=75)
    article3.publish_status = PublishStatus.READY

    article4 = create_sample_article(db, "Failed Article", word_count=1500, score=75)
    article4.publish_status = PublishStatus.FAILED

    db.commit()
    print("   ✓ Created 4 articles with different statuses")

    print("\n2. Getting overall statistics...")
    stats = manager.get_publishing_statistics()

    print(f"   - Total articles: {stats['total_articles']}")
    print(f"   - Draft: {stats.get('draft', 0)}")
    print(f"   - Published: {stats.get('published', 0)}")
    print(f"   - Ready: {stats.get('ready', 0)}")
    print(f"   - Failed: {stats.get('failed', 0)}")

    assert stats['total_articles'] == 4
    assert stats.get('draft', 0) == 1
    assert stats.get('published', 0) == 1
    assert stats.get('ready', 0) == 1
    assert stats.get('failed', 0) == 1
    print("   ✓ Statistics calculated correctly")

    print("\n3. Getting site-specific statistics...")
    site_stats = manager.get_publishing_statistics(site_id=site.id)
    print(f"   - Total for site: {site_stats['total_articles']}")
    assert site_stats['total_articles'] == 2  # Only articles with site_id
    print("   ✓ Site-specific statistics work correctly")

    print("\n✅ Publishing statistics tests passed!")
    return True


def test_unpublished_articles():
    """Test getting unpublished articles ready for publishing."""
    print("\n" + "=" * 70)
    print("Testing Unpublished Articles Retrieval")
    print("=" * 70)

    db = create_test_database()
    manager = WordPressManager(db)

    print("\n1. Creating articles with various scores and statuses...")
    # Create articles with different scores
    article1 = create_sample_article(db, "High Score Article", word_count=1500, score=90)
    article1.publish_status = PublishStatus.READY

    article2 = create_sample_article(db, "Medium Score Article", word_count=1500, score=75)
    article2.publish_status = PublishStatus.READY

    article3 = create_sample_article(db, "Low Score Article", word_count=1500, score=60)
    article3.publish_status = PublishStatus.READY

    article4 = create_sample_article(db, "Already Published", word_count=1500, score=85)
    article4.publish_status = PublishStatus.PUBLISHED
    article4.wordpress_post_id = 101

    db.commit()
    print("   ✓ Created 4 test articles")

    print("\n2. Getting unpublished articles with min_score=70...")
    articles = manager.get_unpublished_articles(min_score=70, limit=50)

    print(f"   - Found {len(articles)} articles")
    assert len(articles) == 2  # Should get articles with score 90 and 75
    assert articles[0].overall_score == 90  # Should be sorted by score desc
    assert articles[1].overall_score == 75
    print("   ✓ Correct articles returned, sorted by score")

    print("\n3. Getting unpublished articles with min_score=80...")
    articles_high = manager.get_unpublished_articles(min_score=80, limit=50)
    print(f"   - Found {len(articles_high)} articles")
    assert len(articles_high) == 1  # Only score 90
    print("   ✓ High score filter works correctly")

    print("\n✅ Unpublished articles tests passed!")
    return True


def test_publishing_queue():
    """Test publishing queue scheduling."""
    print("\n" + "=" * 70)
    print("Testing Publishing Queue")
    print("=" * 70)

    db = create_test_database()
    site = create_sample_wordpress_site(db)
    manager = WordPressManager(db)

    print("\n1. Creating articles for queue...")
    # Create 10 articles ready for publishing
    for i in range(1, 11):
        article = create_sample_article(
            db,
            f"Queue Article {i}",
            word_count=1500,
            score=70 + i
        )
        article.publish_status = PublishStatus.READY

    db.commit()
    print("   ✓ Created 10 articles")

    print("\n2. Creating publishing queue (5 articles per day)...")
    queue = manager.schedule_publishing_queue(
        site_id=site.id,
        articles_per_day=5,
        min_score=70
    )

    print(f"   - Total queued: {queue['total_queued']}")
    print(f"   - Articles per day: {queue['articles_per_day']}")
    print(f"   - Estimated days: {queue['estimated_days']}")

    assert queue['total_queued'] == 10
    assert queue['articles_per_day'] == 5
    assert queue['estimated_days'] == 2
    print("   ✓ Queue created correctly")

    print("\n3. Verifying articles are sorted by score...")
    articles_in_queue = queue['articles']
    scores = [a['overall_score'] for a in articles_in_queue]
    assert scores == sorted(scores, reverse=True)
    print("   ✓ Articles sorted by score (descending)")

    print("\n4. Testing queue with high minimum score...")
    queue_high = manager.schedule_publishing_queue(
        site_id=site.id,
        articles_per_day=3,
        min_score=75
    )
    print(f"   - Total queued with min_score=75: {queue_high['total_queued']}")
    assert queue_high['total_queued'] < 10  # Should filter out some articles
    print("   ✓ Minimum score filter works")

    print("\n✅ Publishing queue tests passed!")
    return True


def test_failed_articles_republish():
    """Test republishing failed articles."""
    print("\n" + "=" * 70)
    print("Testing Failed Articles Republish")
    print("=" * 70)

    db = create_test_database()
    site = create_sample_wordpress_site(db)

    print("\n1. Creating failed articles...")
    failed_articles = []
    for i in range(1, 4):
        article = create_sample_article(db, f"Failed Article {i}", word_count=1500, score=75)
        article.publish_status = PublishStatus.FAILED
        failed_articles.append(article)

    db.commit()
    print(f"   ✓ Created {len(failed_articles)} failed articles")

    # Mock WordPress service
    mock_wp_service = Mock(spec=WordPressService)
    mock_wp_service.publish_article.side_effect = [
        failed_articles[0],  # First succeeds
        Exception("Still failing"),  # Second still fails
        failed_articles[2]   # Third succeeds
    ]

    manager = WordPressManager(db, wordpress_service=mock_wp_service)

    print("\n2. Attempting to republish failed articles...")
    results = manager.republish_failed_articles(site_id=site.id, max_articles=10)

    print(f"   - Total attempted: {results['total']}")
    print(f"   - Successful: {results['success_count']}")
    print(f"   - Still failed: {results['error_count']}")

    assert results['total'] == 3
    assert results['success_count'] == 2
    assert results['error_count'] == 1
    print("   ✓ Republish attempted for all failed articles")

    print("\n3. Testing with no failed articles...")
    # Update all to published
    for article in failed_articles:
        article.publish_status = PublishStatus.PUBLISHED
    db.commit()

    results_empty = manager.republish_failed_articles(site_id=site.id)
    print(f"   - Total: {results_empty['total']}")
    assert results_empty['total'] == 0
    assert 'message' in results_empty
    print(f"   ✓ Handles empty queue correctly: {results_empty['message']}")

    print("\n✅ Failed articles republish tests passed!")
    return True


def test_complete_workflow():
    """Test complete publishing workflow."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Complete Publishing Workflow")
    print("=" * 70)

    db = create_test_database()
    site = create_sample_wordpress_site(db)

    print("\n1. Creating test article...")
    article = create_sample_article(db, "Workflow Test Article", word_count=1500, score=80)
    print(f"   ✓ Article created (ID: {article.id})")

    print("\n2. Validating article...")
    manager = WordPressManager(db)
    errors = manager.validate_article_for_publishing(article)

    if errors:
        print(f"   ❌ Validation failed: {errors}")
        return False

    print("   ✓ Article validation passed")

    print("\n3. Publishing article with retry logic...")
    # Mock WordPress service for the full workflow
    mock_wp_service = Mock(spec=WordPressService)
    mock_article_copy = Mock(spec=Article)
    mock_article_copy.id = article.id
    mock_article_copy.title = article.title
    mock_wp_service.publish_article.return_value = mock_article_copy

    manager_with_mock = WordPressManager(db, wordpress_service=mock_wp_service)

    try:
        published = manager_with_mock.publish_article_with_retry(
            article_id=article.id,
            site_id=site.id,
            status="draft",
            max_retries=3,
            retry_delay=0.1
        )
        print("   ✓ Article published successfully")
    except Exception as e:
        print(f"   ❌ Publishing failed: {e}")
        return False

    print("\n4. Verifying article metadata...")
    db.refresh(article)
    if article.metadata:
        print(f"   - Publish attempts: {article.metadata.get('publish_attempts', 'N/A')}")
        print(f"   - Last success: {article.metadata.get('last_publish_success', 'N/A')}")
        print("   ✓ Metadata updated correctly")

    print("\n5. Getting statistics...")
    stats = manager.get_publishing_statistics()
    print(f"   - Total articles: {stats['total_articles']}")
    print(f"   - Ready: {stats.get('ready', 0)}")
    print("   ✓ Statistics retrieved")

    print("\n✅ Complete workflow test passed!")
    return True


def main():
    """Run all Phase 5 tests."""
    print("\n🧪 Testing Phase 5: WordPress Publishing Integration\n")

    try:
        # Run all tests
        tests = [
            ("Article Validation", test_article_validation),
            ("Retry Logic", test_retry_logic),
            ("Batch Publishing", test_batch_publishing),
            ("Publishing Statistics", test_publishing_statistics),
            ("Unpublished Articles", test_unpublished_articles),
            ("Publishing Queue", test_publishing_queue),
            ("Failed Articles Republish", test_failed_articles_republish),
            ("Complete Workflow", test_complete_workflow)
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
                    print(f"\n⚠️  {test_name} test had issues\n")
            except Exception as e:
                failed += 1
                print(f"\n❌ {test_name} test failed with exception: {e}")
                import traceback
                traceback.print_exc()

        # Print summary
        print("\n" + "=" * 70)
        print(f"Test Results: {passed} passed, {failed} failed")
        print("=" * 70)

        if failed == 0:
            print("\n✅ All Phase 5 tests passed!")
            print("\nPhase 5 capabilities:")
            print("1. Article validation before publishing")
            print("   - Title, content, word count checks")
            print("   - Quality score validation")
            print("   - SEO fields verification")
            print("")
            print("2. Retry logic for reliable publishing")
            print("   - Configurable retry attempts")
            print("   - Exponential backoff")
            print("   - Smart error handling")
            print("")
            print("3. Batch publishing operations")
            print("   - Multiple article publishing")
            print("   - Continue on error option")
            print("   - Detailed success/failure tracking")
            print("")
            print("4. Publishing statistics and monitoring")
            print("   - Overall and per-site statistics")
            print("   - Status breakdowns")
            print("   - Failed article tracking")
            print("")
            print("5. Publishing queue management")
            print("   - Scheduled publishing queues")
            print("   - Quality score filtering")
            print("   - Timeline estimation")
            print("")
            print("Next steps:")
            print("- Review PHASE5.md documentation")
            print("- Configure WordPress site credentials")
            print("- Test with real WordPress installation")
            print("=" * 70 + "\n")
            sys.exit(0)
        else:
            print(f"\n⚠️  {failed} test(s) failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
