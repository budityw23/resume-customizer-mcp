"""
MCP tool handlers for Resume Customizer Server.

This module implements the actual logic for each MCP tool.
"""

import uuid
from datetime import datetime
from typing import Any

from resume_customizer.core.customizer import (
    CustomizationPreferences,
    customize_resume,
)
from resume_customizer.core.exceptions import (
    ParseError,
    ResourceNotFoundError,
    ResumeCustomizerError,
    ValidationError,
)
from resume_customizer.core.matcher import calculate_match_score
from resume_customizer.parsers.markdown_parser import parse_job_description, parse_resume
from resume_customizer.storage.database import CustomizationDatabase
from resume_customizer.utils.logger import get_logger
from resume_customizer.utils.validation import (
    validate_file_path,
    validate_id,
)

logger = get_logger(__name__)


def _format_error_response(error: Exception) -> dict[str, Any]:
    """
    Format an exception into a consistent error response.

    Args:
        error: The exception to format

    Returns:
        Dictionary with error details
    """
    if isinstance(error, ResumeCustomizerError):
        response = {
            "status": "error",
            "message": error.message,
        }
        if error.suggestion:
            response["suggestion"] = error.suggestion
        return response

    # For unexpected errors, return generic message
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    return {
        "status": "error",
        "message": f"An unexpected error occurred: {str(error)}",
        "suggestion": "Please check the logs for more details or contact support.",
    }

# Global database instance
_database: CustomizationDatabase | None = None


def _get_database() -> CustomizationDatabase:
    """Get or create the global database instance."""
    global _database
    if _database is None:
        _database = CustomizationDatabase()
    return _database


# Global session manager instance
_session_manager: Any = None


def _get_session_manager() -> Any:
    """Get or create the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        from resume_customizer.storage.session import SessionManager

        _session_manager = SessionManager(default_ttl=3600)  # 1 hour TTL
    return _session_manager


# Legacy session state dict (for backward compatibility during migration)
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
    try:
        # Validate file path
        file_path = validate_file_path(arguments.get("file_path"))

        logger.info(f"Loading user profile from: {file_path}")

        # Parse the resume
        try:
            profile = parse_resume(file_path)
        except Exception as parse_error:
            raise ParseError(file_path, str(parse_error)) from parse_error

        # Generate a unique profile ID if not present
        if not profile.profile_id:
            profile.profile_id = f"profile-{uuid.uuid4().hex[:8]}"

        if not profile.created_at:
            profile.created_at = datetime.now().isoformat()

        # Store in session using SessionManager
        session = _get_session_manager()
        session.set_profile(profile.profile_id, profile)

        # Also keep in legacy dict for backward compatibility
        _session_state["profiles"][profile.profile_id] = profile

        # Also save to database
        try:
            db = _get_database()
            db.insert_profile(
                profile_id=profile.profile_id,
                name=profile.name,
                email=profile.contact.email,
                full_data=profile.to_dict(),
                phone=profile.contact.phone,
                location=profile.contact.location,
                linkedin=profile.contact.linkedin,
                github=profile.contact.github,
                website=profile.contact.portfolio,
                summary=profile.summary,
                skills_count=len(profile.skills),
                experiences_count=len(profile.experiences),
                education_count=len(profile.education),
                certifications_count=len(profile.certifications),
                created_at=profile.created_at,
            )
            logger.info(f"Saved profile to database: {profile.profile_id}")
        except Exception as db_error:
            # Don't fail the load if database save fails
            logger.warning(f"Failed to save profile to database: {str(db_error)}")

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

    except (ValidationError, ParseError, ResumeCustomizerError) as e:
        return _format_error_response(e)
    except Exception as e:
        return _format_error_response(e)


def handle_load_job_description(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle load_job_description tool call.

    Args:
        arguments: Tool arguments with 'file_path'

    Returns:
        Dictionary with parsed job data
    """
    try:
        # Validate file path
        file_path = validate_file_path(arguments.get("file_path"))

        logger.info(f"Loading job description from: {file_path}")

        # Parse the job description
        try:
            job = parse_job_description(file_path)
        except Exception as parse_error:
            raise ParseError(file_path, str(parse_error)) from parse_error

        # Generate a unique job ID if not present
        if not job.job_id:
            job.job_id = f"job-{uuid.uuid4().hex[:8]}"

        if not job.created_at:
            job.created_at = datetime.now().isoformat()

        # Store in session using SessionManager
        session = _get_session_manager()
        session.set_job(job.job_id, job)

        # Also keep in legacy dict for backward compatibility
        _session_state["jobs"][job.job_id] = job

        # Also save to database
        try:
            db = _get_database()
            db.insert_job(
                job_id=job.job_id,
                title=job.title,
                company=job.company,
                full_data=job.to_dict(),
                location=job.location,
                job_type=job.job_type,
                experience_level=job.experience_level,
                salary_range=job.salary_range,
                required_skills_count=len(job.requirements.required_skills),
                preferred_skills_count=len(job.requirements.preferred_skills),
                created_at=job.created_at,
            )
            logger.info(f"Saved job to database: {job.job_id}")
        except Exception as db_error:
            # Don't fail the load if database save fails
            logger.warning(f"Failed to save job to database: {str(db_error)}")

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

    except (ValidationError, ParseError, ResumeCustomizerError) as e:
        return _format_error_response(e)
    except Exception as e:
        return _format_error_response(e)


