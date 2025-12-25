# Technical Implementation Plan: Resume Customizer MCP Server

## Document Information
- **Project**: Resume Customizer MCP Server
- **Version**: 1.0
- **Timeline**: 8 weeks (56 days)
- **Target Completion**: [Start Date + 8 weeks]
- **Developer**: Development with Claude Code
- **Status**: Planning

---

## Overview

This implementation plan breaks down the Resume Customizer MCP Server development into 8 manageable phases, each with specific deliverables, acceptance criteria, and testing requirements.

**Total Estimated Effort:** 8 weeks (280-320 hours)

---

## Phase 1: Core Foundation (Week 1)
**Duration:** 5-7 days  
**Effort:** 35-40 hours  
**Goal:** Establish project structure, parsers, and basic data models

### 1.1 Project Setup (Day 1-2)

#### Tasks
1. **Initialize Python Project**
   - Create project directory structure
   - Set up `pyproject.toml` with dependencies
   - Configure virtual environment
   - Set up Git repository with `.gitignore`

2. **Configure Development Tools**
   - Install and configure Black (code formatting)
   - Install and configure Ruff (linting)
   - Install and configure MyPy (type checking)
   - Set up pre-commit hooks

3. **Environment Configuration**
   - Create `.env.example` template
   - Set up configuration management (`config.py`)
   - Configure logging system
   - Set up development vs production configs

#### Deliverables
- [ ] Working project structure matching TECHNICAL_DESIGN.md
- [ ] All dependencies installable via `pip install -e .`
- [ ] Development tools configured and working
- [ ] Git repository initialized with first commit

#### Acceptance Criteria
- ✅ `pip install -e .` works without errors
- ✅ `black src/` formats code successfully
- ✅ `ruff check src/` runs without errors
- ✅ `mypy src/` type checks successfully
- ✅ All files have proper docstrings

#### Files Created
```
resume-customizer-mcp/
├── pyproject.toml
├── .gitignore
├── .env.example
├── README.md
├── src/resume_customizer/
│   ├── __init__.py
│   ├── config.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
```

---

### 1.2 Markdown Parsers (Day 2-4)

#### Tasks
1. **Resume Markdown Parser**
   - Parse personal information section
   - Extract work experience with achievements
   - Parse skills sections (multiple categories)
   - Extract education and certifications
   - Parse projects, publications, awards
   - Handle optional sections gracefully
   - Extract preferences section

2. **Job Description Markdown Parser**
   - Parse job details section
   - Extract responsibilities and qualifications
   - Parse required vs preferred skills
   - Extract company information
   - Handle various job posting formats
   - Extract user notes section

3. **Validation System**
   - Validate required fields presence
   - Check data format (emails, dates, URLs)
   - Validate date logic (end > start)
   - Warning system for missing metrics
   - Error handling for malformed markdown

#### Deliverables
- [ ] `parsers/markdown_parser.py` with full resume parsing
- [ ] `parsers/markdown_parser.py` with full job parsing
- [ ] `parsers/validator.py` with validation rules
- [ ] Unit tests for all parsers (>90% coverage)

#### Acceptance Criteria
- ✅ Parses `resume_template.md` without errors
- ✅ Parses `job_template.md` without errors
- ✅ Extracts all sections correctly
- ✅ Handles missing optional sections
- ✅ Provides helpful error messages
- ✅ Validates data formats correctly
- ✅ All tests pass

#### Test Cases
```python
def test_parse_resume_valid():
    """Parse valid resume.md successfully"""
    
def test_parse_resume_missing_required():
    """Fail gracefully with missing required fields"""
    
def test_parse_resume_invalid_email():
    """Validate email format"""
    
def test_parse_achievements_with_metrics():
    """Extract achievements and identify metrics"""
    
def test_parse_skills_multiple_categories():
    """Parse skills organized in categories"""
```

---

### 1.3 Data Models (Day 4-5)

#### Tasks
1. **Core Models**
   - Define `ContactInfo` dataclass
   - Define `Achievement` dataclass with metadata
   - Define `Experience` dataclass
   - Define `Skill` dataclass with proficiency
   - Define `Education`, `Certification`, `Project` dataclasses
   - Define `UserProfile` master dataclass

2. **Job Models**
   - Define `JobRequirements` dataclass
   - Define `JobKeywords` dataclass
   - Define `JobDescription` dataclass

3. **Result Models**
   - Define `SkillMatch` dataclass
   - Define `MatchBreakdown` dataclass
   - Define `MatchResult` dataclass
   - Define `CustomizedResume` dataclass

4. **Serialization**
   - Add `to_dict()` methods
   - Add `from_dict()` class methods
   - Add JSON serialization support

#### Deliverables
- [ ] `core/models.py` with all dataclasses
- [ ] Type hints on all fields
- [ ] Docstrings for all classes
- [ ] Serialization methods
- [ ] Unit tests for models

#### Acceptance Criteria
- ✅ All models properly typed with type hints
- ✅ Models can be serialized to/from dict
- ✅ Default values set appropriately
- ✅ Validation in `__post_init__` where needed
- ✅ MyPy passes with no errors

---

### 1.4 Basic MCP Server Scaffold (Day 5-7)

#### Tasks
1. **MCP Server Setup**
   - Create `server.py` entry point
   - Set up MCP Server instance
   - Configure stdio transport
   - Add basic logging
   - Implement graceful shutdown

2. **Tool Registration System**
   - Create `mcp/tools.py` for tool definitions
   - Create `mcp/handlers.py` for handler stubs
   - Register tools with MCP server
   - Implement `list_tools()` handler
   - Implement basic `call_tool()` dispatcher

