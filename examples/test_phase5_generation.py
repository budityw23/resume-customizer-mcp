#!/usr/bin/env python3
"""
Test Phase 5 functionality - Document Generation.

This script tests the complete Phase 5 workflow using real data:
- Load Budi's resume
- Load Full Stack Engineer job description
- Analyze match
- Customize resume
- Generate PDF and DOCX files with all three templates
- Save files to examples/output directory
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
    handle_generate_resume_files,
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


def verify_file(file_path: str, expected_extension: str, max_size_kb: int = 500) -> bool:
    """Verify generated file exists and is valid."""
    path = Path(file_path)

    if not path.exists():
        print_error(f"File does not exist: {file_path}")
        return False

    if path.suffix != expected_extension:
        print_error(f"Wrong file extension: expected {expected_extension}, got {path.suffix}")
        return False

    file_size_kb = path.stat().st_size / 1024

    if file_size_kb == 0:
        print_error(f"File is empty: {file_path}")
        return False

    if file_size_kb > max_size_kb:
        print_error(f"File too large: {file_size_kb:.2f}KB (max: {max_size_kb}KB)")
        return False

    print_success(f"Valid {expected_extension} file: {file_size_kb:.2f}KB")
    return True


def main():
    """Run the test."""
    print_header("Phase 5 Testing - Document Generation")

    # File paths
    resume_file = "examples/resumes/budi_resume.md"
    job_file = "examples/jobs/fullstack_engineer_job.md"
    output_dir = Path("examples/output/phase5")

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

    print_success("Match analysis complete")
    print_info(f"Match ID: {match_result['match_id']}")
    print_info(f"Overall Score: {match_result['overall_score']}%")
    print_info(f"Technical Skills: {match_result['breakdown']['technical_skills_score']}%")
    print_info(f"Experience: {match_result['breakdown']['experience_score']}%")

    match_id = match_result["match_id"]

    # Step 4: Customize Resume
    print_header("Step 4: Customize Resume", level=2)
    custom_result = handle_customize_resume({
        "match_id": match_id,
        "preferences": {
            "achievements_per_role": 4,
            "max_skills": 15,
            "include_summary": True,
        },
    })

    if custom_result["status"] != "success":
        print_error(f"Failed to customize: {custom_result['message']}")
        return False

    print_success("Resume customized successfully")
    print_info(f"Customization ID: {custom_result['customization_id']}")
    print_info(f"Experiences: {custom_result['experiences_count']}")
    print_info(f"Skills: {custom_result['skills_count']}")
    print_info(f"Template: {custom_result['template']}")

    customization_id = custom_result["customization_id"]

    # Step 5a: Generate PDF - Modern Template
    print_header("Step 5a: Generate PDF - Modern Template", level=2)
    pdf_modern = handle_generate_resume_files({
        "customization_id": customization_id,
        "output_formats": ["pdf"],
        "output_directory": str(output_dir),
        "template": "modern",
        "filename_prefix": "budi_resume_modern",
    })

    if pdf_modern["status"] != "success":
        print_error(f"Failed to generate PDF: {pdf_modern['message']}")
        return False

    print_success("PDF generated with modern template")
    print_info(f"File: {pdf_modern['generated_files']['pdf']}")

    if not verify_file(pdf_modern['generated_files']['pdf'], ".pdf"):
        return False

    # Step 5b: Generate PDF - Classic Template
    print_header("Step 5b: Generate PDF - Classic Template", level=2)
    pdf_classic = handle_generate_resume_files({
        "customization_id": customization_id,
        "output_formats": ["pdf"],
        "output_directory": str(output_dir),
        "template": "classic",
        "filename_prefix": "budi_resume_classic",
    })

    if pdf_classic["status"] != "success":
        print_error(f"Failed to generate PDF: {pdf_classic['message']}")
        return False

    print_success("PDF generated with classic template")
    print_info(f"File: {pdf_classic['generated_files']['pdf']}")

    if not verify_file(pdf_classic['generated_files']['pdf'], ".pdf"):
        return False

    # Step 5c: Generate PDF - ATS Optimized Template
    print_header("Step 5c: Generate PDF - ATS Optimized Template", level=2)
    pdf_ats = handle_generate_resume_files({
        "customization_id": customization_id,
        "output_formats": ["pdf"],
        "output_directory": str(output_dir),
        "template": "ats_optimized",
        "filename_prefix": "budi_resume_ats",
    })

    if pdf_ats["status"] != "success":
        print_error(f"Failed to generate PDF: {pdf_ats['message']}")
        return False

    print_success("PDF generated with ATS optimized template")
    print_info(f"File: {pdf_ats['generated_files']['pdf']}")

    if not verify_file(pdf_ats['generated_files']['pdf'], ".pdf"):
        return False

    # Step 6a: Generate DOCX - Modern Template
    print_header("Step 6a: Generate DOCX - Modern Template", level=2)
    docx_modern = handle_generate_resume_files({
        "customization_id": customization_id,
        "output_formats": ["docx"],
        "output_directory": str(output_dir),
        "template": "modern",
        "filename_prefix": "budi_resume_modern",
    })

    if docx_modern["status"] != "success":
        print_error(f"Failed to generate DOCX: {docx_modern['message']}")
        return False

    print_success("DOCX generated with modern template")
    print_info(f"File: {docx_modern['generated_files']['docx']}")

    if not verify_file(docx_modern['generated_files']['docx'], ".docx"):
        return False

    # Step 6b: Generate DOCX - Classic Template
    print_header("Step 6b: Generate DOCX - Classic Template", level=2)
    docx_classic = handle_generate_resume_files({
        "customization_id": customization_id,
        "output_formats": ["docx"],
        "output_directory": str(output_dir),
        "template": "classic",
        "filename_prefix": "budi_resume_classic",
    })

    if docx_classic["status"] != "success":
        print_error(f"Failed to generate DOCX: {docx_classic['message']}")
        return False

    print_success("DOCX generated with classic template")
    print_info(f"File: {docx_classic['generated_files']['docx']}")

    if not verify_file(docx_classic['generated_files']['docx'], ".docx"):
        return False

    # Step 6c: Generate DOCX - ATS Optimized Template
    print_header("Step 6c: Generate DOCX - ATS Optimized Template", level=2)
    docx_ats = handle_generate_resume_files({
        "customization_id": customization_id,
        "output_formats": ["docx"],
        "output_directory": str(output_dir),
        "template": "ats_optimized",
        "filename_prefix": "budi_resume_ats",
    })

    if docx_ats["status"] != "success":
        print_error(f"Failed to generate DOCX: {docx_ats['message']}")
        return False

    print_success("DOCX generated with ATS optimized template")
    print_info(f"File: {docx_ats['generated_files']['docx']}")

    if not verify_file(docx_ats['generated_files']['docx'], ".docx"):
        return False

    # Step 7: Generate Both Formats at Once
    print_header("Step 7: Generate Both PDF and DOCX Together", level=2)
    both_formats = handle_generate_resume_files({
        "customization_id": customization_id,
        "output_formats": ["pdf", "docx"],
        "output_directory": str(output_dir),
        "template": "modern",
        "filename_prefix": "budi_resume_complete",
    })

    if both_formats["status"] != "success":
        print_error(f"Failed to generate files: {both_formats['message']}")
        return False

    print_success("Both PDF and DOCX generated together")
    print_info(f"PDF: {both_formats['generated_files']['pdf']}")
    print_info(f"DOCX: {both_formats['generated_files']['docx']}")

    if not verify_file(both_formats['generated_files']['pdf'], ".pdf"):
        return False
    if not verify_file(both_formats['generated_files']['docx'], ".docx"):
        return False

    # Save test summary
    print_header("Saving Test Summary", level=2)
    summary = {
        "test_name": "Phase 5 Document Generation",
        "profile": {
            "name": profile_result['name'],
            "profile_id": profile_id,
            "skills_count": profile_result['skills_count'],
            "experiences_count": profile_result['experiences_count'],
        },
        "job": {
            "title": job_result['title'],
            "company": job_result['company'],
            "job_id": job_id,
        },
        "match": {
            "match_id": match_id,
            "overall_score": match_result['overall_score'],
            "breakdown": match_result['breakdown'],
        },
        "customization": {
            "customization_id": customization_id,
            "experiences_count": custom_result['experiences_count'],
            "skills_count": custom_result['skills_count'],
        },
        "generated_files": {
            "pdf_modern": pdf_modern['generated_files']['pdf'],
            "pdf_classic": pdf_classic['generated_files']['pdf'],
            "pdf_ats": pdf_ats['generated_files']['pdf'],
            "docx_modern": docx_modern['generated_files']['docx'],
            "docx_classic": docx_classic['generated_files']['docx'],
            "docx_ats": docx_ats['generated_files']['docx'],
            "pdf_complete": both_formats['generated_files']['pdf'],
            "docx_complete": both_formats['generated_files']['docx'],
        },
    }

    summary_file = output_dir / "test_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print_success(f"Test summary saved to {summary_file}")

    # Final Summary
    print_header("Test Summary", level=1)
    print_success(f"Profile loaded: {profile_result['name']}")
    print_success(f"Job loaded: {job_result['title']} at {job_result['company']}")
    print_success(f"Match score: {match_result['overall_score']}%")
    print_success(f"Customization created: {customization_id[:8]}...")
    print_success(f"Generated files:")
    print_info("  PDF files:")
    print_info(f"    • Modern template: {Path(pdf_modern['generated_files']['pdf']).name}")
    print_info(f"    • Classic template: {Path(pdf_classic['generated_files']['pdf']).name}")
    print_info(f"    • ATS template: {Path(pdf_ats['generated_files']['pdf']).name}")
    print_info("  DOCX files:")
    print_info(f"    • Modern template: {Path(docx_modern['generated_files']['docx']).name}")
    print_info(f"    • Classic template: {Path(docx_classic['generated_files']['docx']).name}")
    print_info(f"    • ATS template: {Path(docx_ats['generated_files']['docx']).name}")
    print_info("  Combined:")
    print_info(f"    • PDF + DOCX: {Path(both_formats['generated_files']['pdf']).name}")

    print_success(f"All files saved to: {output_dir}")

    print_header("✅ ALL TESTS PASSED!", level=1)
    print_info("Phase 5 document generation is working correctly!")
    print_info("You can find the generated files in: examples/output/phase5/")
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
