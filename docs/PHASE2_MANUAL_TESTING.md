# Phase 2 Manual Testing Guide

This guide shows how to manually test the Phase 2 matching engine functionality.

## Prerequisites

1. Activate virtual environment:
```bash
cd "/home/budi/code/self-portfolio/resume customizer mcp server"
source venv/bin/activate
```

2. Ensure all dependencies are installed:
```bash
pip install -e .
```

## Option 1: Test via Python REPL

### Test 1: Skill Matching

```python
from resume_customizer.core.matcher import SkillMatcher
from resume_customizer.core.models import Skill

# Create skill matcher
matcher = SkillMatcher()

# Test exact matching
print("Test 1: Exact match")
print(matcher.match_skill("Python", "python"))  # Should be True

# Test synonym matching
print("\nTest 2: Synonym match")
print(matcher.match_skill("React.js", "react"))  # Should be True
print(matcher.match_skill("Python3", "python"))  # Should be True

# Test hierarchy matching
print("\nTest 3: Hierarchy match")
print(matcher.match_skill("Django", "Python"))  # Should be True (Django implies Python)
print(matcher.match_skill("React", "JavaScript"))  # Should be True (React implies JS)

# Test fuzzy matching
print("\nTest 4: Fuzzy match")
print(matcher.match_skill("Javascrpt", "JavaScript", threshold=80))  # Should be True (typo)

# Test skill list matching
print("\nTest 5: Match skills list")
user_skills = [
    Skill(name="Python", category="language", proficiency="expert"),
    Skill(name="Django", category="framework", proficiency="advanced"),
    Skill(name="PostgreSQL", category="database", proficiency="intermediate"),
]

required_skills = ["python", "django", "postgresql", "docker"]

matched, missing = matcher.match_skills(user_skills, required_skills)
print(f"Matched: {len(matched)} skills")
print(f"Missing: {missing}")  # Should show ['docker']

# Calculate match percentage
percentage = matcher.calculate_required_skills_match(user_skills, required_skills)
print(f"Match percentage: {percentage}%")  # Should be 75% (3 out of 4)
```

### Test 2: Achievement Ranking

```python
from resume_customizer.core.matcher import rank_achievements
from resume_customizer.core.models import Achievement, JobDescription, JobRequirements

# Create a job description
job = JobDescription(
    title="Python Developer",
    company="Tech Corp",
    description="Build web applications using Python and Django",
    responsibilities=[
        "Develop scalable web applications",
        "Write clean, maintainable code",
        "Deploy containerized applications"
    ],
    requirements=JobRequirements(
        required_skills=["python", "django", "docker"],
    )
)

# Create some achievements
achievements = [
    Achievement(text="Built scalable web applications using Python and Django, serving 1M+ users"),
    Achievement(text="Deployed containerized microservices using Docker and Kubernetes"),
    Achievement(text="Organized team building events and managed schedules"),
    Achievement(text="Improved system performance by 50% through code optimization"),
]

# Rank achievements
ranked = rank_achievements(achievements, job)

# Display results
print("Achievement Rankings:")
print("=" * 80)
for i, ranked_ach in enumerate(ranked, 1):
    print(f"\n{i}. Score: {ranked_ach.score:.1f}")
    print(f"   Text: {ranked_ach.achievement.text}")
    print(f"   Reasons: {', '.join(ranked_ach.reasons)}")
```

### Test 3: Match Scoring

