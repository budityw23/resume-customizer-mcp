# Phase 7 Manual Testing Guide

This guide provides step-by-step instructions to manually test all Phase 7 features: Database Persistence, Session Management, History & Retrieval, and Caching.

## Prerequisites

1. Ensure the MCP server is running
2. Have Claude Desktop or another MCP client connected
3. Have sample resume and job description files ready

## Test 1: Database Persistence (Phase 7.1)

### Test 1.1: Profile Storage

**Objective**: Verify profiles are saved to database automatically

1. Load a user profile:
   ```
   Load my profile from examples/resume.md
   ```

2. Check the database file was created:
   ```bash
   ls -la ~/.resume_customizer/customizations.db
   ```

3. Verify profile was saved:
   ```bash
   sqlite3 ~/.resume_customizer/customizations.db "SELECT profile_id, name, email FROM profiles;"
   ```

**Expected Result**: You should see the profile record with name and email.

### Test 1.2: Job Storage

**Objective**: Verify jobs are saved to database automatically

1. Load a job description:
   ```
   Load the job description from examples/job.md
   ```

2. Verify job was saved:
   ```bash
   sqlite3 ~/.resume_customizer/customizations.db "SELECT job_id, title, company FROM jobs;"
   ```

**Expected Result**: You should see the job record with title and company.

### Test 1.3: Match Results Storage

**Objective**: Verify match results are persisted

1. Analyze match between profile and job:
   ```
   Analyze the match between my profile and this job
   ```

2. Verify match result was saved:
   ```bash
   sqlite3 ~/.resume_customizer/customizations.db "SELECT match_id, overall_score, technical_score FROM match_results;"
   ```

**Expected Result**: You should see the match record with scores.

### Test 1.4: Customization Storage

**Objective**: Verify customizations are saved with metadata

1. Customize the resume:
   ```
   Customize my resume for this job
   ```

2. Verify customization was saved:
   ```bash
   sqlite3 ~/.resume_customizer/customizations.db "SELECT customization_id, profile_name, job_title, company, overall_score FROM customizations;"
   ```

**Expected Result**: You should see the customization record with all details.

### Test 1.5: Foreign Key Constraints

**Objective**: Verify data integrity through foreign keys

1. Try to delete a profile that has customizations:
   ```bash
   sqlite3 ~/.resume_customizer/customizations.db "DELETE FROM profiles WHERE profile_id = '<profile-id>';"
   ```

**Expected Result**: Should fail with foreign key constraint error.

## Test 2: Session Management (Phase 7.2)

### Test 2.1: Session Caching

**Objective**: Verify in-memory caching works

1. Load a profile (first time):
   ```
   Load my profile from examples/resume.md
   ```
   Note: Should read from file and cache.

2. Immediately reference the profile again:
   ```
   What's my name in the loaded profile?
   ```

**Expected Result**: Response should be instant (from cache, not re-reading file).

### Test 2.2: TTL Expiration

**Objective**: Verify session entries expire after TTL

1. Load a profile
2. Wait for 1 hour (or modify TTL in code for testing)
3. Try to use the profile

**Expected Result**: Profile should be reloaded from database after TTL expires.

### Test 2.3: Session Metrics

**Objective**: Verify session metrics are tracked

1. Perform multiple operations (load profile, job, analyze match)
2. Check session metrics in logs:
   ```bash
   grep "SessionManager" ~/.resume_customizer/logs/resume_customizer.log
   ```

**Expected Result**: Should see hit/miss tracking in logs.

## Test 3: History & Retrieval (Phase 7.3)

### Test 3.1: Query by Date Range

**Objective**: Test date range filtering

1. Create multiple customizations on different dates (modify created_at in DB if needed)
2. Run Python test script:

```python
from resume_customizer.storage.database import CustomizationDatabase

db = CustomizationDatabase()
results = db.query_customizations_by_date_range(
    start_date="2024-01-01T00:00:00Z",
    end_date="2024-12-31T23:59:59Z"
)
print(f"Found {len(results)} customizations")
for r in results:
    print(f"  - {r['created_at']}: {r['job_title']} at {r['company']}")
```

**Expected Result**: Only customizations within date range are returned.

### Test 3.2: Query by Score Range

**Objective**: Test score filtering

```python
from resume_customizer.storage.database import CustomizationDatabase

db = CustomizationDatabase()
results = db.query_customizations_by_score(min_score=80, max_score=100)
print(f"Found {len(results)} high-scoring customizations")
for r in results:
    print(f"  - Score {r['overall_score']}: {r['job_title']} at {r['company']}")
```

**Expected Result**: Only customizations with scores 80-100 are returned, ordered by score DESC.

### Test 3.3: Full-Text Search

**Objective**: Test search across customizations

```python
from resume_customizer.storage.database import CustomizationDatabase

db = CustomizationDatabase()
results = db.search_customizations("TechCorp")
print(f"Found {len(results)} customizations matching 'TechCorp'")
for r in results:
    print(f"  - {r['company']}: {r['job_title']}")
```

**Expected Result**: All customizations mentioning "TechCorp" in company, job title, or profile name.

### Test 3.4: Analytics Summary

**Objective**: Verify comprehensive analytics

```python
from resume_customizer.storage.database import CustomizationDatabase

db = CustomizationDatabase()
analytics = db.get_analytics_summary()

print(f"Total Customizations: {analytics['total_customizations']}")
print(f"Average Match Score: {analytics['avg_match_score']}")
print(f"\nTop Companies:")
for company in analytics['top_companies'][:5]:
    print(f"  - {company['company']}: {company['count']} customizations")

print(f"\nScore Distribution:")
print(f"  Excellent (90+): {analytics['score_distribution']['excellent_90_plus']}")
print(f"  Good (80-89): {analytics['score_distribution']['good_80_89']}")
print(f"  Fair (70-79): {analytics['score_distribution']['fair_70_79']}")
print(f"  Poor (<70): {analytics['score_distribution']['poor_below_70']}")
```

**Expected Result**: Accurate statistics for all customizations in database.

### Test 3.5: Skill Gap Analysis

**Objective**: Test skill gap trending

```python
from resume_customizer.storage.database import CustomizationDatabase

db = CustomizationDatabase()
trends = db.get_skill_gap_trends(limit=5)

print("Top 5 Missing Skills:")
for trend in trends:
    print(f"  - {trend['skill']}: mentioned in {trend['gap_count']} matches")
```

**Expected Result**: Top missing skills aggregated from all match results.

### Test 3.6: Export to JSON

**Objective**: Test JSON export with filters

```python
from resume_customizer.storage.database import CustomizationDatabase

db = CustomizationDatabase()
stats = db.export_to_json(
    output_path="/tmp/customizations_export.json",
    company="TechCorp",
    start_date="2024-01-01T00:00:00Z",
    end_date="2024-12-31T23:59:59Z"
)

print(f"Exported {stats['records_exported']} records")
print(f"File: {stats['output_path']}")
print(f"Size: {stats['file_size_bytes']} bytes")
```

Then verify the JSON file:
```bash
cat /tmp/customizations_export.json | jq '.analytics'
```

**Expected Result**:
- JSON file created with export_date, filters, analytics, and customizations
- Analytics summary included
- Only filtered records exported

### Test 3.7: Export to CSV

**Objective**: Test CSV export

```python
from resume_customizer.storage.database import CustomizationDatabase

db = CustomizationDatabase()
stats = db.export_to_csv(
    output_path="/tmp/customizations_export.csv",
    company="TechCorp"
)

print(f"Exported {stats['records_exported']} records to CSV")
```

Then verify the CSV:
```bash
head -20 /tmp/customizations_export.csv
```

**Expected Result**:
- CSV file with headers
- All filtered customizations
- Readable format (no JSON metadata column)

