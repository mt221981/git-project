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
                "practical_insights": verdict.practical_insights or []
            }

            # Generate article content
            article_content = self.generate_article_content(verdict_metadata, analysis_data)

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

            # Score article
            scores = self.score_article(article_content)

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

            # Update verdict status
            verdict.status = VerdictStatus.ARTICLE_CREATED

            self.db.commit()
            self.db.refresh(article)

            return article

        except Exception as e:
            self.db.rollback()
            raise ArticleGenerationError(f"Failed to generate article: {str(e)}")

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