```python
from resume_customizer.core.matcher import calculate_match_score
from resume_customizer.core.models import (
    ContactInfo, UserProfile, Experience, Achievement,
    Skill, Education, JobDescription, JobRequirements
)

# Create a user profile
profile = UserProfile(
    name="John Doe",
    contact=ContactInfo(email="john@example.com", phone="+1-555-1234"),
    summary="Experienced Python developer with 5 years building web applications",
    experiences=[
        Experience(
            company="Tech Corp",
            title="Senior Software Engineer",
            start_date="2020-01",
            end_date="Present",
            description="Build and maintain web applications for healthcare industry",
            achievements=[
                Achievement(text="Built scalable web applications using Python and Django"),
                Achievement(text="Improved system performance by 50%"),
                Achievement(text="Deployed containerized applications using Docker"),
            ]
        ),
        Experience(
            company="Startup Inc",
            title="Software Engineer",
            start_date="2018-01",
            end_date="2020-01",
            description="Developed REST APIs and microservices",
            achievements=[
                Achievement(text="Developed REST APIs using Flask"),
                Achievement(text="Wrote comprehensive unit tests"),
            ]
        ),
    ],
    skills=[
        Skill(name="Python", category="language", proficiency="expert", years=5),
        Skill(name="Django", category="framework", proficiency="advanced", years=4),
        Skill(name="Flask", category="framework", proficiency="intermediate", years=2),
        Skill(name="Docker", category="devops", proficiency="intermediate", years=3),
        Skill(name="PostgreSQL", category="database", proficiency="intermediate", years=4),
    ],
    education=[
        Education(
            degree="BS Computer Science",
            institution="State University",
            graduation_year="2018"
        )
    ]
)

# Create a job description
job = JobDescription(
    title="Senior Python Developer",
    company="Healthcare Tech",
    description="Build healthcare applications",
    responsibilities=[
        "Develop web applications using Python and Django",
        "Write clean, testable code",
        "Deploy applications to production",
    ],
    requirements=JobRequirements(
        required_skills=["python", "django", "postgresql", "docker"],
        preferred_skills=["kubernetes", "aws"],
        required_experience_years=4,
    )
)

# Calculate match score
result = calculate_match_score(profile, job)

# Display results
print("\n" + "=" * 80)
print("MATCH ANALYSIS RESULTS")
print("=" * 80)
print(f"\nOverall Score: {result.overall_score}%")
print(f"\nBreakdown:")
print(f"  - Technical Skills:  {result.breakdown.technical_skills_score:.1f}% (weight: 40%)")
print(f"  - Experience Level:  {result.breakdown.experience_score:.1f}% (weight: 25%)")
print(f"  - Domain Knowledge:  {result.breakdown.domain_score:.1f}% (weight: 20%)")
print(f"  - Keyword Coverage:  {result.breakdown.keyword_coverage_score:.1f}% (weight: 15%)")
print(f"  - TOTAL:             {result.breakdown.total_score:.1f}%")

print(f"\nMatched Skills: {len(result.matched_skills)}")
for match in result.matched_skills[:5]:
    print(f"  ✓ {match.skill} ({match.user_proficiency or 'N/A'})")

print(f"\nMissing Required Skills: {len(result.missing_required_skills)}")
for skill in result.missing_required_skills:
    print(f"  ✗ {skill}")

print(f"\nMissing Preferred Skills: {len(result.missing_preferred_skills)}")
for skill in result.missing_preferred_skills:
    print(f"  ○ {skill}")

print(f"\nSuggestions:")
for i, suggestion in enumerate(result.suggestions, 1):
    print(f"  {i}. {suggestion}")

print(f"\nTop 5 Achievements:")
for i, (achievement, score) in enumerate(result.ranked_achievements[:5], 1):
    print(f"  {i}. [{score:.1f}] {achievement.text}")

print("\n" + "=" * 80)
```

## Option 2: Test via MCP Handlers

### Test 4: Handler Integration Test

```python
from resume_customizer.mcp.handlers import (
    handle_load_user_profile,
    handle_load_job_description,
    handle_analyze_match,
    _session_state
)

# Note: You'll need valid resume and job files
# For testing, you can create simple markdown files

# Load a profile
print("Loading user profile...")
profile_result = handle_load_user_profile({
    "file_path": "examples/sample_resume.md"  # Create this file first
})
print(f"Status: {profile_result['status']}")
if profile_result['status'] == 'success':
    print(f"Profile ID: {profile_result['profile_id']}")
    print(f"Name: {profile_result['name']}")
    print(f"Skills: {profile_result['skills_count']}")
    print(f"Experiences: {profile_result['experiences_count']}")
else:
    print(f"Error: {profile_result['message']}")

# Load a job
print("\nLoading job description...")
job_result = handle_load_job_description({
    "file_path": "examples/sample_job.md"  # Create this file first
})
print(f"Status: {job_result['status']}")
if job_result['status'] == 'success':
    print(f"Job ID: {job_result['job_id']}")
    print(f"Title: {job_result['title']}")
    print(f"Company: {job_result['company']}")
else:
    print(f"Error: {job_result['message']}")

# Analyze match
if profile_result['status'] == 'success' and job_result['status'] == 'success':
    print("\nAnalyzing match...")
    match_result = handle_analyze_match({
        "profile_id": profile_result['profile_id'],
        "job_id": job_result['job_id'],
    })

    print(f"Status: {match_result['status']}")
    if match_result['status'] == 'success':
        print(f"\nMatch ID: {match_result['match_id']}")
        print(f"Overall Score: {match_result['overall_score']}%")
        print(f"\nBreakdown:")
        for component, score in match_result['breakdown'].items():
            print(f"  - {component}: {score}%")
        print(f"\nSuggestions:")
        for suggestion in match_result['suggestions']:
            print(f"  • {suggestion}")
    else:
        print(f"Error: {match_result['message']}")
```