## Test 4: Multi-Layer Caching (Phase 7.4)

### Test 4.1: Cache Flow Verification

**Objective**: Verify multi-layer cache architecture

1. **First Request** (cold cache):
   ```
   Load my profile from examples/resume.md
   ```
   Check logs: Should see file read + session cache + database save

2. **Second Request** (session cache hit):
   ```
   What skills are in my profile?
   ```
   Check logs: Should see session cache hit (no file read)

3. **After Session Expiry** (database hit):
   - Wait for session TTL or restart server
   ```
   What skills are in my profile?
   ```
   Check logs: Should see database read (session miss, no file read)

4. **After Full Clear** (file read):
   - Clear database and session
   ```bash
   rm ~/.resume_customizer/customizations.db
   ```
   - Restart server
   ```
   What skills are in my profile?
   ```
   Check logs: Should see file read + cache saves

**Expected Result**: Cache layers working in order: Session → Database → File

### Test 4.2: Session Cache Statistics

**Objective**: Verify cache metrics are accurate

```python
from resume_customizer.storage.session import SessionManager

session = SessionManager(default_ttl=3600)

# Simulate cache operations
session.set_profile("test-1", {"name": "Test User 1"})
session.set_profile("test-2", {"name": "Test User 2"})
session.get_profile("test-1")  # hit
session.get_profile("test-1")  # hit
session.get_profile("nonexistent")  # miss

metrics = session.get_metrics()
print(f"Total Entries: {metrics.total_entries}")
print(f"Profiles: {metrics.profiles_count}")
print(f"Hit Count: {metrics.hit_count}")
print(f"Miss Count: {metrics.miss_count}")
print(f"Hit Rate: {metrics.hit_rate:.2%}")
```

**Expected Result**:
- total_entries = 2
- hit_count = 2
- miss_count = 1
- hit_rate = 66.67%

## Test 5: Integration Testing

### Test 5.1: Complete Workflow

**Objective**: Test all Phase 7 features in one workflow

1. **Load Profile**:
   ```
   Load my profile from examples/resume.md
   ```

2. **Load Multiple Jobs**:
   ```
   Load job from examples/job1.md
   Load job from examples/job2.md
   Load job from examples/job3.md
   ```

3. **Analyze Matches**:
   ```
   Analyze match between my profile and job-1
   Analyze match between my profile and job-2
   Analyze match between my profile and job-3
   ```

4. **Customize for Top Match**:
   ```
   Customize my resume for the highest scoring job
   ```

5. **Query History**:
   ```python
   from resume_customizer.storage.database import CustomizationDatabase

   db = CustomizationDatabase()

   # Get all customizations
   all_customizations = db.get_customizations()
   print(f"\nTotal Customizations: {len(all_customizations)}")

   # Get analytics
   analytics = db.get_analytics_summary()
   print(f"Average Score: {analytics['avg_match_score']}")

   # Get skill gaps
   gaps = db.get_skill_gap_trends()
   print(f"\nTop Skill Gaps: {[g['skill'] for g in gaps[:3]]}")

   # Export
   db.export_to_json("/tmp/my_customizations.json")
   print("\nExported to /tmp/my_customizations.json")
   ```

**Expected Result**: All operations succeed with data persisting correctly across database, session, and exports.

## Test 6: Error Handling

### Test 6.1: Database Failure Graceful Degradation

**Objective**: Verify system continues working if database fails

1. Make database read-only:
   ```bash
   chmod 444 ~/.resume_customizer/customizations.db
   ```

2. Try to load a profile:
   ```
   Load my profile from examples/resume.md
   ```

**Expected Result**:
- Warning logged about database save failure
- Profile still loads successfully (in session)
- No crash or user-facing error

3. Restore permissions:
   ```bash
   chmod 644 ~/.resume_customizer/customizations.db
   ```

### Test 6.2: Session Cleanup

**Objective**: Verify expired entries are cleaned up