3. **Testing Infrastructure**
   - Set up pytest configuration
   - Create test utilities
   - Add fixtures for test data
   - Create example resume.md and job.md for testing

#### Deliverables
- [ ] `server.py` with working MCP server
- [ ] `mcp/tools.py` with all 6 tool definitions
- [ ] `mcp/handlers.py` with stub handlers
- [ ] Server starts and responds to tool list request
- [ ] `tests/` directory with pytest setup

#### Acceptance Criteria
- ✅ Server starts without errors
- ✅ `list_tools()` returns 6 tool definitions
- ✅ Server responds to MCP protocol correctly
- ✅ Logging works properly
- ✅ Can connect from MCP inspector

#### Integration Test
```bash
# Start server
python -m resume_customizer.server

# In another terminal, test with MCP inspector
mcp-inspector python -m resume_customizer.server

# Should see 6 tools listed
```

---

### Phase 1 Completion Checklist

**Before moving to Phase 2:**
- [ ] All files follow project structure
- [ ] Code passes all linters (black, ruff, mypy)
- [ ] Unit tests >90% coverage
- [ ] Documentation complete (docstrings)
- [ ] Example files (resume.md, job.md) created
- [ ] MCP server starts successfully
- [ ] Can list tools via MCP
- [ ] Git commits with clear messages

**Phase 1 Exit Criteria:**
✅ Can parse resume.md into UserProfile object  
✅ Can parse job.md into JobDescription object  
✅ MCP server responds to list_tools request  
✅ All tests pass  
✅ No type errors  

---

## Phase 2: Matching Engine (Week 2)
**Duration:** 5-7 days  
**Effort:** 35-40 hours  
**Goal:** Implement intelligent matching and scoring algorithms

### 2.1 Skill Matching Algorithm (Day 8-10)

#### Tasks
1. **Skill Extraction & Normalization**
   - Extract all skills from UserProfile
   - Normalize skill names (case, spacing)
   - Build skill synonym dictionary
   - Handle skill variations (Python vs python vs Python3)
   - Technology hierarchy (React implies JavaScript)

2. **Skill Matching Logic**
   - Exact match detection
   - Fuzzy matching for similar skills
   - Synonym matching
   - Parent-child skill relationships
   - Weight required vs preferred skills

3. **Scoring Algorithm**
   - Calculate required skills match (0-100%)
   - Calculate preferred skills match (0-100%)
   - Identify missing required skills
   - Identify missing preferred skills
   - Generate skill match report

#### Deliverables
- [ ] `core/matcher.py` with `SkillMatcher` class
- [ ] `config/skill_synonyms.yaml` with common synonyms
- [ ] Fuzzy matching implementation
- [ ] Unit tests for all matching scenarios

#### Acceptance Criteria
- ✅ Matches "Python" with "python", "Python3", "py"
- ✅ Identifies missing required skills correctly
- ✅ Weights required skills higher than preferred
- ✅ Handles typos and variations
- ✅ Score is reproducible and deterministic

#### Test Cases
```python
def test_exact_skill_match():
    """Match exact skill names"""
    
def test_case_insensitive_match():
    """Match skills regardless of case"""
    
def test_synonym_matching():
    """Match skill synonyms (JS = JavaScript)"""
    
def test_missing_required_skills():
    """Identify skills in job but not in resume"""
    
def test_skill_hierarchy():
    """React experience implies JavaScript"""
```

---

### 2.2 Achievement Ranking System (Day 10-12)

#### Tasks
1. **Setup**
   - Install spaCy model: `python -m spacy download en_core_web_sm`

2. **Keyword Extraction**
   - Extract keywords from achievement text
   - Use NLP (spaCy) for entity recognition
   - Identify technical terms
   - Extract action verbs
   - Identify metrics and numbers

3. **Relevance Scoring**
   - Calculate keyword overlap with job
   - Weight by keyword importance
   - Score technology match
   - Bonus for metrics presence
   - Recency bonus for recent achievements

4. **Ranking Algorithm**
   - Score all achievements against job
   - Sort by relevance score
   - Group by job role
   - Apply position-based penalties
   - Return ranked list with scores

#### Deliverables
- [ ] `core/matcher.py` extended with `rank_achievements()`
- [ ] Keyword extraction using spaCy
- [ ] Relevance scoring algorithm
- [ ] Unit tests with various achievement types

#### Acceptance Criteria
- ✅ Achievements with matching tech score higher
- ✅ Achievements with metrics score higher
- ✅ Recent achievements get recency bonus
- ✅ Ranking is consistent and explainable
- ✅ Returns scores with explanations

#### Test Cases
```python
def test_rank_by_keyword_match():
    """Higher keyword overlap = higher rank"""
    
def test_rank_by_technology():
    """Matching technologies rank higher"""
    
def test_metrics_bonus():
    """Achievements with metrics get bonus"""
    
def test_recency_bonus():
    """Recent achievements ranked higher when equal"""
```

---

### 2.3 Match Scoring Implementation (Day 12-14)

#### Tasks
1. **Component Scores**
   - Technical skills match (40% weight)
   - Experience level match (25% weight)
   - Domain knowledge match (20% weight)
   - Keyword coverage (15% weight)

2. **Overall Score Calculation**
   - Weighted average of component scores
   - Normalize to 0-100 scale
   - Round to integer
   - Provide breakdown

3. **Gap Analysis**
   - Identify critical gaps (missing required)
   - Identify recommended additions (missing preferred)
   - Suggest skill improvements
   - Estimate learning time for gaps

4. **Match Report Generation**
   - Create comprehensive MatchResult object
   - Include all component scores
   - List matched and missing skills
   - Provide actionable suggestions
   - Rank all achievements by relevance

