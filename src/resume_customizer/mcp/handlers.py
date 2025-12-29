"""
MCP tool handlers for Resume Customizer Server.

This module implements the actual logic for each MCP tool.
"""

import uuid
from datetime import datetime
from typing import Any

from resume_customizer.core.matcher import calculate_match_score
from resume_customizer.parsers.markdown_parser import parse_job_description, parse_resume
from resume_customizer.utils.logger import get_logger

logger = get_logger(__name__)

# Session state to store loaded profiles, jobs, and results
_session_state: dict[str, Any] = {
    "profiles": {},
    "jobs": {},
    "matches": {},
    "customizations": {},
}


def handle_load_user_profile(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle load_user_profile tool call.

    Args:
        arguments: Tool arguments with 'file_path'

    Returns:
        Dictionary with parsed profile data
    """
    file_path = arguments.get("file_path")

    if not file_path:
        return {
            "status": "error",
            "message": "Missing required parameter: file_path",
        }

    logger.info(f"Loading user profile from: {file_path}")

    try:
        # Parse the resume
        profile = parse_resume(file_path)

        # Generate a unique profile ID if not present
        if not profile.profile_id:
            profile.profile_id = f"profile-{uuid.uuid4().hex[:8]}"

        if not profile.created_at:
            profile.created_at = datetime.now().isoformat()

        # Store in session state
        _session_state["profiles"][profile.profile_id] = profile

        logger.info(f"Profile loaded successfully: {profile.profile_id}")

        return {
            "status": "success",
            "message": f"User profile loaded successfully: {profile.name}",
            "profile_id": profile.profile_id,
            "file_path": file_path,
            "name": profile.name,
            "skills_count": len(profile.skills),
            "experiences_count": len(profile.experiences),
        }

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {
            "status": "error",
            "message": f"File not found: {file_path}",
        }
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        return {
            "status": "error",
            "message": f"Error loading profile: {str(e)}",
        }


def handle_load_job_description(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle load_job_description tool call.

    Args:
        arguments: Tool arguments with 'file_path'

    Returns:
        Dictionary with parsed job data
    """
    file_path = arguments.get("file_path")

    if not file_path:
        return {
            "status": "error",
            "message": "Missing required parameter: file_path",
        }

    logger.info(f"Loading job description from: {file_path}")

    try:
        # Parse the job description
        job = parse_job_description(file_path)

        # Generate a unique job ID if not present
        if not job.job_id:
            job.job_id = f"job-{uuid.uuid4().hex[:8]}"

        if not job.created_at:
            job.created_at = datetime.now().isoformat()

        # Store in session state
        _session_state["jobs"][job.job_id] = job

        logger.info(f"Job description loaded successfully: {job.job_id}")

        return {
            "status": "success",
            "message": f"Job description loaded successfully: {job.title} at {job.company}",
            "job_id": job.job_id,
            "file_path": file_path,
            "title": job.title,
            "company": job.company,
            "required_skills_count": len(job.requirements.required_skills),
            "preferred_skills_count": len(job.requirements.preferred_skills),
        }

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return {
            "status": "error",
            "message": f"File not found: {file_path}",
        }
    except Exception as e:
        logger.error(f"Error loading job description: {str(e)}")
        return {
            "status": "error",
            "message": f"Error loading job description: {str(e)}",
        }


def handle_analyze_match(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle analyze_match tool call.

    Args:
        arguments: Tool arguments with 'profile_id' and 'job_id'

    Returns:
        Dictionary with match analysis results
    """
    profile_id = arguments.get("profile_id")
    job_id = arguments.get("job_id")

    # Validate inputs
    if not profile_id:
        return {
            "status": "error",
            "message": "Missing required parameter: profile_id",
        }

    if not job_id:
        return {
            "status": "error",
            "message": "Missing required parameter: job_id",
        }

    logger.info(f"Analyzing match: profile={profile_id}, job={job_id}")

    try:
        # Retrieve profile from session state
        profile = _session_state["profiles"].get(profile_id)
        if not profile:
            return {
                "status": "error",
                "message": f"Profile not found: {profile_id}. Please load a profile first using load_user_profile.",
            }

        # Retrieve job from session state
        job = _session_state["jobs"].get(job_id)
        if not job:
            return {
                "status": "error",
                "message": f"Job description not found: {job_id}. Please load a job description first using load_job_description.",
            }

        # Calculate match score
        match_result = calculate_match_score(profile, job)

        # Generate a unique match ID
        match_id = f"match-{uuid.uuid4().hex[:8]}"
        match_result.created_at = datetime.now().isoformat()

        # Store in session state
        _session_state["matches"][match_id] = match_result

        logger.info(
            f"Match analysis completed: {match_id} - Score: {match_result.overall_score}%"
        )

        # Format response
        return {
            "status": "success",
            "message": f"Match analysis completed: {match_result.overall_score}% match",
            "match_id": match_id,
            "profile_id": profile_id,
            "job_id": job_id,
            "overall_score": match_result.overall_score,
            "breakdown": {
                "technical_skills_score": match_result.breakdown.technical_skills_score,
                "experience_score": match_result.breakdown.experience_score,
                "domain_score": match_result.breakdown.domain_score,
                "keyword_coverage_score": match_result.breakdown.keyword_coverage_score,
                "matched_skills_count": len(match_result.matched_skills),
                "total_required_skills": len(match_result.missing_required_skills) + len(match_result.matched_skills),
            },
            "matched_skills": match_result.matched_skills,
            "matched_skills_count": len(match_result.matched_skills),
            "missing_required_skills": match_result.missing_required_skills,
            "missing_preferred_skills": match_result.missing_preferred_skills,
            "suggestions": match_result.suggestions,
            "top_achievements": [
                {
                    "text": achievement.text,
                    "score": score,
                    "matched_keywords": achievement.matched_keywords if hasattr(achievement, 'matched_keywords') else [],
                }
                for achievement, score in match_result.ranked_achievements[:5]
            ],
        }

    except Exception as e:
        logger.error(f"Error analyzing match: {str(e)}")
        return {
            "status": "error",
            "message": f"Error analyzing match: {str(e)}",
        }


def handle_customize_resume(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle customize_resume tool call.

    Args:
        arguments: Tool arguments with 'match_id' and optional 'preferences'

    Returns:
        Dictionary with customized resume data
    """
    match_id = arguments.get("match_id")
    preferences = arguments.get("preferences", {})
    logger.info(f"Customizing resume: match={match_id}, preferences={preferences}")

    # TODO: Implement in Phase 4 - Use customization engine
    # For now, return a stub response
    return {
        "status": "success",
        "message": "Resume customized successfully (stub)",
        "customization_id": "stub-customization-id",
        "match_id": match_id,
        "template": preferences.get("template", "modern"),
    }


def handle_generate_resume_files(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle generate_resume_files tool call.

    Args:
        arguments: Tool arguments with 'customization_id' and optional params

    Returns:
        Dictionary with generated file paths
    """
    customization_id = arguments.get("customization_id")
    output_formats = arguments.get("output_formats", ["pdf", "docx"])
    output_directory = arguments.get("output_directory", "./output")
    logger.info(
        f"Generating resume files: customization={customization_id}, "
        f"formats={output_formats}, output_dir={output_directory}"
    )

    # TODO: Implement in Phase 5 - Use document generators
    # For now, return a stub response
    return {
        "status": "success",
        "message": "Resume files generated successfully (stub)",
        "customization_id": customization_id,
        "generated_files": {
            "pdf": f"{output_directory}/resume-stub.pdf" if "pdf" in output_formats else None,
            "docx": f"{output_directory}/resume-stub.docx" if "docx" in output_formats else None,
        },
    }


def handle_list_customizations(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle list_customizations tool call.

    Args:
        arguments: Tool arguments with optional filters

    Returns:
        Dictionary with list of customizations
    """
    filter_by_company = arguments.get("filter_by_company")
    limit = arguments.get("limit", 10)
    logger.info(f"Listing customizations: company={filter_by_company}, limit={limit}")

    # TODO: Implement in Phase 6 - Use database
    # For now, return a stub response
    return {
        "status": "success",
        "message": "Customizations listed successfully (stub)",
        "count": 0,
        "customizations": [],
    }


# Mapping of tool names to handler functions
TOOL_HANDLERS: dict[str, Any] = {
    "load_user_profile": handle_load_user_profile,
    "load_job_description": handle_load_job_description,
    "analyze_match": handle_analyze_match,
    "customize_resume": handle_customize_resume,
    "generate_resume_files": handle_generate_resume_files,
    "list_customizations": handle_list_customizations,
}
