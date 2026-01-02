#!/usr/bin/env python3
"""
Test Phase 4 functionality with Budi's actual resume and job description.

This script tests the complete Phase 4 workflow using real data:
- Load Budi's resume
- Load Full Stack Engineer job description
- Analyze match
- Customize resume with various preferences
- Save detailed output to examples/output directory
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from resume_customizer.mcp.handlers import (
    _session_state,
    handle_analyze_match,
    handle_customize_resume,
    handle_load_job_description,
    handle_load_user_profile,
)


def print_header(text: str, level: int = 1):
    """Print a formatted header."""
    if level == 1:
        print(f"\n{'=' * 80}")
        print(f"  {text}")
        print(f"{'=' * 80}")
    else:
        print(f"\n{'-' * 80}")
        print(f"  {text}")
        print(f"{'-' * 80}")


def print_success(text: str):
    """Print success message."""
    print(f"✓ {text}")


def print_info(text: str):
    """Print info message."""
    print(f"• {text}")


def print_error(text: str):
    """Print error message."""
    print(f"✗ {text}")


def save_customization_output(customization, filename: str, output_dir: Path):
    """Save customization details to a JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / filename

    # Convert customization object to dict
    output_data = {
        "customization_id": customization.customization_id,
        "profile_id": customization.profile_id,
        "job_id": customization.job_id,
        "template": customization.template,
        "created_at": customization.created_at,
        "experiences_count": len(customization.selected_experiences),
        "skills_count": len(customization.reordered_skills),
        "has_summary": customization.customized_summary is not None,
        "experiences": [
            {
                "company": exp.company,
                "title": exp.title,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "achievements_count": len(exp.achievements),
                "achievements": [
                    {
                        "description": ach.description,
                        "relevance_score": ach.relevance_score,
                        "has_metrics": ach.has_metrics,
                        "has_leadership": ach.has_leadership,
                    }
                    for ach in exp.achievements
                ],
            }
            for exp in customization.selected_experiences
        ],
        "skills": [
            {
                "name": skill.name,
                "category": skill.category,
                "proficiency": skill.proficiency,
                "years": skill.years,
            }
            for skill in customization.reordered_skills
        ],
        "summary": customization.customized_summary,
        "metadata": customization.metadata,
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    print_success(f"Saved output to {output_file}")


def main():
    """Run the test."""
    print_header("Phase 4 Testing - Budi's Resume Customization")

    # File paths
    resume_file = "examples/resumes/budi_resume.md"
    job_file = "examples/jobs/fullstack_engineer_job.md"
    output_dir = Path("examples/output")

    print_info(f"Resume: {resume_file}")
    print_info(f"Job: {job_file}")
    print_info(f"Output directory: {output_dir}")

    # Clear session state
    _session_state["profiles"].clear()
    _session_state["jobs"].clear()
    _session_state["matches"].clear()
    _session_state["customizations"].clear()

    # Step 1: Load Profile
    print_header("Step 1: Load User Profile", level=2)
    profile_result = handle_load_user_profile({"file_path": resume_file})

    if profile_result["status"] != "success":
        print_error(f"Failed to load profile: {profile_result['message']}")
        return False

    print_success(f"Loaded profile: {profile_result['name']}")
    print_info(f"Profile ID: {profile_result['profile_id']}")
    print_info(f"Skills: {profile_result['skills_count']}")
    print_info(f"Experiences: {profile_result['experiences_count']}")

    profile_id = profile_result["profile_id"]

    # Step 2: Load Job Description
    print_header("Step 2: Load Job Description", level=2)
    job_result = handle_load_job_description({"file_path": job_file})

    if job_result["status"] != "success":
        print_error(f"Failed to load job: {job_result['message']}")
        return False

    print_success(f"Loaded job: {job_result['title']} at {job_result['company']}")
    print_info(f"Job ID: {job_result['job_id']}")
    print_info(f"Required skills: {job_result['required_skills_count']}")
    print_info(f"Preferred skills: {job_result['preferred_skills_count']}")

    job_id = job_result["job_id"]

    # Step 3: Analyze Match
    print_header("Step 3: Analyze Match", level=2)
    match_result = handle_analyze_match({
        "profile_id": profile_id,
        "job_id": job_id,
    })

    if match_result["status"] != "success":
        print_error(f"Failed to analyze match: {match_result['message']}")
        return False

    print_success(f"Match analysis complete")
    print_info(f"Match ID: {match_result['match_id']}")
    print_info(f"Overall Score: {match_result['overall_score']}%")
    print_info(f"Technical Skills: {match_result['breakdown']['technical_skills_score']}%")
    print_info(f"Experience: {match_result['breakdown']['experience_score']}%")
    print_info(f"Domain: {match_result['breakdown']['domain_score']}%")
    print_info(f"Matched Skills: {match_result['matched_skills_count']}")

    if match_result.get('missing_required_skills'):
        print_info(f"Missing Required: {', '.join(match_result['missing_required_skills'][:5])}")

    match_id = match_result["match_id"]

    # Step 4: Customize Resume - Default Preferences
    print_header("Step 4a: Customize Resume - Default Preferences", level=2)
    custom1 = handle_customize_resume({
        "match_id": match_id,
    })

    if custom1["status"] != "success":
        print_error(f"Failed to customize: {custom1['message']}")
        return False

    print_success("Resume customized with default preferences")
    print_info(f"Customization ID: {custom1['customization_id']}")
    print_info(f"Template: {custom1['template']}")
    print_info(f"Experiences: {custom1['experiences_count']}")
    print_info(f"Skills: {custom1['skills_count']}")
    print_info(f"Include Summary: {custom1['include_summary']}")
    print_info(f"Achievements Reordered: {custom1['metadata']['achievements_reordered']}")
    print_info(f"Skills Reordered: {custom1['metadata']['skills_reordered']}")

    # Display changes summary
    if custom1.get('changes_summary'):
        changes = custom1['changes_summary']
        print_info(f"Achievements Removed: {changes.get('achievements_removed', 0)}")
        print_info(f"Skills Removed: {changes.get('skills_removed', 0)}")

    # Save output
    customization_obj = _session_state["customizations"][custom1["customization_id"]]
    save_customization_output(customization_obj, "budi_resume_default.json", output_dir)

    # Step 5: Customize Resume - Custom Preferences
    print_header("Step 4b: Customize Resume - Custom Preferences", level=2)
    custom2 = handle_customize_resume({
        "match_id": match_id,
        "preferences": {
            "achievements_per_role": 4,
            "max_skills": 12,
            "template": "ats",
            "include_summary": True,
        },
    })

    if custom2["status"] != "success":
        print_error(f"Failed to customize: {custom2['message']}")
        return False

    print_success("Resume customized with custom preferences")
    print_info(f"Customization ID: {custom2['customization_id']}")
    print_info(f"Template: {custom2['template']}")
    print_info(f"Experiences: {custom2['experiences_count']}")
    print_info(f"Skills: {custom2['skills_count']} (max: 12)")
    print_info(f"Include Summary: {custom2['include_summary']}")

    # Save output
    customization_obj = _session_state["customizations"][custom2["customization_id"]]
    save_customization_output(customization_obj, "budi_resume_custom.json", output_dir)

    # Step 6: Customize Resume - Minimal
    print_header("Step 4c: Customize Resume - Minimal (ATS Optimized)", level=2)
    custom3 = handle_customize_resume({
        "match_id": match_id,
        "preferences": {
            "achievements_per_role": 3,
            "max_skills": 8,
            "template": "minimal",
            "include_summary": False,
        },
    })

    if custom3["status"] != "success":
        print_error(f"Failed to customize: {custom3['message']}")
        return False

    print_success("Resume customized for ATS")
    print_info(f"Customization ID: {custom3['customization_id']}")
    print_info(f"Template: {custom3['template']}")
    print_info(f"Experiences: {custom3['experiences_count']}")
    print_info(f"Skills: {custom3['skills_count']} (max: 8)")
    print_info(f"Include Summary: {custom3['include_summary']}")

    # Save output
    customization_obj = _session_state["customizations"][custom3["customization_id"]]
    save_customization_output(customization_obj, "budi_resume_minimal.json", output_dir)

    # Also save the match result
    match_output = {
        "match_id": match_result["match_id"],
        "profile_id": profile_id,
        "job_id": job_id,
        "overall_score": match_result["overall_score"],
        "breakdown": match_result["breakdown"],
        "matched_skills_count": match_result["matched_skills_count"],
        "missing_required_skills": match_result.get("missing_required_skills", []),
        "missing_preferred_skills": match_result.get("missing_preferred_skills", []),
    }
    with open(output_dir / "match_analysis.json", "w") as f:
        json.dump(match_output, f, indent=2)
    print_success(f"Saved match analysis to {output_dir / 'match_analysis.json'}")

    # Summary
    print_header("Test Summary", level=1)
    print_success(f"Profile loaded: {profile_result['name']}")
    print_success(f"Job loaded: {job_result['title']} at {job_result['company']}")
    print_success(f"Match score: {match_result['overall_score']}%")
    print_success(f"Created {len(_session_state['customizations'])} customizations:")

    for i, (cid, customization) in enumerate(_session_state["customizations"].items(), 1):
        print_info(f"  {i}. {cid[:8]}... - {customization.template} template - "
                  f"{len(customization.selected_experiences)} exp, "
                  f"{len(customization.reordered_skills)} skills")

    print_header("✅ ALL TESTS PASSED!", level=1)
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