#### Deliverables
- [ ] `core/matcher.py` with `calculate_match_score()`
- [ ] Complete MatchResult generation
- [ ] Gap analysis algorithm
- [ ] Suggestion engine
- [ ] Comprehensive unit tests

#### Acceptance Criteria
- ✅ Overall score is 0-100 integer
- ✅ Component scores sum correctly with weights
- ✅ Gap analysis identifies real gaps
- ✅ Suggestions are actionable
- ✅ Achievement rankings make sense

#### Test Cases
```python
def test_perfect_match():
    """100% match when all skills present"""
    
def test_no_match():
    """Low score when few skills match"""
    
def test_weighted_scoring():
    """Verify weighted average calculation"""
    
def test_gap_identification():
    """Correctly identify missing skills"""
    
def test_realistic_scenario():
    """Test with real resume + job data"""
```

---

### 2.4 MCP Tool: analyze_match (Day 14)

#### Tasks
1. **Handler Implementation**
   - Implement `handle_analyze_match()` in handlers.py
   - Load profile and job from session state
   - Call matching engine
   - Format response as JSON
   - Handle errors gracefully

2. **Session State Management**
   - Store loaded profiles in memory
   - Store loaded jobs in memory
   - Track analysis results
   - Implement simple in-memory cache

3. **Integration Testing**
   - Test via MCP inspector
   - Test with actual resume.md and job.md
   - Verify match scores make sense
   - Test error cases

#### Deliverables
- [ ] Working `analyze_match` MCP tool
- [ ] Session state management
- [ ] Integration tests
- [ ] Error handling

#### Acceptance Criteria
- ✅ Returns valid MatchResult JSON
- ✅ Scores are reasonable (not always 100 or 0)
- ✅ Gap analysis is accurate
- ✅ Works end-to-end via MCP

---

### Phase 2 Completion Checklist

**Before moving to Phase 3:**
- [ ] All matching algorithms implemented
- [ ] Unit tests pass with >90% coverage
- [ ] Integration test passes
- [ ] Match scores validated against manual review
- [ ] Documentation complete
- [ ] No performance issues (< 5 seconds)

**Phase 2 Exit Criteria:**
✅ Can calculate accurate match scores  
✅ Achievement ranking makes sense  
✅ Gap analysis identifies real gaps  
✅ `analyze_match` tool works via MCP  
✅ All tests pass  

---

## Phase 3: AI Integration (Week 3)
**Duration:** 5-7 days  
**Effort:** 35-40 hours  
**Goal:** Integrate Claude API for intelligent features

### 3.1 Claude API Service (Day 15-16)

#### Tasks
1. **API Client Setup**
   - Create `core/ai_service.py`
   - Install Anthropic SDK: Add to pyproject.toml
   - Initialize Anthropic client
   - Load API key from environment
   - Implement error handling
   - Add retry logic with exponential backoff
   - Implement rate limiting

2. **Base API Functions**
   - `call_claude()` - Generic API call wrapper
   - `extract_keywords()` - Keyword extraction prompt
   - `generate_summary()` - Summary generation prompt
   - `rephrase_achievement()` - Achievement rephrasing
   - Response parsing and validation

3. **Caching Strategy**
   - Cache API responses to reduce costs
   - Implement TTL for cache
   - Cache invalidation logic
   - File-based cache for development

#### Deliverables
- [ ] `core/ai_service.py` with API client
- [ ] Error handling and retries
- [ ] Caching implementation
- [ ] Unit tests with mocked responses

#### Acceptance Criteria
- ✅ Can connect to Claude API
- ✅ Handles rate limits gracefully
- ✅ Retries on transient failures
- ✅ Caches responses correctly
- ✅ API key loaded from .env

#### Test Cases
```python
def test_api_connection():
    """Connect to Claude API successfully"""
    
def test_retry_on_failure():
    """Retry on 5xx errors"""
    
def test_cache_hit():
    """Use cached response when available"""
    
def test_rate_limit_handling():
    """Handle 429 rate limit errors"""
```

---

### 3.2 Keyword Extraction (Day 17-18)

#### Tasks
1. **Job Keyword Extraction**
   - Create prompt for extracting technical keywords
   - Extract domain knowledge keywords
   - Extract soft skill keywords
   - Categorize keywords by type
   - Weight keywords by importance

2. **Resume Keyword Extraction**
   - Extract skills from achievements
   - Identify implicit skills
   - Find domain expertise
   - Extract action verbs

3. **Fallback to spaCy**
   - Implement spaCy-based extraction
   - Use when API unavailable
   - Compare AI vs rule-based results
   - Hybrid approach (AI + spaCy)

#### Deliverables
- [ ] AI-powered keyword extraction
- [ ] spaCy fallback implementation
- [ ] Keyword categorization
- [ ] Unit tests

#### Acceptance Criteria
- ✅ Extracts relevant keywords from job descriptions
- ✅ Categorizes keywords correctly
- ✅ Falls back to spaCy if API fails
- ✅ Results are consistent and useful

---

### 3.3 Achievement Rephrasing (Day 18-19)

#### Tasks
1. **Rephrasing Prompt Engineering**
   - Create prompt template for achievement rephrasing
   - Include job keywords in context
   - Preserve original meaning and metrics
   - Optimize for ATS and readability
   - Maintain truthfulness (no exaggeration)

2. **Implementation**
   - Implement `rephrase_achievement()` function
   - Call Claude API with achievement text
   - Parse and validate rephrased version
   - Compare original vs rephrased
   - Allow user approval/rejection

3. **Quality Validation**
   - Verify metrics preserved
   - Check keyword inclusion
   - Ensure no fabrication
   - Validate length (not too long)
   - Grammar and clarity check

