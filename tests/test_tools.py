"""
Tests for MCP tool definitions (src/resume_customizer/mcp/tools.py).

These tests verify that all tool definitions are properly structured
according to the MCP specification.
"""

from mcp.types import Tool

from resume_customizer.mcp.tools import (
    ALL_TOOLS,
    ANALYZE_MATCH_TOOL,
    CUSTOMIZE_RESUME_TOOL,
    GENERATE_RESUME_FILES_TOOL,
    LIST_CUSTOMIZATIONS_TOOL,
    LOAD_JOB_DESCRIPTION_TOOL,
    LOAD_USER_PROFILE_TOOL,
)


class TestToolDefinitions:
    """Test individual tool definitions."""

    def test_load_user_profile_tool(self) -> None:
        """Test LOAD_USER_PROFILE_TOOL definition."""
        assert isinstance(LOAD_USER_PROFILE_TOOL, Tool)
        assert LOAD_USER_PROFILE_TOOL.name == "load_user_profile"
        assert "resume" in LOAD_USER_PROFILE_TOOL.description.lower()

        # Check schema
        schema = LOAD_USER_PROFILE_TOOL.inputSchema
        assert schema["type"] == "object"
        assert "file_path" in schema["properties"]
        assert "file_path" in schema["required"]
        assert schema["properties"]["file_path"]["type"] == "string"

    def test_load_job_description_tool(self) -> None:
        """Test LOAD_JOB_DESCRIPTION_TOOL definition."""
        assert isinstance(LOAD_JOB_DESCRIPTION_TOOL, Tool)
        assert LOAD_JOB_DESCRIPTION_TOOL.name == "load_job_description"
        assert "job" in LOAD_JOB_DESCRIPTION_TOOL.description.lower()

        schema = LOAD_JOB_DESCRIPTION_TOOL.inputSchema
        assert schema["type"] == "object"
        assert "file_path" in schema["properties"]
        assert "file_path" in schema["required"]

    def test_analyze_match_tool(self) -> None:
        """Test ANALYZE_MATCH_TOOL definition."""
        assert isinstance(ANALYZE_MATCH_TOOL, Tool)
        assert ANALYZE_MATCH_TOOL.name == "analyze_match"
        assert "match" in ANALYZE_MATCH_TOOL.description.lower()

        schema = ANALYZE_MATCH_TOOL.inputSchema
        assert schema["type"] == "object"
        assert "profile_id" in schema["properties"]
        assert "job_id" in schema["properties"]
        assert set(schema["required"]) == {"profile_id", "job_id"}

    def test_customize_resume_tool(self) -> None:
        """Test CUSTOMIZE_RESUME_TOOL definition."""
        assert isinstance(CUSTOMIZE_RESUME_TOOL, Tool)
        assert CUSTOMIZE_RESUME_TOOL.name == "customize_resume"
        assert "customize" in CUSTOMIZE_RESUME_TOOL.description.lower()

        schema = CUSTOMIZE_RESUME_TOOL.inputSchema
        assert schema["type"] == "object"
        assert "match_id" in schema["properties"]
        assert "preferences" in schema["properties"]
        assert "match_id" in schema["required"]

        # Check preferences schema
        prefs = schema["properties"]["preferences"]
        assert prefs["type"] == "object"
        assert "template" in prefs["properties"]
        assert "max_achievements_per_role" in prefs["properties"]
        assert "summary_style" in prefs["properties"]

        # Check template enum
        template = prefs["properties"]["template"]
        assert "enum" in template
        assert "modern" in template["enum"]
        assert "classic" in template["enum"]
        assert "ats_optimized" in template["enum"]

    def test_generate_resume_files_tool(self) -> None:
        """Test GENERATE_RESUME_FILES_TOOL definition."""
        assert isinstance(GENERATE_RESUME_FILES_TOOL, Tool)
        assert GENERATE_RESUME_FILES_TOOL.name == "generate_resume_files"
        assert "generate" in GENERATE_RESUME_FILES_TOOL.description.lower()

        schema = GENERATE_RESUME_FILES_TOOL.inputSchema
        assert schema["type"] == "object"
        assert "customization_id" in schema["properties"]
        assert "output_formats" in schema["properties"]
        assert "output_directory" in schema["properties"]
        assert "customization_id" in schema["required"]

        # Check output_formats
        formats = schema["properties"]["output_formats"]
        assert formats["type"] == "array"
        assert formats["items"]["type"] == "string"
        assert set(formats["items"]["enum"]) == {"pdf", "docx"}

    def test_list_customizations_tool(self) -> None:
        """Test LIST_CUSTOMIZATIONS_TOOL definition."""
        assert isinstance(LIST_CUSTOMIZATIONS_TOOL, Tool)
        assert LIST_CUSTOMIZATIONS_TOOL.name == "list_customizations"
        assert "list" in LIST_CUSTOMIZATIONS_TOOL.description.lower()

        schema = LIST_CUSTOMIZATIONS_TOOL.inputSchema
        assert schema["type"] == "object"
        assert "filter_by_company" in schema["properties"]
        assert "filter_by_date_range" in schema["properties"]
        assert "limit" in schema["properties"]

        # Check filter_by_date_range structure
        date_range = schema["properties"]["filter_by_date_range"]
        assert date_range["type"] == "object"
        assert "start_date" in date_range["properties"]
        assert "end_date" in date_range["properties"]


