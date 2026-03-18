# Phase 7 Implementation Context

This file provides the complete context needed to implement Phase 7 (Storage & History) after clearing the conversation.

## Quick Start Prompt

```
I'm continuing work on the Resume Customizer MCP Server project. I need to implement Phase 7 (Storage & History).

Please read these files in order:
1. PHASE7_CONTEXT.md (this file - overview and context)
2. .claude/init.md (working style guidelines)
3. docs/IMPLEMENTATION_CHECKLIST.md (focus on Phase 7 section)
4. src/resume_customizer/storage/database.py (existing implementation from Phase 6)
5. src/resume_customizer/mcp/handlers.py (current MCP handlers)
6. src/resume_customizer/core/models.py (data models)

After reading, let's start with Phase 7.1: Database Schema & Implementation.

Key points:
- Phases 1-6 are complete with 48/48 tests passing
- Phase 6 already has basic SQLite database (customizations table)
- Phase 7 needs to expand database with profiles, jobs, match_results tables
- Follow concise response format from .claude/init.md
- All new code must have tests with >80% coverage
```

---

## Phase 7 Overview

**Goal**: Implement comprehensive storage, history tracking, session management, and caching.

**Phases**:
- **7.1**: Database Schema & Implementation - Expand database with new tables and operations
- **7.2**: Session Management - In-memory state tracking across tool calls
- **7.3**: History & Retrieval - Query, analytics, and export functionality
- **7.4**: Caching Strategy - Cache API responses and parsed data

---

## What's Already Done (Phase 6)

### Existing Database Implementation
Located in: `src/resume_customizer/storage/database.py`

**Current Features**:
- SQLite database with `customizations` table
- Basic CRUD operations for customizations
- Filtering by company, date range
- Auto-save on customize_resume
- Context manager support

**Current Schema**:
```sql
CREATE TABLE customizations (
    customization_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    profile_name TEXT NOT NULL,
    job_title TEXT NOT NULL,
    company TEXT NOT NULL,
    overall_score INTEGER NOT NULL,
    template TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT
)
```

**Indexes**:
- `idx_company` on company
- `idx_created_at` on created_at
- `idx_profile_id` on profile_id
- `idx_job_id` on job_id

### Existing Session State
Located in: `src/resume_customizer/mcp/handlers.py`

**Current Implementation**:
```python
_session_state: dict[str, Any] = {
    "profiles": {},      # profile_id -> UserProfile
    "jobs": {},          # job_id -> JobDescription
    "matches": {},       # match_id -> MatchResult
    "customizations": {} # customization_id -> CustomizedResume
}
```

**Usage**:
- Module-level dictionary stores loaded data
- Used across all MCP handler functions
- Cleared in tests via fixtures

---

## Phase 7.1: Database Schema & Implementation

### Goal
Expand the existing database with new tables for profiles, jobs, and match_results. Add advanced operations and make it production-ready.

### New Tables to Add

#### 1. profiles table
```sql
CREATE TABLE profiles (
    profile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    location TEXT,
    linkedin TEXT,
    github TEXT,
    website TEXT,
    summary TEXT,
    skills_count INTEGER,
    experiences_count INTEGER,
    education_count INTEGER,
    certifications_count INTEGER,
    full_data TEXT NOT NULL,  -- JSON serialized UserProfile
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

#### 2. jobs table
```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    job_type TEXT,
    experience_level TEXT,
    salary_range TEXT,
    required_skills_count INTEGER,
    preferred_skills_count INTEGER,
    full_data TEXT NOT NULL,  -- JSON serialized JobDescription
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

#### 3. match_results table
```sql
CREATE TABLE match_results (
    match_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL,
    job_id TEXT NOT NULL,
    overall_score INTEGER NOT NULL,
    technical_score INTEGER NOT NULL,
    experience_score INTEGER NOT NULL,
    domain_score INTEGER NOT NULL,
    keyword_coverage INTEGER NOT NULL,
    matched_skills_count INTEGER NOT NULL,
    missing_skills_count INTEGER NOT NULL,
    full_data TEXT NOT NULL,  -- JSON serialized MatchResult
    created_at TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
)
```