#### Deliverables
- [ ] `rephrase_achievement()` function in ai_service.py
- [ ] Prompt template for rephrasing
- [ ] Validation logic
- [ ] Unit tests

#### Acceptance Criteria
- ✅ Rephrased achievements maintain original meaning
- ✅ Metrics and numbers preserved exactly
- ✅ Job keywords naturally included
- ✅ No fabricated information
- ✅ Improved readability and ATS optimization

#### Test Cases
```python
def test_rephrase_preserves_metrics():
    """Ensure numbers/metrics stay exact"""

def test_rephrase_adds_keywords():
    """Job keywords naturally integrated"""

def test_no_fabrication():
    """No new skills or achievements added"""

def test_improved_clarity():
    """Rephrased version is clearer"""
```

**Note:** This feature is optional and can be used selectively by users through Claude conversation.

---

### 3.4 Summary Generation (Day 19-20)

#### Tasks
1. **Summary Prompt Engineering**
   - Create prompt template for summary generation
   - Include job requirements in context
   - Include user's top skills and achievements
   - Specify tone and style preferences
   - Enforce 2-3 sentence limit

2. **Style Variations**
   - Technical-focused style
   - Results-focused style
   - Balanced style
   - Allow custom style via user preference

3. **Quality Validation**
   - Check summary length
   - Verify keywords included
   - Ensure truthfulness (no fabrication)
   - Grammar and tone check

#### Deliverables
- [ ] `generate_custom_summary()` function
- [ ] Multiple style options
- [ ] Quality validation
- [ ] Unit tests with examples

#### Acceptance Criteria
- ✅ Generates 2-3 sentence summaries
- ✅ Includes relevant keywords naturally
- ✅ Different styles produce different outputs
- ✅ No fabricated information
- ✅ Professional tone

#### Test Cases
```python
def test_technical_summary():
    """Generate technical-focused summary"""
    
def test_results_summary():
    """Generate results-focused summary"""
    
def test_keyword_inclusion():
    """Summary includes job keywords"""
    
def test_no_fabrication():
    """Summary only uses resume data"""
    
def test_length_constraint():
    """Summary is 2-3 sentences"""
```

---

### 3.5 Integration & Testing (Day 20-21)

#### Tasks
1. **End-to-End AI Pipeline**
   - Test keyword extraction → matching → summary
   - Verify quality of AI outputs
   - Compare AI vs rule-based results
   - Tune prompts based on results

2. **Cost Optimization**
   - Measure API token usage
   - Implement caching effectively
   - Batch requests where possible
   - Monitor costs during testing

3. **Error Recovery**
   - Handle API failures gracefully
   - Fallback to rule-based when needed
   - Provide degraded but functional experience

#### Deliverables
- [ ] Complete AI pipeline tested
- [ ] Cost monitoring in place
- [ ] Fallback mechanisms working
- [ ] Documentation of API usage patterns

#### Acceptance Criteria
- ✅ AI features improve match quality
- ✅ API costs are reasonable (< $0.10 per customization)
- ✅ Fallbacks work when API unavailable
- ✅ No dependency on API for core functionality

---

### Phase 3 Completion Checklist

**Before moving to Phase 4:**
- [ ] Claude API integration complete
- [ ] Keyword extraction working
- [ ] Summary generation working
- [ ] Caching reduces costs
- [ ] Fallbacks in place
- [ ] Tests pass
- [ ] API usage documented

**Phase 3 Exit Criteria:**
✅ AI features enhance matching  
✅ Summaries are high quality  
✅ Cost per customization < $0.10  
✅ Graceful degradation when API unavailable  
✅ All tests pass  

---

## Phase 4: Customization Engine (Week 4)
**Duration:** 5-7 days  
**Effort:** 35-40 hours  
**Goal:** Build resume customization logic

### 4.1 Achievement Reordering (Day 22-24)

#### Tasks
1. **Ranking Integration**
   - Use match scores from Phase 2
   - Reorder achievements within each job
   - Select top N achievements per role
   - Preserve chronological order of jobs
   - Handle edge cases (few achievements)

2. **Selection Strategy**
   - Top N by relevance score
   - Ensure diversity (not all from one role)
   - Include at least one leadership achievement
   - Balance technical and business impact
   - User preference override

3. **Validation**
   - Ensure no achievements fabricated
   - Verify all selected achievements from original
   - Check achievement text not modified
   - Validate metrics preserved

#### Deliverables
- [ ] `core/customizer.py` with achievement reordering
- [ ] Selection strategies implementation
- [ ] Truthfulness validation
- [ ] Unit tests

#### Acceptance Criteria
- ✅ Most relevant achievements appear first
- ✅ No fabricated content
- ✅ User preferences respected
- ✅ Validation catches any modifications

---

### 4.2 Skills Optimization (Day 24-25)

#### Tasks
1. **Skill Reordering**
   - Move job-relevant skills to top
   - Group by category
   - Hide irrelevant skills (optional)
   - Maintain original categorization
   - Apply user preferences

2. **Display Strategy**
   - Show all skills vs relevant only
   - Top N skills by relevance
   - Category-based grouping
   - Visual emphasis on matched skills

3. **Truthfulness Check**
   - Never add skills not in original resume
   - Never change proficiency levels
   - Only reorder existing skills
   - Flag if user lacks critical skills

#### Deliverables
- [ ] Skills optimization logic
- [ ] Multiple display strategies
- [ ] Truthfulness validation
- [ ] Unit tests

#### Acceptance Criteria
- ✅ Relevant skills appear first
- ✅ No skills added
- ✅ Original data preserved
- ✅ User preferences applied

---

### 4.3 Resume Customization Logic (Day 25-27)

