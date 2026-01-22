"""Article generation service using Claude API."""

import json
import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from slugify import slugify

from app.models.verdict import Verdict, VerdictStatus
from app.models.article import Article, PublishStatus
from app.services.article_generator import ArticleGenerator, ArticleGeneratorError as GeneratorError
from app.services.prompts import SCHEMA_GENERATION_PROMPT


class ArticleGenerationError(Exception):
    """Exception raised when article generation fails."""
    pass


class ArticleService:
    """
    Service for generating SEO-optimized articles from analyzed verdicts.

    Handles:
    - Article content generation
    - SEO optimization
    - Schema markup generation
    - Quality scoring
    """

    def __init__(self, db: Session, generator: Optional[ArticleGenerator] = None):
        """
        Initialize article service.

        Args:
            db: Database session
            generator: Optional ArticleGenerator instance (creates default if not provided)
        """
        self.db = db
        self.generator = generator or ArticleGenerator()

    def generate_article_content(
        self,
        verdict_metadata: Dict[str, Any],
        analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate article content from verdict analysis.

        Args:
            verdict_metadata: Verdict metadata (case number, court, etc.)
            analysis_data: Analysis results (facts, legal questions, etc.)

        Returns:
            Dictionary with article content

        Raises:
            ArticleGenerationError: If generation fails
        """
        try:
            # Combine verdict metadata and analysis data for the generator
            verdict_data = {**verdict_metadata, **analysis_data}
            # Use new ArticleGenerator service
            result = self.generator.generate(verdict_data)
            return result

        except GeneratorError as e:
            raise ArticleGenerationError(f"Article generation failed: {str(e)}")
        except Exception as e:
            raise ArticleGenerationError(f"Article generation failed: {str(e)}")

    def calculate_word_count(self, html_content: str) -> int:
        """
        Calculate word count from HTML content.

        Args:
            html_content: HTML content string

        Returns:
            Word count
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Count words (split by whitespace)
        words = text.split()
        return len(words)

    def calculate_reading_time(self, word_count: int) -> int:
        """
        Calculate estimated reading time in minutes.

        Args:
            word_count: Number of words

        Returns:
            Reading time in minutes (assumes 200 words per minute)
        """
        return max(1, round(word_count / 200))

    def score_article(self, article_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score article quality.

        Args:
            article_content: Article content dictionary

        Returns:
            Scoring results with:
            {
                "content_score": int,
                "seo_score": int,
                "readability_score": int,
                "eeat_score": int,
                "overall_score": int
            }

        Raises:
            ArticleGenerationError: If scoring fails
        """
        try:
            # Log what we're sending to calculate_scores
            print(f"[ArticleService] score_article called with keys: {list(article_content.keys())}")
            print(f"[ArticleService] Has faq_items: {'faq_items' in article_content}")
            print(f"[ArticleService] Has title: {'title' in article_content}")

            # Use ArticleGenerator's calculate_scores method
            scores = self.generator.calculate_scores(article_content)

            print(f"[ArticleService] Scores received: content={scores.get('content_score')}, overall={scores.get('overall_score')}")
            return scores

        except Exception as e:
            # Log the exception
            import traceback
            print(f"[ArticleService] EXCEPTION in score_article:")
            print(traceback.format_exc())

            # Return default scores if scoring fails
            return {
                "content_score": 70,
                "seo_score": 70,
                "readability_score": 70,
                "eeat_score": 70,
                "overall_score": 70
            }

    def generate_schema_markup(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Schema.org JSON-LD markup for the article.

        Args:
            article_data: Article data

        Returns:
            Schema markup dictionary

        Raises:
            ArticleGenerationError: If schema generation fails
        """
        article_str = json.dumps(article_data, ensure_ascii=False, indent=2)

        prompt = SCHEMA_GENERATION_PROMPT.format(article_data=article_str)

        try:
            response = self.generator.client.create_structured_message(
                prompt=prompt,
                max_tokens=2000
            )

            # Parse response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]

            return json.loads(json_str)

        except Exception as e:
            # Return minimal schema if generation fails
            return {
                "schema_article": None,
                "schema_faq": None
            }

    def generate_article_from_verdict(self, verdict_id: int) -> Article:
        """
        Generate a complete article from an analyzed verdict.

        Args:
            verdict_id: ID of verdict to generate article from

        Returns:
            Created article

        Raises:
            ValueError: If verdict not found or not analyzed
            ArticleGenerationError: If generation fails
        """
        verdict = self.db.query(Verdict).filter(Verdict.id == verdict_id).first()

        if not verdict:
            raise ValueError(f"Verdict with ID {verdict_id} not found")

        if verdict.status not in [VerdictStatus.ANALYZED, VerdictStatus.ARTICLE_CREATED]:
            raise ValueError(
                f"Verdict must be analyzed before article generation. "
                f"Current status: {verdict.status}"
            )

        # Check if article already exists for this verdict
        existing_article = self.db.query(Article).filter(
            Article.verdict_id == verdict_id
        ).first()

        if existing_article:
            raise ValueError(
                f"Article already exists for this verdict (ID: {existing_article.id}). "
                "Use update or regenerate instead."
            )

        try:
            # Prepare verdict metadata
            verdict_metadata = {
                "case_number": verdict.case_number,
                "court_name": verdict.court_name,
                "court_level": verdict.court_level.value if verdict.court_level else None,
                "judge_name": verdict.judge_name,
                "verdict_date": str(verdict.verdict_date) if verdict.verdict_date else None,
                "legal_area": verdict.legal_area,
                "legal_sub_area": verdict.legal_sub_area
            }

            # Prepare analysis data
            analysis_data = {
                "key_facts": verdict.key_facts or [],
                "legal_questions": verdict.legal_questions or [],
                "legal_principles": verdict.legal_principles or [],
                "compensation_amount": verdict.compensation_amount,
                "compensation_breakdown": verdict.compensation_breakdown,
                "relevant_laws": verdict.relevant_laws or [],
                "precedents_cited": verdict.precedents_cited or [],
                "practical_insights": verdict.practical_insights or [],
                # Add actual verdict content for the prompt
                "verdict_text": (verdict.anonymized_text or verdict.cleaned_text or "")[:8000],
                "summary": self._generate_summary(verdict)
            }

            # Quality control retry loop
            MAX_GENERATION_ATTEMPTS = 3  # Allow retries for quality improvement
            MIN_SCORE_THRESHOLD = 80  # High quality threshold - all metrics must reach 80+
            previous_scores = None

            # Set initial progress for article generation - start from 60%
            verdict.status = VerdictStatus.ARTICLE_CREATING
            verdict.processing_progress = 60
            verdict.processing_message = "מתחיל יצירת מאמר..."
            self.db.commit()

            for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
                # Calculate progress: 60 + (attempt-1)*15 = 60, 75
                progress = 60 + (attempt - 1) * 15
                verdict.processing_progress = progress
                verdict.processing_message = f"יוצר מאמר ({attempt}/{MAX_GENERATION_ATTEMPTS}) - שולח ל-AI..."
                self.db.commit()

                print(f"[ArticleService] Article generation attempt {attempt}/{MAX_GENERATION_ATTEMPTS}")

                # Build improvement hints from previous attempt
                improvement_hints = None
                if attempt > 1 and previous_scores:
                    improvement_hints = self._build_improvement_hints(previous_scores)
                    print(f"[ArticleService] Improvement hints:\n{improvement_hints}")
                    verdict.processing_message = f"יוצר מאמר ({attempt}/{MAX_GENERATION_ATTEMPTS}) - משפר לפי משוב..."
                    self.db.commit()

                # Generate article content (pass hints to generator)
                verdict.processing_message = f"יוצר מאמר ({attempt}/{MAX_GENERATION_ATTEMPTS}) - מחכה לתשובה מ-AI (1-3 דקות)..."
                self.db.commit()

                article_content = self.generator.generate(
                    {**verdict_metadata, **analysis_data},
                    improvement_hints=improvement_hints
                )

                verdict.processing_message = f"יוצר מאמר ({attempt}/{MAX_GENERATION_ATTEMPTS}) - בודק איכות..."
                verdict.processing_progress = progress + 3
                self.db.commit()

                print(f"[ArticleService] Article generated, content_html length: {len(article_content.get('content_html', ''))}")

                # Enhance with SEO links
                from app.services.link_enhancement import LinkEnhancementService
                link_service = LinkEnhancementService()

                enhanced_html = link_service.enhance_with_links(
                    content_html=article_content["content_html"],
                    focus_keyword=article_content.get("focus_keyword"),
                    secondary_keywords=article_content.get("secondary_keywords"),
                    max_internal=5,
                    max_external=3
                )

                article_content["content_html"] = enhanced_html

                # Log link stats
                link_stats = link_service.get_stats(enhanced_html)
                print(f"[LinkEnhancement] Added {link_stats['internal_links']} internal, {link_stats['external_links']} external links")

                # Score article
                scores = self.score_article(article_content)

                # Check all metrics against uniform threshold
                content_ok = scores["content_score"] >= MIN_SCORE_THRESHOLD
                seo_ok = scores["seo_score"] >= MIN_SCORE_THRESHOLD
                readability_ok = scores["readability_score"] >= MIN_SCORE_THRESHOLD
                eeat_ok = scores["eeat_score"] >= MIN_SCORE_THRESHOLD

                all_passed = content_ok and seo_ok and readability_ok and eeat_ok
                min_score = min(scores["content_score"], scores["seo_score"], scores["readability_score"], scores["eeat_score"])

                print(f"[ArticleService] Scores - Content: {scores['content_score']}, SEO: {scores['seo_score']}, Readability: {scores['readability_score']}, E-E-A-T: {scores['eeat_score']}")
                print(f"[ArticleService] Quality threshold (all metrics): {MIN_SCORE_THRESHOLD}")

                # Check if quality threshold met
                if all_passed:
                    print(f"[ArticleService] Quality thresholds met! All scores passed.")
                    verdict.processing_progress = 95
                    verdict.processing_message = f"מאמר עבר את כל בדיקות האיכות"
                    self.db.commit()
                    # Break out of retry loop - continue to save article
                    break

                # Not good enough - prepare for retry or fail
                if attempt < MAX_GENERATION_ATTEMPTS:
                    failed_metrics = []
                    if not content_ok: failed_metrics.append(f"Content({scores['content_score']})")
                    if not seo_ok: failed_metrics.append(f"SEO({scores['seo_score']})")
                    if not readability_ok: failed_metrics.append(f"Readability({scores['readability_score']})")
                    if not eeat_ok: failed_metrics.append(f"E-E-A-T({scores['eeat_score']})")

                    print(f"[ArticleService] Quality threshold not met. Failed: {', '.join(failed_metrics)}. Retrying...")
                    verdict.processing_message = f"מנסה שוב - נכשלו: {', '.join(failed_metrics)}"
                    self.db.commit()
                    previous_scores = scores
                    # Loop continues to next attempt
                else:
                    # Failed after max attempts
                    print(f"[ArticleService] Failed to meet quality threshold after {MAX_GENERATION_ATTEMPTS} attempts")
                    verdict.status = VerdictStatus.FAILED
                    verdict.processing_progress = 60
                    verdict.processing_message = f"נכשל אחרי {MAX_GENERATION_ATTEMPTS} ניסיונות"
                    verdict.review_notes = f"Article quality below threshold after {MAX_GENERATION_ATTEMPTS} attempts. Last scores: Content={scores['content_score']}, SEO={scores['seo_score']}, Readability={scores['readability_score']}, E-E-A-T={scores['eeat_score']}"
                    self.db.commit()
                    raise ArticleGenerationError(verdict.review_notes)

            # Calculate metrics
            word_count = self.calculate_word_count(article_content["content_html"])
            reading_time = self.calculate_reading_time(word_count)

            # Generate slug from title with uniqueness check
            base_slug = slugify(article_content["title"], max_length=180)
            slug = base_slug
            counter = 1
            while self.db.query(Article).filter(Article.slug == slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Generate schema markup
            schema_data = self.generate_schema_markup({
                **article_content,
                **verdict_metadata
            })

            # Create article record
            article = Article(
                verdict_id=verdict_id,
                title=article_content["title"][:70],
                slug=slug,
                meta_title=article_content.get("meta_title", article_content["title"])[:70],
                meta_description=article_content.get("meta_description", "")[:160],
                content_html=article_content["content_html"],
                excerpt=article_content.get("excerpt", ""),
                focus_keyword=article_content.get("focus_keyword", ""),
                secondary_keywords=article_content.get("secondary_keywords", []),
                long_tail_keywords=article_content.get("long_tail_keywords", []),
                word_count=word_count,
                reading_time_minutes=reading_time,
                faq_items=article_content.get("faq_items", []),
                common_mistakes=article_content.get("common_mistakes", []),
                schema_article=schema_data.get("schema_article"),
                schema_faq=schema_data.get("schema_faq"),
                internal_links=article_content.get("internal_links", []),
                external_links=article_content.get("external_links", []),
                category_primary=article_content.get("category_primary", verdict.legal_area),
                categories_secondary=article_content.get("categories_secondary", []),
                tags=article_content.get("tags", []),
                featured_image_prompt=article_content.get("featured_image_prompt", ""),
                featured_image_alt=article_content.get("featured_image_alt", ""),
                content_score=scores.get("content_score", 0),
                seo_score=scores.get("seo_score", 0),
                readability_score=scores.get("readability_score", 0),
                eeat_score=scores.get("eeat_score", 0),
                overall_score=scores.get("overall_score", 0),
                quality_issues=scores.get("quality_issues", []),
                publish_status=PublishStatus.DRAFT
            )

            self.db.add(article)
            self.db.commit()
            self.db.refresh(article)

            # Fetch featured image from Pexels
            verdict.processing_progress = 92
            verdict.processing_message = "מחפש תמונה ראשית מתאימה..."
            self.db.commit()

            try:
                self._fetch_featured_image(article, verdict.legal_area)
                self.db.commit()
            except Exception as e:
                print(f"[ArticleService] Featured image fetch failed: {e}")
                # Continue without image - not critical

            # Update verdict status
            verdict.status = VerdictStatus.ARTICLE_CREATED
            verdict.processing_progress = 95
            verdict.processing_message = "מאמר נוצר בהצלחה, מתכונן לפרסום..."

            self.db.commit()
            self.db.refresh(article)

            # Auto-publish to WordPress if quality threshold met
            # First, check if WordPress is configured
            from app.models.wordpress_site import WordPressSite

            default_site = self.db.query(WordPressSite).filter(
                WordPressSite.is_active == True
            ).first()

            if default_site:
                # WordPress site exists - try to publish
                try:
                    verdict.processing_message = "מפרסם אוטומטית ל-WordPress..."
                    self.db.commit()

                    # Import WordPress service
                    from app.services.wordpress_service import WordPressService
                    wp_service = WordPressService(self.db)

                    # Publish to WordPress
                    updated_article = wp_service.publish_article(
                        article_id=article.id,
                        site_id=default_site.id,
                        status="publish"  # Publish immediately
                    )

                    # The publish_article method already updates article.wordpress_post_id
                    # Just update verdict status
                    verdict.status = VerdictStatus.PUBLISHED
                    verdict.processing_progress = 100
                    verdict.processing_message = f"פורסם בהצלחה ל-WordPress (Post ID: {updated_article.wordpress_post_id})"
                    self.db.commit()

                    print(f"[ArticleService] Auto-published to WordPress: Post ID {updated_article.wordpress_post_id}")

                except Exception as e:
                    # If WordPress publish fails, keep article as ARTICLE_CREATED (manual publish option)
                    import traceback
                    print(f"[ArticleService] Auto-publish failed: {str(e)}")
                    print(traceback.format_exc())

                    verdict.status = VerdictStatus.ARTICLE_CREATED
                    verdict.processing_progress = 100
                    verdict.processing_message = f"מאמר נוצר בהצלחה - פרסום ל-WordPress נכשל (יש לבדוק הגדרות)"
                    self.db.commit()
            else:
                # No WordPress site configured - save as ARTICLE_CREATED
                print("[ArticleService] No active WordPress site - skipping auto-publish")
                verdict.status = VerdictStatus.ARTICLE_CREATED
                verdict.processing_progress = 100
                verdict.processing_message = "מאמר נוצר בהצלחה - אין אתר WordPress מוגדר לפרסום אוטומטי"
                self.db.commit()

            return article

        except Exception as e:
            self.db.rollback()
            raise ArticleGenerationError(f"Failed to generate article: {str(e)}")

    def _generate_summary(self, verdict) -> str:
        """Generate a summary from verdict analysis data."""
        parts = []

        if verdict.key_facts:
            parts.append("עובדות: " + "; ".join(str(f) for f in verdict.key_facts[:3]))

        if verdict.legal_questions:
            parts.append("שאלות: " + "; ".join(str(q) for q in verdict.legal_questions[:2]))

        if verdict.practical_insights:
            parts.append("תובנות: " + "; ".join(str(i) for i in verdict.practical_insights[:2]))

        if verdict.compensation_amount:
            parts.append(f"פיצוי: {verdict.compensation_amount:,.0f} ש\"ח")

        return " | ".join(parts) if parts else ""

    def _fetch_featured_image(self, article: Article, legal_area: str = None) -> None:
        """
        Fetch featured image from Pexels based on article prompt.

        Args:
            article: Article to update with image
            legal_area: Legal area for category-specific search
        """
        import os
        if not os.getenv("PEXELS_API_KEY"):
            print("[ArticleService] PEXELS_API_KEY not set - skipping featured image")
            return

        # Generate default prompt if none provided
        prompt = article.featured_image_prompt
        if not prompt:
            prompt = self._get_default_image_prompt(legal_area, article.title)
            article.featured_image_prompt = prompt
            print(f"[ArticleService] Generated default image prompt: {prompt[:50]}...")

        try:
            from app.services.image_service import PexelsImageService, ImageServiceError

            image_service = PexelsImageService()

            image_url, credit, metadata = image_service.get_featured_image(
                prompt=prompt,
                legal_area=legal_area,
                preferred_size="large"
            )

            if image_url:
                article.featured_image_url = image_url
                article.featured_image_credit = credit
                print(f"[ArticleService] Featured image found: {image_url[:60]}...")
            else:
                print("[ArticleService] No suitable image found")

        except Exception as e:
            print(f"[ArticleService] Image fetch error: {e}")

    def _get_default_image_prompt(self, legal_area: str, title: str) -> str:
        """Generate a default image prompt based on legal area and title.

        IMPORTANT: This system handles ONLY tort law (נזיקין) and insurance (ביטוח).
        All prompts should relate to these areas - NOT family law, divorce, criminal, etc.
        """
        prompts = {
            # Core tort/insurance
            "nziqin": "law office gavel scales justice court legal compensation",
            "bituah": "insurance policy document claim settlement legal",
            "pizuyim": "compensation settlement court gavel legal money",
            # Accidents
            "taavura": "car accident damage vehicle traffic collision",
            "teuna": "car accident damage vehicle road crash",
            "teunat_avoda": "workplace safety equipment injury protection",
            # Medical
            "refui": "stethoscope medical records hospital healthcare",
            "rashlanut_refuit": "medical records hospital doctor stethoscope",
            # Property
            "rekhush": "property damage insurance home building",
            "nzqei_rekhush": "property damage flood fire house insurance",
            # General legal (still tort themed)
            "mishpat_ezrahi": "courtroom judge gavel legal documents justice",
        }

        # Try to match legal area
        if legal_area:
            legal_lower = legal_area.lower()
            if "nzq" in legal_lower or "nzikin" in legal_lower or "נזיקין" in legal_area:
                return prompts["nziqin"]
            if "bituah" in legal_lower or "ביטוח" in legal_area:
                return prompts["bituah"]
            if "pizuy" in legal_lower or "פיצוי" in legal_area:
                return prompts["pizuyim"]
            if "refui" in legal_lower or "רפואי" in legal_area or "rashlanut" in legal_lower:
                return prompts["refui"]
            if "taavura" in legal_lower or "teuna" in legal_lower or "תאונה" in legal_area:
                return prompts["taavura"]
            if "rekhush" in legal_lower or "רכוש" in legal_area:
                return prompts["rekhush"]

        # Check title for hints (Hebrew)
        title_check = title.lower() if title else ""
        if "נזק" in title or "פיצוי" in title or "nzq" in title_check:
            return prompts["nziqin"]
        if "ביטוח" in title or "bituah" in title_check:
            return prompts["bituah"]
        if "תאונה" in title or "teuna" in title_check or "taavura" in title_check:
            return prompts["taavura"]
        if "רפואי" in title or "רשלנות" in title:
            return prompts["refui"]
        if "teuna" in title_lower:
            return prompts["taavura"]
        if "hashkaa" in title_lower or "hskaa" in title_lower:
            return "investment business finance money contract agreement"

        # Default legal image
        return "law office legal books gavel justice court attorney"

    def _build_improvement_hints(self, previous_scores: dict) -> str:
        """Build concise improvement hints based on previous scores."""
        hints = []

        if previous_scores["seo_score"] < 70:
            hints.append(f"SEO({previous_scores['seo_score']}): הוסף מילות מפתח 22+ פעמים, בכותרות ובפסקה ראשונה")

        if previous_scores["eeat_score"] < 70:
            hints.append(f"E-E-A-T({previous_scores['eeat_score']}): הוסף 8+ סעיפי חוק עם מספרים, ביטויים סמכותיים, מונחים משפטיים עם הסבר")

        if previous_scores["readability_score"] < 70:
            hints.append(f"קריאות({previous_scores['readability_score']}): קצר משפטים, הוסף רשימות")

        if previous_scores["content_score"] < 70:
            hints.append(f"תוכן({previous_scores['content_score']}): הוסף FAQ, סיכום, קריאה לפעולה")

        return " | ".join(hints) if hints else ""

    def get_article(self, article_id: int) -> Optional[Article]:
        """Get article by ID."""
        return self.db.query(Article).filter(Article.id == article_id).first()

    def list_articles(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[PublishStatus] = None
    ) -> tuple:
        """List articles with pagination."""
        query = self.db.query(Article)

        if status:
            query = query.filter(Article.publish_status == status)

        total = query.count()
        articles = query.order_by(Article.created_at.desc()).offset(skip).limit(limit).all()

        return articles, total

    def get_article_stats(self) -> Dict[str, Any]:
        """Get article statistics."""
        from sqlalchemy import func

        total = self.db.query(func.count(Article.id)).scalar()

        by_status = {}
        for status in PublishStatus:
            count = self.db.query(func.count(Article.id)).filter(
                Article.publish_status == status
            ).scalar()
            by_status[status.value] = count

        avg_scores = self.db.query(
            func.avg(Article.content_score),
            func.avg(Article.seo_score),
            func.avg(Article.readability_score),
            func.avg(Article.eeat_score),
            func.avg(Article.overall_score)
        ).first()

        return {
            "total": total,
            "by_status": by_status,
            "average_scores": {
                "content": round(avg_scores[0], 1) if avg_scores[0] else 0,
                "seo": round(avg_scores[1], 1) if avg_scores[1] else 0,
                "readability": round(avg_scores[2], 1) if avg_scores[2] else 0,
                "eeat": round(avg_scores[3], 1) if avg_scores[3] else 0,
                "overall": round(avg_scores[4], 1) if avg_scores[4] else 0
            }
        }