```python
from resume_customizer.storage.session import SessionManager
import time

session = SessionManager(default_ttl=1)  # 1 second TTL

session.set_profile("test-1", {"name": "Test"})
print(f"Before expiry: {session.get_profile('test-1')}")

time.sleep(1.5)
print(f"After expiry: {session.get_profile('test-1')}")  # Should be None

# Check expired count
metrics = session.get_metrics()
print(f"Expired count: {metrics.expired_count}")
```

**Expected Result**:
- First get returns profile
- After TTL, get returns None
- expired_count increments

## Verification Checklist

After completing all tests, verify:

- [ ] Database file created at `~/.resume_customizer/customizations.db`
- [ ] All 4 tables exist (profiles, jobs, match_results, customizations)
- [ ] Indexes created for performance
- [ ] Foreign key constraints enforced
- [ ] Session caching reduces file/DB reads
- [ ] TTL expiration works correctly
- [ ] Date range queries return correct results
- [ ] Score filtering works accurately
- [ ] Full-text search finds matches
- [ ] Analytics provide accurate statistics
- [ ] Skill gap analysis identifies trends
- [ ] JSON export includes analytics
- [ ] CSV export is readable
- [ ] Multi-layer cache flows correctly
- [ ] Session metrics track hit/miss rates
- [ ] System gracefully handles database failures
- [ ] Expired sessions are cleaned up

## Automated Test Verification

Run the automated test suite to verify all functionality:

```bash
cd /path/to/resume-customizer-mcp-server
source venv/bin/activate
pytest tests/test_database.py tests/test_session.py tests/test_history.py -v
```

**Expected Result**: All 86 tests should pass.

## Performance Benchmarks

### Database Query Performance

```python
import time
from resume_customizer.storage.database import CustomizationDatabase

db = CustomizationDatabase()

# Benchmark date range query
start = time.time()
results = db.query_customizations_by_date_range(
    "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"
)
elapsed = time.time() - start
print(f"Date range query: {elapsed*1000:.2f}ms for {len(results)} records")

# Benchmark analytics
start = time.time()
analytics = db.get_analytics_summary()
elapsed = time.time() - start
print(f"Analytics summary: {elapsed*1000:.2f}ms")
```

**Expected Performance**:
- Date range query: < 50ms for 1000 records
- Analytics summary: < 100ms for 1000 records
- Search query: < 50ms for 1000 records

### Session Cache Performance

```python
import time
from resume_customizer.storage.session import SessionManager

session = SessionManager()

# Add 100 profiles
for i in range(100):
    session.set_profile(f"profile-{i}", {"name": f"User {i}"})

# Benchmark cache hit
start = time.time()
for i in range(100):
    session.get_profile(f"profile-{i}")
elapsed = time.time() - start
print(f"100 cache hits: {elapsed*1000:.2f}ms ({elapsed*10:.2f}ms per hit)")
```

**Expected Performance**:
- Cache hit: < 0.1ms per operation
- Cache miss: < 0.1ms per operation

## Troubleshooting

### Issue: Database file not created

**Solution**: Check permissions on `~/.resume_customizer/` directory:
```bash
mkdir -p ~/.resume_customizer
chmod 755 ~/.resume_customizer
```

### Issue: Foreign key constraint errors

**Solution**: Verify foreign keys are enabled:
```bash
sqlite3 ~/.resume_customizer/customizations.db "PRAGMA foreign_keys;"
```
Should return: `1`

### Issue: Session cache not working

**Solution**: Check logs for SessionManager initialization:
```bash
grep "SessionManager initialized" ~/.resume_customizer/logs/resume_customizer.log
```

### Issue: Export fails with directory error

**Solution**: Export methods create parent directories automatically. Check file permissions.

## Next Steps

After completing Phase 7 testing:
1. Review test coverage report
2. Address any failed tests
3. Document any issues found
4. Proceed to Phase 8: Testing, Documentation & Polish