#### Tasks
1. **Customization Engine**
   - Combine all components (achievements, skills, summary)
   - Apply user preferences
   - Generate CustomizedResume object
   - Track changes made
   - Create change log

2. **Preference Handling**
   - Resume length preference
   - Achievements per role
   - Template selection
   - Emphasis keywords
   - Style preferences

3. **Metadata Generation**
   - Record customization timestamp
   - Save original match score
   - Log all changes made
   - Track job details
   - Generate unique ID

#### Deliverables
- [ ] Complete customization engine
- [ ] Preference system
- [ ] Change tracking
- [ ] CustomizedResume model

#### Acceptance Criteria
- ✅ Generates complete customized resume
- ✅ Respects all user preferences
- ✅ Tracks all changes
- ✅ No data loss or fabrication

---

### 4.4 MCP Tool: customize_resume (Day 27-28)

#### Tasks
1. **Handler Implementation**
   - Implement `handle_customize_resume()`
   - Load match result
   - Apply customization
   - Return CustomizedResume
   - Save to session state

2. **Integration Testing**
   - Test full workflow: load → analyze → customize
   - Test various preference combinations
   - Verify output quality
   - Test error handling

#### Deliverables
- [ ] Working `customize_resume` tool
- [ ] Integration tests
- [ ] End-to-end test scenario

#### Acceptance Criteria
- ✅ Tool works via MCP
- ✅ Customization quality is high
- ✅ Preferences applied correctly
- ✅ No errors in normal flow

---

### Phase 4 Completion Checklist

**Before moving to Phase 5:**
- [ ] Customization engine complete
- [ ] Truthfulness validation working
- [ ] Preferences system implemented
- [ ] Tests pass
- [ ] No data fabrication possible
- [ ] Quality review passed

**Phase 4 Exit Criteria:**
✅ Can customize resume for job  
✅ No fabricated information  
✅ User preferences respected  
✅ `customize_resume` tool works  
✅ All tests pass  

---

## Phase 5: Document Generation (Week 5)
**Duration:** 5-7 days  
**Effort:** 35-40 hours  
**Goal:** Generate professional PDF and DOCX files

### 5.1 Template System (Day 29-31)

#### Tasks
1. **HTML Template Structure**
   - Create base template structure
   - Define Jinja2 template syntax
   - Create modern template
   - Create classic template
   - Create ATS-optimized template

2. **Template Rendering**
   - Implement `template_engine.py`
   - Load templates from directory
   - Render with Jinja2
   - Handle missing data gracefully
   - Support custom templates

3. **CSS Styling**
   - Modern template styles
   - Classic template styles
   - ATS-optimized styles
   - Print-friendly CSS
   - Responsive design (for preview)

#### Deliverables
- [ ] `generators/template_engine.py`
- [ ] `templates/modern.html` + CSS
- [ ] `templates/classic.html` + CSS
- [ ] `templates/ats_optimized.html` + CSS
- [ ] Template rendering tests

#### Acceptance Criteria
- ✅ Templates render correctly
- ✅ All three templates look professional
- ✅ Data displays properly
- ✅ Print-friendly output
- ✅ No formatting errors

---

### 5.2 PDF Generator (Day 31-33)

#### Tasks
1. **WeasyPrint Setup**
   - Install WeasyPrint
   - Configure WeasyPrint
   - Set up fonts
   - Configure page settings
   - Implement PDF generation
   - Handle special characters

2. **PDF Optimization**
   - Optimize file size
   - Ensure proper page breaks
   - Verify fonts embed correctly
   - Test printing quality
   - Ensure ATS compatibility

3. **Error Handling**
   - Handle rendering failures
   - Validate PDF output
   - Fallback mechanisms
   - Clear error messages

#### Deliverables
- [ ] `generators/pdf_generator.py`
- [ ] PDF generation working
- [ ] Font handling
- [ ] Unit tests

#### Acceptance Criteria
- ✅ Generates valid PDF files
- ✅ Professional appearance
- ✅ Correct page layout
- ✅ Fonts render properly
- ✅ File size reasonable (< 500KB)

#### Test Cases
```python
def test_generate_pdf_modern():
    """Generate PDF with modern template"""
    
def test_generate_pdf_classic():
    """Generate PDF with classic template"""
    
def test_pdf_one_page():
    """Resume fits on one page when requested"""
    
def test_pdf_file_size():
    """PDF size is reasonable"""
```

---

### 5.3 DOCX Generator (Day 33-34)

#### Tasks
1. **python-docx Setup**
   - Install python-docx
   - Configure document settings
   - Set up styles
   - Define formatting rules
   - Implement DOCX generation

2. **Formatting Implementation**
   - Headers and sections
   - Bullet points
   - Tables (for skills)
   - Font and sizing
   - Margins and spacing

3. **Template Conversion**
   - Convert HTML templates to DOCX logic
   - Maintain consistent styling
   - Support three template styles

#### Deliverables
- [ ] `generators/docx_generator.py`
- [ ] DOCX generation working
- [ ] Style implementation
- [ ] Unit tests

#### Acceptance Criteria
- ✅ Generates valid DOCX files
- ✅ Opens in Microsoft Word correctly
- ✅ Formatting preserved
- ✅ Professional appearance
- ✅ Editable by user

---

### 5.4 MCP Tool: generate_resume_files (Day 34-35)

#### Tasks
1. **Handler Implementation**
   - Implement `handle_generate_resume_files()`
   - Load customized resume
   - Generate PDF and/or DOCX
   - Save to output directory
   - Generate filename
   - Return file paths

2. **File Management**
   - Create output directory if needed
   - Handle filename conflicts
   - Clean up temp files
   - Validate output files

3. **Integration Testing**
   - Test full workflow: load → analyze → customize → generate
   - Test both PDF and DOCX
   - Test all templates
   - Verify file quality