## Option 3: Create Test Files and Run Interactive Test

### Step 1: Create Sample Resume File

Create `examples/test_resume.md`:

```markdown
# Jane Smith

## Contact Information
- **Email:** jane.smith@example.com
- **Phone:** +1-555-9876
- **Location:** San Francisco, CA, USA
- **LinkedIn:** linkedin.com/in/janesmith
- **GitHub:** github.com/janesmith

## Professional Summary

Senior Software Engineer with 6 years of experience building scalable web applications using Python and modern frameworks. Specialized in backend development, API design, and cloud infrastructure.

## Work Experience

### Senior Software Engineer at Tech Solutions Inc
**Jan 2021 - Present** | Remote | Remote

- Built and maintained microservices architecture serving 5M+ daily users
- Improved API response time by 60% through optimization and caching
- Deployed containerized applications using Docker and Kubernetes
- Mentored team of 3 junior developers

### Software Engineer at Digital Startup
**Jun 2018 - Dec 2020** | San Francisco, CA | Onsite

- Developed REST APIs using Python and Django
- Implemented automated testing achieving 90% code coverage
- Migrated monolithic application to microservices architecture
- Collaborated with product team on feature development

## Skills

### Programming Languages
- Python (Expert, 6 years)
- JavaScript (Intermediate, 4 years)
- SQL (Advanced, 5 years)

### Frameworks & Tools
- Django (Expert, 5 years)
- Flask (Advanced, 3 years)
- FastAPI (Intermediate, 2 years)
- Docker (Advanced, 4 years)
- Kubernetes (Intermediate, 2 years)

### Databases
- PostgreSQL (Advanced, 5 years)
- Redis (Intermediate, 3 years)
- MongoDB (Basic, 1 year)

### Cloud & DevOps
- AWS (Intermediate, 3 years)
- CI/CD (Advanced, 4 years)
- Git (Expert, 6 years)

## Education

### Bachelor of Science in Computer Science
Stanford University | 2014 - 2018
GPA: 3.8/4.0
```

### Step 2: Create Sample Job File

Create `examples/test_job.md`:

```markdown
# Senior Backend Engineer

**Company**: CloudScale Technologies
**Location**: Remote
**Type**: Full-time
**Experience Level**: Senior (5+ years)
**Salary Range**: $140,000 - $180,000

## About the Role

We're looking for an experienced Backend Engineer to join our platform team and help build the next generation of cloud-native applications.

## Responsibilities

- Design and develop scalable backend services using Python
- Build and maintain RESTful APIs and microservices
- Optimize application performance and database queries
- Implement automated testing and CI/CD pipelines
- Collaborate with frontend and DevOps teams
- Mentor junior engineers and conduct code reviews

## Required Qualifications

- 5+ years of professional software development experience
- Strong proficiency in Python and modern web frameworks
- Experience with microservices architecture
- Solid understanding of database design and optimization
- Experience with containerization and orchestration

### Required Skills
- Python
- Django
- PostgreSQL
- Docker
- Kubernetes
- REST APIs

### Preferred Skills
- AWS
- Redis
- FastAPI
- GraphQL
- Terraform

## About Us

CloudScale Technologies builds cloud infrastructure solutions for enterprises. We're a remote-first company with a strong engineering culture.
```

### Step 3: Run Interactive Test

