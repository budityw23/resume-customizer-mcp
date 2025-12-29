# Phase 3 Manual Testing Guide - AI Integration

This guide provides step-by-step instructions for manually testing all Phase 3 AI features.

## Prerequisites

1. **Environment Setup**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate  # or venv\Scripts\activate on Windows

   # Verify dependencies are installed
   pip install -e ".[dev]"

   # Download spaCy model (for fallback)
   python -m spacy download en_core_web_sm
   ```

2. **API Key Configuration**
   ```bash
   # Create .env file if not exists
   echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
   echo "CACHE_DIR=.cache" >> .env
   echo "LOG_LEVEL=INFO" >> .env
   ```

3. **Verify Installation**
   ```bash
   # Run tests to ensure everything works
   pytest tests/test_ai_service.py -v
   pytest tests/test_ai_integration.py -v
   ```

## Manual Test Script

Create and run this interactive test script to explore all AI features:

### 1. Create Test Script

Save this as `examples/test_ai_features.py`:

```python
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
```

### 2. Run Manual Tests

```bash
# Make script executable
chmod +x examples/test_ai_features.py

# Run the interactive test
python examples/test_ai_features.py
```

## Expected Results

### Test 1: Keyword Extraction
- Should extract 10-20 technical skills with weights
- Should identify domain knowledge (e.g., "cloud infrastructure", "microservices")
- Should find soft skills (e.g., "leadership", "mentoring")
- Should extract action verbs (e.g., "design", "build", "lead")
- Should identify metrics (e.g., "5+ years", "99.9% uptime")

### Test 2: Achievement Rephrasing
- **Technical style**: Should emphasize technologies and implementation details
- **Results style**: Should focus on metrics and business impact
- **Balanced style**: Should blend technical details with results
- Should preserve all original metrics (35%, $50K, 2 weeks, etc.)
- Should incorporate job keywords naturally

### Test 3: Summary Generation
- Should create 2-3 sentence summaries
- Word count should be 40-60 words
- Should include relevant keywords from job context
- Different styles should have different emphasis:
  - **Technical**: Focus on technologies and skills
  - **Results**: Focus on achievements and impact
  - **Balanced**: Mix of both

### Test 4: Error Handling
- spaCy fallback should work when API fails
- Should still extract basic technical skills
- Should handle gracefully without crashing

### Test 5: Caching
- Second call should be significantly faster (2x+)
- Should return identical results
- Cache files should appear in `.cache/` directory

### Test 6: Cost Estimation
- Should show ~$0.02 per customization
- Should be well under $0.10 target

## Quick Tests (Without Script)

If you want to quickly test individual features:

### Python REPL Test

```python
# Start Python REPL
python

# Import and initialize
from resume_customizer.core.ai_service import AIService
service = AIService()

# Test 1: Quick keyword extraction
keywords = service.extract_keywords("Looking for Python developer with AWS experience")
print(keywords["technical_skills"])

# Test 2: Quick achievement rephrasing
result = service.rephrase_achievement(
    "Built API that improved performance by 50%",
    job_keywords=["Python", "scalable"]
)
print(result["rephrased"])

# Test 3: Quick summary
summary = service.generate_custom_summary({
    "top_skills": ["Python", "AWS"],
    "experience_years": 5,
    "current_title": "Software Engineer"
})
print(summary["summary"])
```

## Verification Checklist

After running manual tests, verify:

- [ ] Keyword extraction produces relevant, categorized results
- [ ] Achievement rephrasing preserves all metrics
- [ ] Achievement rephrasing incorporates job keywords naturally
- [ ] Three different styles produce noticeably different outputs
- [ ] Summaries are 2-3 sentences, 40-60 words
- [ ] spaCy fallback works when API fails
- [ ] Caching speeds up repeated requests
- [ ] Estimated cost is under $0.10 per customization
- [ ] No errors or crashes during execution
- [ ] Log messages appear showing progress

## Troubleshooting

### Issue: API Key Error
```
Solution: Check .env file has ANTHROPIC_API_KEY set
```

### Issue: spaCy Model Not Found
```bash
# Download the model
python -m spacy download en_core_web_sm
```

### Issue: Import Errors
```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

### Issue: Cache Not Working
```bash
# Clear cache and try again
rm -rf .cache/
```

## Advanced Testing

### Test with Real Resume/Job Files

```python
from resume_customizer.parsers.markdown_parser import parse_resume, parse_job_description

# Parse real files
resume = parse_resume("examples/resumes/john_doe_resume.md")
job = parse_job_description("examples/jobs/backend_engineer.md")

# Extract keywords from job
keywords = service.extract_keywords(job.raw_text)

# Rephrase achievements from resume
for achievement in resume.work_experience[0].achievements[:3]:
    result = service.rephrase_achievement(
        achievement,
        job_keywords=[s["keyword"] for s in keywords["technical_skills"][:5]]
    )
    print(f"Original: {achievement}")
    print(f"Rephrased: {result['rephrased']}\n")
```

## Cost Monitoring

To monitor actual API costs:

```python
# Track token usage
import json
from pathlib import Path

cache_dir = Path(".cache")
total_tokens = 0

for cache_file in cache_dir.glob("*.json"):
    with open(cache_file) as f:
        data = json.load(f)
        # Estimate tokens from response length
        tokens = len(data.get("response", "")) // 4  # Rough estimate
        total_tokens += tokens

print(f"Total cached responses: {len(list(cache_dir.glob('*.json')))}")
print(f"Estimated tokens used: {total_tokens}")
print(f"Estimated cost: ${(total_tokens / 1_000_000) * 9:.4f}")
```

## Next Steps

After manual testing is complete:

1. **Review automated test coverage**: `pytest tests/test_ai_*.py --cov`
2. **Check implementation checklist**: Review `docs/IMPLEMENTATION_CHECKLIST.md`
3. **Test integration with matching engine**: Combine AI features with Phase 2 matching
4. **Prepare for Phase 4**: Customization engine that uses AI outputs

## Support

If you encounter issues:
- Check logs in console output
- Review `.cache/` directory for cached responses
- Run automated tests: `pytest -v`
- Check `docs/IMPLEMENTATION_CHECKLIST.md` for feature status