#### Deliverables
- [ ] Working `generate_resume_files` tool
- [ ] File management system
- [ ] Integration tests
- [ ] End-to-end workflow test

#### Acceptance Criteria
- ✅ Generates both PDF and DOCX
- ✅ Files saved to correct location
- ✅ Filenames follow convention
- ✅ Output quality is professional
- ✅ Works via MCP

---

### Phase 5 Completion Checklist

**Before moving to Phase 6:**
- [ ] Templates created and tested
- [ ] PDF generation working
- [ ] DOCX generation working
- [ ] All three template styles implemented
- [ ] File quality verified
- [ ] Tests pass

**Phase 5 Exit Criteria:**
✅ Can generate professional PDF  
✅ Can generate editable DOCX  
✅ Three templates available  
✅ `generate_resume_files` tool works  
✅ All tests pass  

---

## Phase 6: MCP Tools Integration (Week 6)
**Duration:** 5-7 days  
**Effort:** 35-40 hours  
**Goal:** Complete all MCP tools and integration

### 6.1 MCP Tools: load_user_profile & load_job_description (Day 36-38)

#### Tasks
1. **load_user_profile Handler**
   - Implement `handle_load_user_profile()`
   - Parse markdown file
   - Validate data
   - Store in session state
   - Return parsed profile

2. **load_job_description Handler**
   - Implement `handle_load_job_description()`
   - Parse markdown file
   - Extract keywords (with AI if enabled)
   - Store in session state
   - Return parsed job

3. **Error Handling**
   - File not found
   - Parse errors
   - Validation failures
   - Helpful error messages

#### Deliverables
- [ ] `handle_load_user_profile()` complete
- [ ] `handle_load_job_description()` complete
- [ ] Error handling
- [ ] Integration tests

#### Acceptance Criteria
- ✅ Both tools work via MCP
- ✅ Files parsed correctly
- ✅ Validation works
- ✅ Good error messages
- ✅ Session state managed

---

### 6.2 MCP Tool: list_customizations (Day 38-39)

#### Tasks
1. **Database Setup**
   - Create SQLite schema
   - Implement `storage/database.py`
   - Create tables for customizations
   - Add indexes for performance

2. **History Tracking**
   - Save customization records
   - Include all metadata
   - Track files generated
   - Store match scores

3. **List Handler**
   - Implement `handle_list_customizations()`
   - Support filtering
   - Support sorting
   - Pagination support
   - Format output

#### Deliverables
- [ ] SQLite database setup
- [ ] `storage/database.py` complete
- [ ] `handle_list_customizations()` complete
- [ ] Database tests

#### Acceptance Criteria
- ✅ Customizations saved to database
- ✅ Can retrieve customization history
- ✅ Filtering and sorting work
- ✅ Performance is good

---

### 6.3 Error Handling & Validation (Day 39-40)

#### Tasks
1. **Comprehensive Error Handling**
   - Custom exception classes
   - Error response formatting
   - User-friendly messages
   - Logging all errors
   - Stack traces in debug mode

2. **Input Validation**
   - Validate all tool inputs
   - Check file paths exist
   - Validate IDs (profile_id, job_id, etc.)
   - Validate preferences
   - Return validation errors clearly

3. **Recovery Mechanisms**
   - Graceful degradation
   - Fallback to defaults
   - Retry logic where appropriate
   - Clear next steps for user

#### Deliverables
- [ ] Exception classes defined
- [ ] Validation system complete
- [ ] Error handling in all tools
- [ ] Error message tests

#### Acceptance Criteria
- ✅ All errors handled gracefully
- ✅ Error messages are helpful
- ✅ No uncaught exceptions
- ✅ Users know how to fix issues

---

### 6.4 Integration Testing & Polish (Day 40-42)

#### Tasks
1. **End-to-End Testing**
   - Test complete workflow multiple times
   - Test with various resume formats
   - Test with various job descriptions
   - Test error scenarios
   - Test performance

2. **MCP Protocol Compliance**
   - Verify all tool schemas correct
   - Test with MCP inspector
   - Test with Claude Desktop
   - Verify response formats
   - Test concurrent requests

3. **Polish & Optimization**
   - Code cleanup
   - Performance optimization
   - Memory usage check
   - Response time optimization

#### Deliverables
- [ ] Complete integration test suite
- [ ] MCP compliance verified
- [ ] Performance benchmarks met
- [ ] Code polished

#### Acceptance Criteria
- ✅ All 6 tools work correctly
- ✅ End-to-end workflow < 30 seconds
- ✅ MCP protocol compliant
- ✅ No memory leaks
- ✅ Code is clean

---

### Phase 6 Completion Checklist

**Before moving to Phase 7:**
- [ ] All 6 MCP tools implemented
- [ ] Error handling complete
- [ ] Database working
- [ ] Integration tests pass
- [ ] Performance acceptable
- [ ] MCP compliance verified

**Phase 6 Exit Criteria:**
✅ All MCP tools functional  
✅ Complete workflow works  
✅ Error handling robust  
✅ Performance < 30 seconds  
✅ All tests pass  

---

## Phase 7: Storage & History (Week 7)
**Duration:** 5-7 days  
**Effort:** 35-40 hours  
**Goal:** Implement persistent storage and history

### 7.1 Database Schema & Implementation (Day 43-44)

#### Tasks
1. **Database Schema**
   - Design customizations table
   - Design profiles table (cache)
   - Design jobs table (cache)
   - Design match_results table
   - Add proper indexes

2. **Database Operations**
   - CRUD operations for all tables
   - Transaction support
   - Connection pooling
   - Async operations
   - Migration system