```python
# Save this as test_phase2.py and run: python test_phase2.py

from resume_customizer.mcp.handlers import (
    handle_load_user_profile,
    handle_load_job_description,
    handle_analyze_match,
)

def test_phase2_complete_workflow():
    """Test the complete Phase 2 workflow."""

    print("=" * 80)
    print("PHASE 2 MANUAL TEST - COMPLETE WORKFLOW")
    print("=" * 80)

    # Step 1: Load profile
    print("\n[1/3] Loading user profile...")
    profile_result = handle_load_user_profile({
        "file_path": "examples/test_resume.md"
    })

    if profile_result['status'] != 'success':
        print(f"❌ Failed to load profile: {profile_result['message']}")
        return

    print(f"✓ Profile loaded: {profile_result['name']}")
    print(f"  - Skills: {profile_result['skills_count']}")
    print(f"  - Experiences: {profile_result['experiences_count']}")

    # Step 2: Load job
    print("\n[2/3] Loading job description...")
    job_result = handle_load_job_description({
        "file_path": "examples/test_job.md"
    })

    if job_result['status'] != 'success':
        print(f"❌ Failed to load job: {job_result['message']}")
        return

    print(f"✓ Job loaded: {job_result['title']} at {job_result['company']}")
    print(f"  - Required skills: {job_result['required_skills_count']}")
    print(f"  - Preferred skills: {job_result['preferred_skills_count']}")

    # Step 3: Analyze match
    print("\n[3/3] Analyzing match...")
    match_result = handle_analyze_match({
        "profile_id": profile_result['profile_id'],
        "job_id": job_result['job_id'],
    })

    if match_result['status'] != 'success':
        print(f"❌ Failed to analyze match: {match_result['message']}")
        return

    print(f"✓ Match analysis complete!")

    # Display detailed results
    print("\n" + "=" * 80)
    print("MATCH RESULTS")
    print("=" * 80)

    print(f"\n📊 Overall Score: {match_result['overall_score']}%")

    print(f"\n📈 Score Breakdown:")
    breakdown = match_result['breakdown']
    print(f"  • Technical Skills:  {breakdown['technical_skills_score']:.1f}%")
    print(f"  • Experience Level:  {breakdown['experience_score']:.1f}%")
    print(f"  • Domain Knowledge:  {breakdown['domain_score']:.1f}%")
    print(f"  • Keyword Coverage:  {breakdown['keyword_coverage_score']:.1f}%")

    print(f"\n✅ Matched Skills: {match_result['matched_skills_count']}")

    if match_result['missing_required_skills']:
        print(f"\n❌ Missing Required Skills:")
        for skill in match_result['missing_required_skills']:
            print(f"  • {skill}")

    if match_result['missing_preferred_skills']:
        print(f"\n⚠️  Missing Preferred Skills:")
        for skill in match_result['missing_preferred_skills'][:5]:
            print(f"  • {skill}")

    if match_result['suggestions']:
        print(f"\n💡 Suggestions:")
        for i, suggestion in enumerate(match_result['suggestions'], 1):
            print(f"  {i}. {suggestion}")

    if match_result['top_achievements']:
        print(f"\n🏆 Top Achievements:")
        for i, ach in enumerate(match_result['top_achievements'], 1):
            print(f"  {i}. [{ach['score']:.1f}] {ach['text'][:80]}...")

    print("\n" + "=" * 80)
    print("✅ Phase 2 test completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    test_phase2_complete_workflow()
```

## Option 4: Run Unit Tests

```bash
# Run all Phase 2 tests
pytest tests/test_matcher.py tests/test_achievement_ranking.py tests/test_match_scoring.py -v

# Run specific test class
pytest tests/test_matcher.py::TestSkillMatching -v

# Run with coverage
pytest tests/test_matcher.py tests/test_achievement_ranking.py tests/test_match_scoring.py --cov=src/resume_customizer/core/matcher --cov-report=html
```

## Expected Results

### Good Match (70-100%)
- Profile has most required skills
- Experience level matches or exceeds requirement
- Relevant domain knowledge
- Good keyword overlap

### Medium Match (40-69%)
- Profile has some required skills
- Experience level close to requirement
- Some relevant experience
- Moderate keyword overlap

### Low Match (<40%)
- Profile missing many required skills
- Under-qualified on experience
- Different domain
- Low keyword overlap

## Troubleshooting

### Error: "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### Error: "File not found"
- Make sure you're in the correct directory
- Check file paths are correct
- Use absolute paths if needed

### Error: "Module not found"
```bash
pip install -e .
```

## Next Steps

After manual testing confirms everything works:
1. Run all unit tests: `pytest`
2. Check test coverage: `pytest --cov`
3. Proceed to Phase 3 implementation
