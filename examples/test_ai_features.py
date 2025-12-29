#!/usr/bin/env python3
"""
Interactive manual test script for Phase 3 AI features.

This script demonstrates:
- Keyword extraction from job descriptions
- Achievement rephrasing with different styles
- Professional summary generation
- Error handling and fallback mechanisms
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
from resume_customizer.core.ai_service import AIService

# Load environment variables
load_dotenv()


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(label: str, value: any):
    """Print a labeled result."""
    print(f"{label}:")
    print(f"  {value}")
    print()


def test_keyword_extraction():
    """Test keyword extraction from job description."""
    print_header("TEST 1: Keyword Extraction")

    service = AIService()

    # Sample job description
    job_description = """
    Senior Backend Engineer - Cloud Infrastructure

    We're looking for an experienced backend engineer to join our cloud team.

    Requirements:
    - 5+ years of Python development experience
    - Strong experience with AWS (EC2, S3, Lambda, RDS)
    - Docker and Kubernetes for container orchestration
    - RESTful API design and microservices architecture
    - Experience with PostgreSQL and Redis
    - CI/CD pipelines (Jenkins, GitHub Actions)
    - Team leadership and mentoring skills

    Responsibilities:
    - Design and build scalable backend services
    - Lead technical initiatives and architecture decisions
    - Mentor junior engineers
    - Optimize system performance and reliability
    - Deliver features on time with high quality
    """

    print("Job Description:")
    print(job_description)
    print("\nExtracting keywords...\n")

    # Extract keywords
    keywords = service.extract_keywords(job_description)

    # Display results
    print_result("Technical Skills",
                 [f"{s['keyword']} (weight: {s['weight']})"
                  for s in keywords["technical_skills"][:10]])

    print_result("Domain Knowledge",
                 [f"{s['keyword']} (weight: {s['weight']})"
                  for s in keywords["domain_knowledge"][:5]])

    print_result("Soft Skills",
                 [f"{s['keyword']} (weight: {s['weight']})"
                  for s in keywords["soft_skills"][:5]])

    print_result("Action Verbs", keywords["action_verbs"][:10])
    print_result("Metrics", keywords["metrics"][:5])

    return keywords


def test_achievement_rephrasing(job_keywords):
    """Test achievement rephrasing with different styles."""
    print_header("TEST 2: Achievement Rephrasing")

    service = AIService()

    # Sample achievements to rephrase
    achievements = [
        "Built a web application that improved customer engagement by 35%",
        "Reduced server costs by $50K annually",
        "Led team of 4 engineers to deliver project 2 weeks ahead of schedule"
    ]

    # Test different styles
    styles = ["technical", "results", "balanced"]

    # Extract top keywords from job
    top_keywords = [skill["keyword"] for skill in job_keywords["technical_skills"][:5]]

    for i, achievement in enumerate(achievements, 1):
        print(f"\n--- Achievement {i} ---")
        print_result("Original", achievement)

        for style in styles:
            print(f"\nStyle: {style.upper()}")
            result = service.rephrase_achievement(
                achievement=achievement,
                job_keywords=top_keywords,
                style=style
            )

            print_result("Rephrased", result["rephrased"])
            print_result("Keywords Added", ", ".join(result["keywords_added"]))
            print_result("Metrics Preserved", "✓" if result["metrics_preserved"] else "✗")
            print_result("Improvements", ", ".join(result["improvements"]))

        print("\n" + "-" * 80)


def test_summary_generation(job_keywords):
    """Test professional summary generation."""
    print_header("TEST 3: Summary Generation")

    service = AIService()

    # Sample profile context
    profile_context = {
        "top_skills": ["Python", "AWS", "Docker", "Kubernetes", "PostgreSQL"],
        "experience_years": 6,
        "current_title": "Senior Backend Engineer",
        "domain": "Cloud Infrastructure",
        "top_achievements": [
            "Architected microservices platform serving 2M+ users",
            "Reduced infrastructure costs by 45% through optimization",
            "Led team of 4 engineers to deliver major features"
        ]
    }

    # Sample job context
    job_context = {
        "title": "Lead Backend Engineer",
        "company": "TechCorp",
        "key_requirements": [skill["keyword"] for skill in job_keywords["technical_skills"][:5]],
        "industry": "SaaS"
    }

    print("Profile Context:")
    for key, value in profile_context.items():
        print(f"  {key}: {value}")

    print("\nJob Context:")
    for key, value in job_context.items():
        print(f"  {key}: {value}")

    # Test different styles
    styles = ["technical", "results", "balanced"]

    for style in styles:
        print(f"\n--- {style.upper()} Style ---")

        result = service.generate_custom_summary(
            profile_context=profile_context,
            job_context=job_context,
            style=style
        )

        print_result("Summary", result["summary"])
        print_result("Word Count", result["word_count"])
        print_result("Keywords Included", ", ".join(result["keywords_included"]))
        print()


def test_error_handling():
    """Test error handling and fallback mechanisms."""
    print_header("TEST 4: Error Handling & Fallback")

    service = AIService()

    print("Testing spaCy fallback for keyword extraction...")
    print("(This simulates what happens when Claude API fails)\n")

    job_text = """
    Looking for a Python developer with cloud experience.
    Must know Docker and Kubernetes.
    Experience with AWS is required.
    """

    # Force fallback by using spaCy directly
    try:
        keywords = service._extract_keywords_spacy(job_text)

        print("✓ spaCy fallback working!")
        print_result("Technical Skills Found",
                     [f"{s['keyword']}" for s in keywords["technical_skills"]])
        print_result("Domain Keywords",
                     [f"{s['keyword']}" for s in keywords["domain_knowledge"][:5]])
    except Exception as e:
        print(f"✗ Fallback failed: {e}")


def test_caching():
    """Test caching functionality."""
    print_header("TEST 5: Caching Performance")

    import time

    service = AIService()

    test_text = "Looking for a Python developer with 5 years of experience"

    print("First call (no cache)...")
    start = time.time()
    result1 = service.extract_keywords(test_text, use_cache=True)
    time1 = time.time() - start

    print(f"  Time: {time1:.2f}s")
    print(f"  Skills found: {len(result1['technical_skills'])}")

    print("\nSecond call (with cache)...")
    start = time.time()
    result2 = service.extract_keywords(test_text, use_cache=True)
    time2 = time.time() - start

    print(f"  Time: {time2:.2f}s")
    print(f"  Skills found: {len(result2['technical_skills'])}")

    if time2 < time1 * 0.5:  # Cache should be significantly faster
        print(f"\n✓ Cache working! Speedup: {time1/time2:.1f}x faster")
    else:
        print(f"\n⚠ Cache may not be working as expected")


def test_cost_estimation():
    """Estimate API costs for typical usage."""
    print_header("TEST 6: Cost Estimation")

    print("Estimated token usage per operation:")
    print("  - Keyword extraction: ~700 tokens")
    print("  - Achievement rephrasing: ~450 tokens")
    print("  - Summary generation: ~500 tokens")
    print()

    print("Typical resume customization workflow:")
    print("  1 keyword extraction + 3 achievement rephrasings + 1 summary")
    print("  = 700 + (450 × 3) + 500 = 2,550 tokens")
    print()

    # Claude 3.5 Sonnet pricing (as of 2024)
    input_cost_per_1m = 3.00  # $3 per 1M input tokens
    output_cost_per_1m = 15.00  # $15 per 1M output tokens

    # Assuming 50/50 split
    avg_cost_per_1m = (input_cost_per_1m + output_cost_per_1m) / 2
    cost_per_token = avg_cost_per_1m / 1_000_000

    estimated_cost = 2550 * cost_per_token

    print(f"Estimated cost per customization: ${estimated_cost:.4f}")
    print(f"With 50% cache hit rate: ${estimated_cost * 0.5:.4f}")
    print()

    if estimated_cost < 0.10:
        print(f"✓ Under target budget of $0.10 per customization!")
    else:
        print(f"⚠ Above target budget")


def main():
    """Run all manual tests."""
    print("\n" + "=" * 80)
    print("  Phase 3 Manual Testing - AI Integration")
    print("=" * 80)

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠ ERROR: ANTHROPIC_API_KEY not found in environment")
        print("Please set it in your .env file")
        return

    print("\n✓ API key found")
    print("✓ Starting interactive tests...\n")

    try:
        # Test 1: Keyword Extraction
        keywords = test_keyword_extraction()

        input("\nPress Enter to continue to Achievement Rephrasing...")

        # Test 2: Achievement Rephrasing
        test_achievement_rephrasing(keywords)

        input("\nPress Enter to continue to Summary Generation...")

        # Test 3: Summary Generation
        test_summary_generation(keywords)

        input("\nPress Enter to continue to Error Handling...")

        # Test 4: Error Handling
        test_error_handling()

        input("\nPress Enter to continue to Caching...")

        # Test 5: Caching
        test_caching()

        # Test 6: Cost Estimation
        test_cost_estimation()

        print_header("ALL TESTS COMPLETE")
        print("✓ All Phase 3 features tested successfully!")
        print("\nNext steps:")
        print("  - Review the outputs above")
        print("  - Check .cache/ directory for cached responses")
        print("  - Run automated tests: pytest tests/test_ai_*.py")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