3. **Data Persistence**
   - Save customizations
   - Save generated files metadata
   - Save match scores
   - Track changes

#### Deliverables
- [ ] Complete database schema
- [ ] All CRUD operations
- [ ] Database migrations
- [ ] Unit tests

#### Acceptance Criteria
- ✅ Database operations work
- ✅ Data persists correctly
- ✅ Queries are performant
- ✅ No data loss

---

### 7.2 File Management (Day 44-45)

#### Tasks
1. **File Manager Implementation**
   - Create `storage/file_manager.py`
   - Implement file reading operations
   - Implement file writing operations
   - Handle file path validation
   - Directory creation and management

2. **Output File Management**
   - Manage output directory structure
   - Generate unique filenames
   - Handle file conflicts
   - Clean up temporary files
   - Validate file permissions

3. **File Operations**
   - Read markdown files safely
   - Save PDF/DOCX files
   - Track generated file metadata
   - File size validation
   - Error handling for I/O operations

#### Deliverables
- [ ] `storage/file_manager.py` implementation
- [ ] File path validation
- [ ] Output directory management
- [ ] Unit tests for file operations

#### Acceptance Criteria
- ✅ Safe file reading/writing
- ✅ Proper error handling for I/O
- ✅ File conflicts handled gracefully
- ✅ No path traversal vulnerabilities
- ✅ Temp files cleaned up properly

---

### 7.3 Session Management (Day 45-46)

#### Tasks
1. **Session State**
   - In-memory session storage
   - Session lifecycle management
   - Cleanup old sessions
   - Session serialization

2. **State Tracking**
   - Track loaded profiles
   - Track loaded jobs
   - Track match results
   - Track customizations
   - Cross-tool state sharing

#### Deliverables
- [ ] Session management system
- [ ] State tracking
- [ ] Cleanup mechanisms
- [ ] Tests

#### Acceptance Criteria
- ✅ State persists across tool calls
- ✅ No memory leaks
- ✅ Old sessions cleaned up
- ✅ Multi-user support

---

### 7.4 History & Retrieval (Day 46-47)

#### Tasks
1. **History Queries**
   - Query by date range
   - Query by company
   - Query by match score
   - Full-text search
   - Export history to CSV

2. **Analytics**
   - Track application success rate
   - Average match scores
   - Most applied companies
   - Skill gap trends

3. **Data Export**
   - Export customization history
   - Export match analysis
   - Export statistics
   - JSON and CSV formats

#### Deliverables
- [ ] History query system
- [ ] Analytics implementation
- [ ] Export functionality
- [ ] Tests

#### Acceptance Criteria
- ✅ Can query history effectively
- ✅ Analytics provide insights
- ✅ Export works correctly
- ✅ Performance is good

---

### 7.5 Caching Strategy (Day 47-49)

#### Tasks
1. **File-based Cache**
   - Cache API responses
   - Cache parsed resumes
   - Cache parsed jobs
   - TTL implementation
   - Cache invalidation

2. **Cache Management**
   - Cache size limits
   - LRU eviction
   - Manual cache clear
   - Cache statistics

#### Deliverables
- [ ] Caching system
- [ ] Cache management
- [ ] Cache tests

#### Acceptance Criteria
- ✅ Reduces API calls
- ✅ Improves performance
- ✅ Cache invalidation works
- ✅ No stale data issues

---

### Phase 7 Completion Checklist

**Before moving to Phase 8:**
- [ ] Database fully implemented
- [ ] Session management working
- [ ] History tracking complete
- [ ] Caching reduces costs
- [ ] Tests pass
- [ ] No data loss

**Phase 7 Exit Criteria:**
✅ Persistent storage working  
✅ History tracking complete  
✅ Caching improves performance  
✅ All tests pass  

---

## Phase 8: Testing, Documentation & Polish (Week 8)
**Duration:** 5-7 days  
**Effort:** 35-40 hours  
**Goal:** Comprehensive testing, documentation, and final polish

### 8.1 Comprehensive Testing (Day 50-52)

#### Tasks
1. **Unit Test Coverage**
   - Achieve >90% code coverage
   - Test all edge cases
   - Test error conditions
   - Test data validation
   - Parameterized tests

2. **Integration Tests**
   - End-to-end workflows
   - Multi-tool sequences
   - Error recovery flows
   - Performance tests
   - Load tests

3. **MCP Protocol Tests**
   - Tool discovery
   - Tool invocation
   - Response formats
   - Error responses
   - Concurrent requests

4. **Real-world Testing**
   - Test with 10+ real resumes
   - Test with 10+ real job descriptions
   - Validate output quality
   - User acceptance testing
   - Performance benchmarking

#### Deliverables
- [ ] Complete test suite
- [ ] >90% code coverage
- [ ] Integration tests
- [ ] Real-world validation
- [ ] Performance benchmarks

#### Acceptance Criteria
- ✅ All tests pass
- ✅ Coverage > 90%
- ✅ No known bugs
- ✅ Performance targets met
- ✅ Real-world validation passed

---

### 8.2 Documentation (Day 52-54)

#### Tasks
1. **User Documentation**
   - User guide (how to use)
   - Template filling guide
   - Example resumes and jobs
   - Troubleshooting guide
   - FAQ

2. **Developer Documentation**
   - Architecture overview
   - API reference
   - Development setup
   - Contributing guide
   - Code style guide

3. **Code Documentation**
   - Docstrings for all functions
   - Type hints everywhere
   - Inline comments for complex logic
   - README files for modules

4. **Examples**
   - Example resume.md (complete)
   - Example job.md (multiple)
   - Example outputs (PDF, DOCX)
   - Example workflows