### Tasks for 7.1

1. **Expand Database Class**
   - Add methods for profile CRUD: `insert_profile()`, `get_profile()`, `update_profile()`, `delete_profile()`
   - Add methods for job CRUD: `insert_job()`, `get_job()`, `update_job()`, `delete_job()`
   - Add methods for match CRUD: `insert_match()`, `get_match()`, `delete_match()`
   - Add transaction support with context manager
   - Add batch operations for efficiency

2. **Schema Migrations**
   - Check if new tables exist on init
   - Create tables if missing (backward compatible)
   - Add indexes for performance:
     - `idx_profiles_email` on profiles.email
     - `idx_jobs_company` on jobs.company
     - `idx_matches_score` on match_results.overall_score
     - `idx_matches_profile` on match_results.profile_id
     - `idx_matches_job` on match_results.job_id

3. **Update Handlers**
   - Modify `handle_load_user_profile()` to save profile to database
   - Modify `handle_load_job_description()` to save job to database
   - Modify `handle_analyze_match()` to save match_result to database
   - Keep session state for fast access, database for persistence

4. **Testing**
   - Test all new CRUD operations
   - Test schema migration (creating tables)
   - Test transactions and rollback
   - Test concurrent access
   - Test foreign key constraints
   - Achieve >80% coverage for new code

### Expected Files to Modify
- `src/resume_customizer/storage/database.py` (expand class)
- `src/resume_customizer/mcp/handlers.py` (add database saves)
- `tests/test_database.py` (add new tests)

---

## Phase 7.2: Session Management

### Goal
Formalize session management with lifecycle, cleanup, and state tracking.

### Current State
Session state is currently a module-level dict in handlers.py. This works but needs improvement:
- No session lifecycle
- No memory management
- No automatic cleanup
- No session metadata

### New Implementation

#### Session Class
Create `src/resume_customizer/storage/session.py`:

```python
class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.profiles: dict[str, UserProfile] = {}
        self.jobs: dict[str, JobDescription] = {}
        self.matches: dict[str, MatchResult] = {}
        self.customizations: dict[str, CustomizedResume] = {}

    def update_access_time(self):
        self.last_accessed = datetime.now()

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        elapsed = (datetime.now() - self.last_accessed).total_seconds()
        return elapsed > ttl_seconds
```

#### SessionManager Class
```python
class SessionManager:
    def __init__(self, cleanup_interval: int = 300):
        self._sessions: dict[str, Session] = {}
        self._cleanup_interval = cleanup_interval

    def get_or_create_session(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id)
        session = self._sessions[session_id]
        session.update_access_time()
        return session

    def cleanup_expired_sessions(self, ttl_seconds: int = 3600):
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired(ttl_seconds)
        ]
        for sid in expired:
            del self._sessions[sid]
```

### Tasks for 7.2

1. **Create Session Classes**
   - Implement `Session` class with state storage
   - Implement `SessionManager` with lifecycle management
   - Add session metadata (created_at, last_accessed)
   - Add TTL and expiration logic

2. **Update Handlers**
   - Replace module-level `_session_state` with `SessionManager`
   - Add session_id parameter to handlers (optional, default to "default")
   - Update all handlers to use session manager
   - Maintain backward compatibility

3. **Add Cleanup**
   - Implement periodic cleanup task
   - Add memory usage tracking
   - Add session statistics

4. **Testing**
   - Test session creation and retrieval
   - Test state persistence across calls
   - Test session expiration
   - Test cleanup
   - Test concurrent sessions
   - Achieve >80% coverage

### Expected Files to Create
- `src/resume_customizer/storage/session.py`
- `tests/test_session.py`

### Expected Files to Modify
- `src/resume_customizer/mcp/handlers.py` (use SessionManager)

---

## Phase 7.3: History & Retrieval

### Goal
Add advanced query capabilities, analytics, and data export.

