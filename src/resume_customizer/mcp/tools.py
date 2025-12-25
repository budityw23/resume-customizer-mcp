"""
MCP tool definitions for Resume Customizer Server.

This module defines all the MCP tools (functions) that the server exposes
to Claude and other MCP clients.
"""

from mcp.types import Tool

# Tool definitions as per MCP specification


LOAD_USER_PROFILE_TOOL = Tool(
    name="load_user_profile",
    description="Load and parse a user's resume from a markdown file",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the markdown resume file (resume.md)",
            }
        },
        "required": ["file_path"],
    },
)

LOAD_JOB_DESCRIPTION_TOOL = Tool(
    name="load_job_description",
    description="Load and parse a job description from a markdown file",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the markdown job description file (job.md)",
            }
        },
        "required": ["file_path"],
    },
)

ANALYZE_MATCH_TOOL = Tool(
    name="analyze_match",
    description="Analyze how well a user profile matches a job description",
    inputSchema={
        "type": "object",
        "properties": {
            "profile_id": {
                "type": "string",
                "description": "ID of the loaded user profile",
            },
            "job_id": {
                "type": "string",
                "description": "ID of the loaded job description",
            },
        },
        "required": ["profile_id", "job_id"],
    },
)

CUSTOMIZE_RESUME_TOOL = Tool(
    name="customize_resume",
    description="Customize a resume for a specific job based on match analysis",
    inputSchema={
        "type": "object",
        "properties": {
            "match_id": {
                "type": "string",
                "description": "ID of the match analysis result",
            },
            "preferences": {
                "type": "object",
                "description": "Customization preferences",
                "properties": {
                    "template": {
                        "type": "string",
                        "enum": ["modern", "classic", "ats_optimized"],
                        "description": "Resume template to use",
                    },
                    "max_achievements_per_role": {
                        "type": "integer",
                        "description": "Maximum number of achievements to show per role",
                        "default": 4,
                    },
                    "summary_style": {
                        "type": "string",
                        "enum": ["technical", "results", "balanced"],
                        "description": "Style for the professional summary",
                        "default": "balanced",
                    },
                },
            },
        },
        "required": ["match_id"],
    },
)

GENERATE_RESUME_FILES_TOOL = Tool(
    name="generate_resume_files",
    description="Generate PDF and/or DOCX files from a customized resume",
    inputSchema={
        "type": "object",
        "properties": {
            "customization_id": {
                "type": "string",
                "description": "ID of the customized resume",
            },
            "output_formats": {
                "type": "array",
                "items": {"type": "string", "enum": ["pdf", "docx"]},
                "description": "Output file formats to generate",
                "default": ["pdf", "docx"],
            },
            "output_directory": {
                "type": "string",
                "description": "Directory to save the generated files",
            },
        },
        "required": ["customization_id"],
    },
)

LIST_CUSTOMIZATIONS_TOOL = Tool(
    name="list_customizations",
    description="List all resume customizations with optional filtering",
    inputSchema={
        "type": "object",
        "properties": {
            "filter_by_company": {
                "type": "string",
                "description": "Filter by company name",
            },
            "filter_by_date_range": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10,
            },
        },
    },
)

# List of all available tools
ALL_TOOLS = [
    LOAD_USER_PROFILE_TOOL,
    LOAD_JOB_DESCRIPTION_TOOL,
    ANALYZE_MATCH_TOOL,
    CUSTOMIZE_RESUME_TOOL,
    GENERATE_RESUME_FILES_TOOL,
    LIST_CUSTOMIZATIONS_TOOL,
]