class TestAllTools:
    """Test ALL_TOOLS collection."""

    def test_all_tools_list(self) -> None:
        """Test that ALL_TOOLS contains all tool definitions."""
        assert isinstance(ALL_TOOLS, list)
        assert len(ALL_TOOLS) == 6

        # Check all tools are Tool instances
        for tool in ALL_TOOLS:
            assert isinstance(tool, Tool)

    def test_all_tools_contains_expected_tools(self) -> None:
        """Test that ALL_TOOLS contains all expected tools."""
        expected_tools = {
            "load_user_profile",
            "load_job_description",
            "analyze_match",
            "customize_resume",
            "generate_resume_files",
            "list_customizations",
        }

        actual_tools = {tool.name for tool in ALL_TOOLS}
        assert actual_tools == expected_tools

    def test_all_tools_unique_names(self) -> None:
        """Test that all tools have unique names."""
        tool_names = [tool.name for tool in ALL_TOOLS]
        assert len(tool_names) == len(set(tool_names))

    def test_all_tools_have_descriptions(self) -> None:
        """Test that all tools have non-empty descriptions."""
        for tool in ALL_TOOLS:
            assert tool.description
            assert len(tool.description) > 10

    def test_all_tools_have_valid_schemas(self) -> None:
        """Test that all tools have valid input schemas."""
        for tool in ALL_TOOLS:
            schema = tool.inputSchema
            assert isinstance(schema, dict)
            assert schema.get("type") == "object"
            assert "properties" in schema


class TestToolSchemaProperties:
    """Test specific schema property requirements."""

    def test_required_fields_are_in_properties(self) -> None:
        """Test that all required fields are defined in properties."""
        for tool in ALL_TOOLS:
            schema = tool.inputSchema
            required = schema.get("required", [])
            properties = schema.get("properties", {})

            for field in required:
                assert field in properties, f"Tool {tool.name}: required field '{field}' not in properties"

    def test_enum_properties_have_values(self) -> None:
        """Test that enum properties have at least one value."""
        for tool in ALL_TOOLS:
            schema = tool.inputSchema
            properties = schema.get("properties", {})

            for prop_name, prop_def in properties.items():
                if "enum" in prop_def:
                    assert len(prop_def["enum"]) > 0, f"Tool {tool.name}: enum '{prop_name}' has no values"

    def test_array_properties_have_items(self) -> None:
        """Test that array properties define item types."""
        for tool in ALL_TOOLS:
            schema = tool.inputSchema
            properties = schema.get("properties", {})

            def check_array_items(props: dict, path: str = "", _tool_name: str = tool.name) -> None:
                for prop_name, prop_def in props.items():
                    current_path = f"{path}.{prop_name}" if path else prop_name
                    if isinstance(prop_def, dict):
                        if prop_def.get("type") == "array":
                            assert "items" in prop_def, f"Tool {_tool_name}: array '{current_path}' missing items definition"
                        # Recursively check nested objects
                        if prop_def.get("type") == "object" and "properties" in prop_def:
                            check_array_items(prop_def["properties"], current_path, _tool_name)

            check_array_items(properties)


class TestToolNaming:
    """Test tool naming conventions."""

    def test_tool_names_are_lowercase_with_underscores(self) -> None:
        """Test that tool names follow snake_case convention."""
        for tool in ALL_TOOLS:
            assert tool.name == tool.name.lower()
            assert " " not in tool.name
            assert "-" not in tool.name
            # Should only contain lowercase letters, numbers, and underscores
            assert all(c.islower() or c.isdigit() or c == "_" for c in tool.name)

    def test_tool_descriptions_are_sentences(self) -> None:
        """Test that descriptions are properly formatted sentences."""
        for tool in ALL_TOOLS:
            # Should start with capital letter
            assert tool.description[0].isupper()
            # Should be descriptive (more than just a few words)
            assert len(tool.description.split()) >= 5