### New Functionality

#### 1. Advanced Queries
Add methods to `CustomizationDatabase`:

```python
def get_customizations_by_score_range(
    self, min_score: int, max_score: int
) -> list[dict]:
    """Query customizations by match score range."""

def get_customizations_by_company(
    self, company: str, limit: int = 10
) -> list[dict]:
    """Get all customizations for a company (already exists, enhance)."""

def search_customizations(
    self, keyword: str, fields: list[str] = None
) -> list[dict]:
    """Full-text search in customization data."""
```

#### 2. Analytics
```python
def get_analytics(
    self, start_date: str = None, end_date: str = None
) -> dict[str, Any]:
    """
    Get analytics summary.

    Returns:
        {
            "total_customizations": int,
            "average_score": float,
            "top_companies": list[tuple[str, int]],
            "score_distribution": dict[str, int],
            "success_rate": float,  # % with score > 70
        }
    """

def get_skill_gaps(
    self, start_date: str = None, end_date: str = None
) -> dict[str, int]:
    """Get most frequently missing skills."""
```

#### 3. Data Export
```python
def export_to_json(
    self, output_file: str, filters: dict = None
) -> None:
    """Export customizations to JSON."""

def export_to_csv(
    self, output_file: str, filters: dict = None
) -> None:
    """Export customizations to CSV."""
```

#### 4. New MCP Tool: get_history_analytics
Add to handlers.py:

```python
def handle_get_history_analytics(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Get analytics about customization history.

    Arguments:
        start_date (str, optional): Start date (ISO format)
        end_date (str, optional): End date (ISO format)

    Returns:
        Analytics summary with statistics
    """
```

### Tasks for 7.3

1. **Implement Queries**
   - Add score range filtering
   - Add full-text search
   - Add compound filters (AND/OR)
   - Optimize with indexes

2. **Implement Analytics**
   - Add `get_analytics()` method
   - Add `get_skill_gaps()` method
   - Calculate aggregates efficiently
   - Return actionable insights

3. **Implement Export**
   - Add JSON export with pretty formatting
   - Add CSV export with headers
   - Support filtering in exports
   - Include metadata in exports

4. **Add MCP Tool**
   - Create `handle_get_history_analytics()` handler
   - Register in MCP server
   - Add to tool registry
   - Document in tool descriptions

5. **Testing**
   - Test all query variations
   - Test analytics accuracy
   - Test exports (JSON, CSV)
   - Test with large datasets
   - Achieve >80% coverage

### Expected Files to Modify
- `src/resume_customizer/storage/database.py` (add methods)
- `src/resume_customizer/mcp/handlers.py` (add analytics tool)
- `src/resume_customizer/mcp/server.py` (register new tool)
- `tests/test_database.py` (add query/analytics tests)

---

## Phase 7.4: Caching Strategy

### Goal
Reduce API calls and improve performance by caching parsed data and API responses.

### What to Cache

1. **Parsed Files**: Resume and job markdown parsing results
2. **AI Responses**: Summary generation, customization suggestions
3. **Match Results**: Expensive skill matching calculations
4. **External Data**: Any fetched resources

### Implementation

#### Cache Class
Create `src/resume_customizer/utils/cache.py`:

```python
class Cache:
    def __init__(self, cache_dir: str = ".cache", default_ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0}

    def get(self, key: str) -> Any | None:
        """Get cached value by key."""

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set cached value with TTL."""

    def delete(self, key: str) -> None:
        """Delete cached value."""

    def clear(self) -> None:
        """Clear all cached values."""

    def cleanup_expired(self) -> int:
        """Remove expired entries, return count."""

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics."""
```

#### Cache Key Generation
```python
def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate deterministic cache key.

    Example:
        generate_cache_key("resume", file_path)
        -> "resume_abc123def456"
    """
    data = json.dumps([args, sorted(kwargs.items())], sort_keys=True)
    hash_val = hashlib.md5(data.encode()).hexdigest()
    return f"{prefix}_{hash_val}"
```