def handle_analyze_match(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle analyze_match tool call.

    Args:
        arguments: Tool arguments with 'profile_id' and 'job_id'

    Returns:
        Dictionary with match analysis results
    """
    try:
        # Validate inputs
        profile_id = validate_id(
            arguments.get("profile_id"), "profile_id", "profile"
        )
        job_id = validate_id(arguments.get("job_id"), "job_id", "job")

        logger.info(f"Analyzing match: profile={profile_id}, job={job_id}")

        # Retrieve profile from session (try SessionManager first, fall back to legacy)
        session = _get_session_manager()
        profile = session.get_profile(profile_id)
        if not profile:
            profile = _session_state["profiles"].get(profile_id)
        if not profile:
            raise ResourceNotFoundError("profile", profile_id)

        # Retrieve job from session (try SessionManager first, fall back to legacy)
        job = session.get_job(job_id)
        if not job:
            job = _session_state["jobs"].get(job_id)
        if not job:
            raise ResourceNotFoundError("job", job_id)

        # Calculate match score
        match_result = calculate_match_score(profile, job)

        # Generate a unique match ID
        match_id = f"match-{uuid.uuid4().hex[:8]}"
        match_result.created_at = datetime.now().isoformat()

        # Store in session using SessionManager
        session = _get_session_manager()
        session.set_match(match_id, match_result)

        # Also keep in legacy dict for backward compatibility
        _session_state["matches"][match_id] = match_result

        # Also save to database
        try:
            db = _get_database()
            db.insert_match(
                match_id=match_id,
                profile_id=profile_id,
                job_id=job_id,
                overall_score=match_result.overall_score,
                technical_score=int(match_result.breakdown.technical_skills_score),
                experience_score=int(match_result.breakdown.experience_score),
                domain_score=int(match_result.breakdown.domain_score),
                keyword_coverage=int(match_result.breakdown.keyword_coverage_score),
                matched_skills_count=len(match_result.matched_skills),
                missing_skills_count=len(match_result.missing_required_skills),
                full_data=match_result.to_dict(),
                created_at=match_result.created_at,
            )
            logger.info(f"Saved match result to database: {match_id}")
        except Exception as db_error:
            # Don't fail the match if database save fails
            logger.warning(f"Failed to save match to database: {str(db_error)}")

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

    except (ValidationError, ResourceNotFoundError, ResumeCustomizerError) as e:
        return _format_error_response(e)
    except Exception as e:
        return _format_error_response(e)


def handle_customize_resume(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle customize_resume tool call.

    Args:
        arguments: Tool arguments with 'match_id' and optional 'preferences'

    Returns:
        Dictionary with customized resume data
    """
    match_id = arguments.get("match_id")
    preferences_dict = arguments.get("preferences", {})

    # Validate match_id
    if not match_id:
        return {
            "status": "error",
            "message": "Missing required parameter: match_id",
        }

    logger.info(f"Customizing resume: match={match_id}, preferences={preferences_dict}")

    try:
        # Retrieve match result from session (try SessionManager first)
        session = _get_session_manager()
        match_result = session.get_match(match_id)
        if not match_result:
            match_result = _session_state["matches"].get(match_id)
        if not match_result:
            return {
                "status": "error",
                "message": f"Match not found: {match_id}. Please run analyze_match first.",
            }

        # Retrieve profile from session state
        profile_id = match_result.profile_id
        profile = _session_state["profiles"].get(profile_id)
        if not profile:
            return {
                "status": "error",
                "message": f"Profile not found: {profile_id}. Session state may be corrupted.",
            }

        # Parse preferences
        preferences = None
        if preferences_dict:
            preferences = CustomizationPreferences(
                achievements_per_role=preferences_dict.get("achievements_per_role", 3),
                max_skills=preferences_dict.get("max_skills"),
                template=preferences_dict.get("template", "modern"),
                include_summary=preferences_dict.get("include_summary", True),
            )

        # Customize resume using the core logic
        customized_resume = customize_resume(
            user_profile=profile,
            match_result=match_result,
            preferences=preferences,
        )

        # Store in session using SessionManager
        session = _get_session_manager()
        session.set_customization(
            customized_resume.customization_id, customized_resume
        )

        # Also keep in legacy dict for backward compatibility
        _session_state["customizations"][
            customized_resume.customization_id
        ] = customized_resume

        # Also store in database
        try:
            # Get job info for database
            job = _session_state["jobs"].get(customized_resume.job_id)
            job_title = job.title if job else "Unknown"
            company = job.company if job else "Unknown"

            # Get match result for overall score
            match_result = customized_resume.match_result
            overall_score = match_result.overall_score if match_result else 0

            # Ensure customization_id is not None
            customization_id = customized_resume.customization_id
            if not customization_id:
                raise ValueError("Customization ID is required")

            db = _get_database()
            db.insert_customization(
                customization_id=customization_id,
                profile_id=customized_resume.profile_id,
                job_id=customized_resume.job_id,
                profile_name=profile.name,
                job_title=job_title,
                company=company,
                overall_score=overall_score,
                template=customized_resume.template,
                created_at=customized_resume.created_at or datetime.now().isoformat(),
                metadata=customized_resume.metadata,
            )
            logger.info(f"Saved customization to database: {customized_resume.customization_id}")
        except Exception as db_error:
            # Don't fail the customization if database save fails
            logger.warning(f"Failed to save customization to database: {str(db_error)}")

        logger.info(
            f"Resume customized successfully: {customized_resume.customization_id} - "
            f"{len(customized_resume.selected_experiences)} experiences, "
            f"{len(customized_resume.reordered_skills)} skills"
        )

        # Format response
        return {
            "status": "success",
            "message": f"Resume customized successfully for {profile.name}",
            "customization_id": customized_resume.customization_id,
            "match_id": match_id,
            "profile_id": profile_id,
            "job_id": customized_resume.job_id,
            "created_at": customized_resume.created_at,
            "template": customized_resume.template,
            "experiences_count": len(customized_resume.selected_experiences),
            "skills_count": len(customized_resume.reordered_skills),
            "include_summary": customized_resume.customized_summary is not None,
            "metadata": {
                "changes_count": customized_resume.metadata.get("changes_count", 0),
                "achievements_reordered": customized_resume.metadata.get("achievements_reordered", 0),
                "skills_reordered": customized_resume.metadata.get("skills_reordered", 0),
            },
            "changes_summary": customized_resume.metadata.get("changes_log", {}),  # Full changes log
        }

    except ValueError as e:
        # Handle validation errors (e.g., fabricated achievements/skills)
        logger.error(f"Validation error customizing resume: {str(e)}")
        return {
            "status": "error",
            "message": f"Validation error: {str(e)}",
        }
    except Exception as e:
        logger.error(f"Error customizing resume: {str(e)}")
        return {
            "status": "error",
            "message": f"Error customizing resume: {str(e)}",
        }


def handle_generate_resume_files(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Handle generate_resume_files tool call.

    Args:
        arguments: Tool arguments with 'customization_id' and optional params

    Returns:
        Dictionary with generated file paths
    """
    from pathlib import Path

    from ..generators.template_engine import TemplateEngine

    customization_id = arguments.get("customization_id")
    output_formats = arguments.get("output_formats", ["pdf"])
    output_directory = arguments.get("output_directory", "./output")
    template = arguments.get("template")  # Optional override
    filename_prefix = arguments.get("filename_prefix", "resume")

    logger.info(
        f"Generating resume files: customization={customization_id}, "
        f"formats={output_formats}, output_dir={output_directory}"
    )

    # Validate customization_id
    if not customization_id:
        return {
            "status": "error",
            "message": "Missing required field: customization_id",
        }

    # Get customization from session (try SessionManager first)
    session = _get_session_manager()
    customized_resume = session.get_customization(customization_id)
    if not customized_resume:
        customized_resume = _session_state["customizations"].get(customization_id)
    if not customized_resume:
        return {
            "status": "error",
            "message": f"Customization not found: {customization_id}",
        }

    # Get user profile from session (try SessionManager first)
    profile_id = customized_resume.profile_id
    user_profile = session.get_profile(profile_id)
    if not user_profile:
        user_profile = _session_state["profiles"].get(profile_id)
    if not user_profile:
        return {
            "status": "error",
            "message": f"Profile not found: {profile_id}",
        }

    # Determine template to use
    template_name = template or customized_resume.template

    # Create output directory
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate files
    generated_files: dict[str, str | None] = {}
    try:
        engine = TemplateEngine()

        # Generate PDF
        if "pdf" in output_formats:
            pdf_filename = f"{filename_prefix}_{customization_id[:8]}.pdf"
            pdf_path = output_path / pdf_filename
            engine.generate_pdf(
                customized_resume, user_profile, pdf_path, template_name
            )
            generated_files["pdf"] = str(pdf_path.absolute())
            logger.info(f"Generated PDF: {pdf_path}")

        # Generate DOCX
        if "docx" in output_formats:
            docx_filename = f"{filename_prefix}_{customization_id[:8]}.docx"
            docx_path = output_path / docx_filename
            engine.generate_docx(
                customized_resume, user_profile, docx_path, template_name
            )
            generated_files["docx"] = str(docx_path.absolute())
            logger.info(f"Generated DOCX: {docx_path}")

        return {
            "status": "success",
            "message": f"Generated {len([f for f in generated_files.values() if f])} file(s)",
            "customization_id": customization_id,
            "template": template_name,
            "generated_files": generated_files,
        }

    except Exception as e:
        logger.error(f"Error generating resume files: {str(e)}")
        return {
            "status": "error",
            "message": f"Error generating files: {str(e)}",
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
    filter_by_date_range = arguments.get("filter_by_date_range", {})
    limit = arguments.get("limit", 10)

    start_date = filter_by_date_range.get("start_date") if filter_by_date_range else None
    end_date = filter_by_date_range.get("end_date") if filter_by_date_range else None

    logger.info(
        f"Listing customizations: company={filter_by_company}, "
        f"dates={start_date} to {end_date}, limit={limit}"
    )

    try:
        db = _get_database()
        customizations = db.get_customizations(
            company=filter_by_company,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        return {
            "status": "success",
            "message": f"Found {len(customizations)} customization(s)",
            "count": len(customizations),
            "customizations": customizations,
        }

    except Exception as e:
        logger.error(f"Error listing customizations: {str(e)}")
        return {
            "status": "error",
            "message": f"Error listing customizations: {str(e)}",
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