#### Deliverables
- [ ] Complete user guide
- [ ] Developer documentation
- [ ] API reference
- [ ] Example files
- [ ] README.md

#### Acceptance Criteria
- ✅ Documentation is complete
- ✅ Examples are helpful
- ✅ Setup instructions work
- ✅ All public APIs documented

---

### 8.3 Performance Optimization (Day 54-55)

#### Tasks
1. **Profiling**
   - Profile CPU usage
   - Profile memory usage
   - Identify bottlenecks
   - Measure API call times

2. **Optimization**
   - Optimize slow functions
   - Reduce memory usage
   - Minimize API calls
   - Optimize database queries
   - Parallel processing where possible

3. **Benchmarking**
   - Measure end-to-end time
   - Measure individual tool times
   - Document performance
   - Set performance budgets

#### Deliverables
- [ ] Performance profile
- [ ] Optimizations implemented
- [ ] Performance benchmarks
- [ ] Performance documentation

#### Acceptance Criteria
- ✅ End-to-end < 30 seconds
- ✅ Memory usage < 500MB
- ✅ API costs < $0.10 per customization
- ✅ No performance regressions

---

### 8.4 Final Polish & Release Preparation (Day 55-56)

#### Tasks
1. **Code Quality**
   - Final code review
   - Fix all linter warnings
   - Update dependencies
   - Remove debug code
   - Clean up comments

2. **Configuration**
   - Production configuration
   - Environment variables documented
   - Security review
   - Secrets management

3. **Packaging**
   - Create distribution package
   - Test installation process
   - Create release notes
   - Version tagging

4. **Claude Desktop Integration**
   - Test with Claude Desktop
   - Create config template
   - Installation guide
   - Troubleshooting guide

#### Deliverables
- [ ] Production-ready code
- [ ] Installation package
- [ ] Release notes
- [ ] Integration guide

#### Acceptance Criteria
- ✅ No linter errors
- ✅ All dependencies up-to-date
- ✅ Installable via pip
- ✅ Works with Claude Desktop
- ✅ Documentation complete

---

### Phase 8 Completion Checklist

**Final Release Checklist:**
- [ ] All tests pass (unit + integration)
- [ ] Code coverage > 90%
- [ ] Documentation complete
- [ ] Examples provided
- [ ] Performance targets met
- [ ] No known bugs
- [ ] Installable via pip
- [ ] Works with Claude Desktop
- [ ] Release notes written
- [ ] License file included
- [ ] Contributing guide available

**Phase 8 Exit Criteria:**
✅ Production-ready code  
✅ Comprehensive documentation  
✅ All tests passing  
✅ Performance optimized  
✅ Ready for release  

---

## Release Criteria

Before releasing v1.0, ensure:

### Functionality
- ✅ All 6 MCP tools working
- ✅ Can parse resume.md and job.md
- ✅ Match scoring accurate
- ✅ Customization quality high
- ✅ PDF and DOCX generation working
- ✅ No fabricated information

### Quality
- ✅ Test coverage > 90%
- ✅ No critical bugs
- ✅ Performance < 30 seconds end-to-end
- ✅ Memory usage reasonable
- ✅ API costs < $0.10 per customization

### Documentation
- ✅ User guide complete
- ✅ Developer docs complete
- ✅ Examples provided
- ✅ Installation guide clear
- ✅ Troubleshooting guide available

### Integration
- ✅ Works with Claude Desktop
- ✅ Works with MCP inspector
- ✅ Config template provided
- ✅ Installation tested

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 1. Foundation | Week 1 | Parsers, models, MCP scaffold |
| 2. Matching | Week 2 | Match scoring, achievement ranking |
| 3. AI Integration | Week 3 | Claude API, keyword extraction, summaries |
| 4. Customization | Week 4 | Resume customization engine |
| 5. Generation | Week 5 | PDF/DOCX generation, templates |
| 6. MCP Tools | Week 6 | All 6 tools, error handling |
| 7. Storage | Week 7 | Database, history, caching |
| 8. Polish | Week 8 | Testing, docs, optimization |

**Total: 8 weeks (280-320 hours)**

---

## Risk Management

### High-Risk Items
1. **WeasyPrint PDF Generation** - May have font/rendering issues
   - Mitigation: Test early, have fallback template
   
2. **Claude API Costs** - Could exceed budget
   - Mitigation: Aggressive caching, fallback to spaCy

3. **Match Score Accuracy** - May not align with human judgment
   - Mitigation: Validate with real users, tune weights

### Medium-Risk Items
1. **MCP Protocol Changes** - Protocol may evolve
   - Mitigation: Follow MCP updates, version pinning

2. **Performance** - May not meet < 30s target
   - Mitigation: Profile early, optimize incrementally

---

## Success Metrics

**Development Success:**
- ✅ All phases completed on time
- ✅ Test coverage > 90%
- ✅ No critical bugs in release
- ✅ Documentation complete

**Product Success:**
- ✅ Users can customize resumes in < 5 minutes
- ✅ Match scores correlate with human judgment
- ✅ Generated resumes look professional
- ✅ No fabricated information in any output

**Technical Success:**
- ✅ End-to-end < 30 seconds
- ✅ API costs < $0.10 per customization
- ✅ Memory usage < 500MB
- ✅ Works reliably with Claude Desktop

---

## Appendix: Development Tools

### Required
- Python 3.10+
- pip
- git
- Claude Desktop (for testing)

### Recommended
- VS Code with Python extensions
- MCP Inspector
- DB Browser for SQLite
- Postman (for API testing)

### CI/CD (Future)
- GitHub Actions
- pytest
- black, ruff, mypy
- codecov

---

**Ready for Implementation!**

Follow this plan phase by phase, checking off items in the Technical Implementation Checklist as you complete them.