### Where to Add Caching

1. **parse_resume()** - Cache by file path + mtime
2. **parse_job_description()** - Cache by file path + mtime
3. **calculate_match_score()** - Cache by profile_id + job_id
4. **AI service calls** - Cache by prompt hash
5. **Database queries** - Cache frequent queries

### Tasks for 7.4

1. **Implement Cache Class**
   - File-based storage with pickle/json
   - TTL support with expiration metadata
   - LRU eviction when size limit reached
   - Thread-safe operations
   - Statistics tracking

2. **Add Cache to Parsers**
   - Wrap `parse_resume()` with cache decorator
   - Wrap `parse_job_description()` with cache decorator
   - Cache key includes file mtime for invalidation
   - Add cache control arguments (bypass_cache)

3. **Add Cache to AI Service**
   - Cache summary generation by input hash
   - Cache achievement optimization by input hash
   - Add cache control in AI service
   - Shorter TTL for AI responses (1 hour)

4. **Add Cache to Matcher**
   - Cache match results by profile_id + job_id
   - Invalidate on profile/job updates
   - Add cache statistics to match result

5. **Add Cache Management**
   - Background cleanup task
   - Size-based eviction
   - Manual clear command
   - Cache statistics reporting

6. **Testing**
   - Test cache hit/miss
   - Test TTL expiration
   - Test LRU eviction
   - Test thread safety
   - Test statistics accuracy
   - Measure performance improvement
   - Achieve >80% coverage

### Expected Files to Create
- `src/resume_customizer/utils/cache.py`
- `tests/test_cache.py`

### Expected Files to Modify
- `src/resume_customizer/parsers/markdown_parser.py` (add caching)
- `src/resume_customizer/core/matcher.py` (add caching)
- `src/resume_customizer/core/ai_service.py` (add caching)

---

## Key Dependencies

### Existing Code to Understand

1. **Data Models** (`src/resume_customizer/core/models.py`):
   - `UserProfile`, `JobDescription`, `MatchResult`, `CustomizedResume`
   - All have `to_dict()` methods for JSON serialization
   - Need `from_dict()` methods for deserialization (add if missing)

2. **Database** (`src/resume_customizer/storage/database.py`):
   - `CustomizationDatabase` class with SQLite
   - `insert_customization()`, `get_customizations()`, `get_by_id()`, `delete_customization()`
   - Context manager support (`__enter__`, `__exit__`)

3. **Handlers** (`src/resume_customizer/mcp/handlers.py`):
   - Module-level `_session_state` dict
   - `handle_load_user_profile()`, `handle_load_job_description()`, `handle_analyze_match()`
   - `handle_customize_resume()`, `handle_list_customizations()`
   - Error handling with custom exceptions

4. **Parsers** (`src/resume_customizer/parsers/markdown_parser.py`):
   - `parse_resume(file_path: str) -> UserProfile`
   - `parse_job_description(file_path: str) -> JobDescription`

5. **Matcher** (`src/resume_customizer/core/matcher.py`):
   - `calculate_match_score(profile: UserProfile, job: JobDescription) -> MatchResult`

6. **AI Service** (`src/resume_customizer/core/ai_service.py`):
   - `generate_summary(profile: UserProfile, job: JobDescription) -> str`
   - Uses Anthropic Claude API

### Testing Infrastructure

- **pytest** with fixtures
- **tmp_path** fixture for database tests
- **autouse fixture** in integration tests for cleanup
- Test files in `tests/` directory
- Fixtures in `tests/fixtures/`

### Quality Standards

- Type hints required (mypy)
- Google-style docstrings
- Ruff linting
- >80% test coverage
- No failing tests before commit

---

## Success Criteria for Phase 7

### Phase 7.1 Complete When:
- ✅ New tables (profiles, jobs, match_results) created
- ✅ All CRUD operations implemented and tested
- ✅ Schema migration works (creates tables if missing)
- ✅ Handlers save data to database
- ✅ All tests passing, >80% coverage
- ✅ No data loss or corruption

### Phase 7.2 Complete When:
- ✅ Session and SessionManager classes implemented
- ✅ Handlers use SessionManager instead of module dict
- ✅ Session expiration and cleanup working
- ✅ Memory management effective
- ✅ All tests passing, >80% coverage
- ✅ No memory leaks

### Phase 7.3 Complete When:
- ✅ Advanced queries implemented (score range, search)
- ✅ Analytics methods working (stats, skill gaps)
- ✅ Export functions working (JSON, CSV)
- ✅ New MCP tool for analytics registered
- ✅ All tests passing, >80% coverage
- ✅ Analytics provide actionable insights

### Phase 7.4 Complete When:
- ✅ Cache class implemented with TTL and LRU
- ✅ Parsers use caching
- ✅ AI service uses caching
- ✅ Matcher uses caching
- ✅ Cache statistics available
- ✅ Performance improved (measure API call reduction)
- ✅ All tests passing, >80% coverage

### Overall Phase 7 Complete When:
- ✅ All 4 sub-phases complete
- ✅ All tests passing (expect 60+ tests total)
- ✅ Documentation updated
- ✅ IMPLEMENTATION_CHECKLIST.md marked complete
- ✅ Committed to git with proper commit message

---

## Working Style Reminders

From `.claude/init.md`:

### DO:
- ✅ Be concise - no summaries unless asked
- ✅ Report completion with test results only
- ✅ Use TodoWrite to track progress
- ✅ Fix all linter/type errors immediately
- ✅ Run tests after each change
- ✅ Commit with proper message format (no attribution footer)

### DON'T:
- ❌ Create summaries or "What We Built" sections
- ❌ Suggest "Next Steps"
- ❌ Create new documentation unless asked
- ❌ Include usage examples in responses
- ❌ Add verbose explanations

### Commit Format:
```
feat(storage): implement Phase 7.1 - database schema expansion

Added profiles, jobs, and match_results tables with CRUD operations.

- Created schema migrations
- Added transaction support
- Updated handlers to save to database
- Added 20 new database tests

Tests: 68/68 passing
Coverage: 52%
```

**NO attribution footer** - do not include:
```
🤖 Generated with [Claude Code](...)
Co-Authored-By: Claude Sonnet 4.5 <...>
```

---

## Files to Reference

### Must Read:
1. `.claude/init.md` - Working style
2. `docs/IMPLEMENTATION_CHECKLIST.md` - Phase 7 tasks
3. `src/resume_customizer/storage/database.py` - Existing database
4. `src/resume_customizer/mcp/handlers.py` - Current handlers
5. `src/resume_customizer/core/models.py` - Data models

### May Need:
6. `src/resume_customizer/parsers/markdown_parser.py` - For caching
7. `src/resume_customizer/core/matcher.py` - For caching
8. `src/resume_customizer/core/ai_service.py` - For caching
9. `tests/test_database.py` - Existing database tests
10. `tests/test_mcp_integration.py` - Integration test patterns

---

## Estimated Effort

- **Phase 7.1**: ~2 hours (database expansion)
- **Phase 7.2**: ~1 hour (session management)
- **Phase 7.3**: ~2 hours (history & analytics)
- **Phase 7.4**: ~2 hours (caching)

**Total**: ~7 hours for complete Phase 7 implementation

---

## Ready to Start?

Use this prompt after clearing conversation:

```
I'm continuing work on the Resume Customizer MCP Server project. I need to implement Phase 7 (Storage & History).

Please read these files in order:
1. PHASE7_CONTEXT.md
2. .claude/init.md
3. docs/IMPLEMENTATION_CHECKLIST.md (Phase 7 section)
4. src/resume_customizer/storage/database.py
5. src/resume_customizer/mcp/handlers.py
6. src/resume_customizer/core/models.py

Let's start with Phase 7.1: Database Schema & Implementation.

Follow the concise response format from .claude/init.md - no summaries, just implementation and test results.
```
