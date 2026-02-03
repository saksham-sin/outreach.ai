# Manual Testing Guide for Reliability Fixes

This guide provides step-by-step instructions for manually testing the reliability fixes, including race conditions and edge cases.

## Prerequisites

- Backend running locally (uvicorn)
- Database access (psql or DBeaver)
- Campaign with leads in ACTIVE status

---

## Test 1: Reply/Send Race Condition

**Goal:** Verify that follow-ups are blocked if a lead becomes "replied" between validation and send.

### Setup
1. Start the backend:
   ```powershell
   cd backend
   uvicorn app.main:app --reload
   ```

2. Create a campaign with 2-step sequence via UI
3. Launch the campaign
4. Note the campaign_id and a lead_id from the logs

### Manual Test Execution

**Option A: Using Database Directly**
1. Wait for a follow-up job to be scheduled (check `email_jobs` table)
2. Find a pending follow-up job:
   ```sql
   SELECT id, lead_id, step_number, status, scheduled_at 
   FROM email_jobs 
   WHERE status = 'pending' AND step_number > 1
   LIMIT 1;
   ```

3. Right before the job executes (watch worker logs), mark the lead as replied:
   ```sql
   UPDATE leads 
   SET status = 'replied', updated_at = NOW()
   WHERE id = '<lead_id_from_step_2>';
   ```

4. **Expected Result:**
   - Worker log shows: `Job {job_id} skipped at final validation: Lead is in terminal state: replied`
   - Job status becomes `SKIPPED`
   - Email is NOT sent

**Option B: Using Simulated Reply Endpoint**
1. Set `VITE_ENABLE_SIMULATED_REPLY=true` in frontend `.env`
2. In campaign detail page, click "Mark as Replied" on a lead with pending follow-up
3. Watch worker logs

4. **Expected Result:**
   - Next follow-up job for that lead is skipped
   - Log shows terminal state check blocked the send

### Verification Queries
```sql
-- Check job was skipped (not sent)
SELECT id, status, last_error 
FROM email_jobs 
WHERE lead_id = '<lead_id>' AND step_number > 1;

-- Verify lead status
SELECT id, email, status FROM leads WHERE id = '<lead_id>';
```

---

## Test 2: Concurrent Worker Claim Prevention

**Goal:** Verify FOR UPDATE SKIP LOCKED prevents duplicate sends.

### Setup (Multi-Process Test)
1. Start first backend instance:
   ```powershell
   uvicorn app.main:app --port 8000
   ```

2. Start second backend instance:
   ```powershell
   uvicorn app.main:app --port 8001
   ```

3. Both workers will poll the same database

### Manual Test Execution
1. Create campaign with 10+ leads
2. Launch campaign (schedule all jobs to send "now")
3. Watch logs from both terminals simultaneously

4. **Expected Result:**
   - Jobs are claimed by only ONE worker at a time
   - No duplicate `sent_at` timestamps for same job
   - Each job appears in only one worker's logs

### Verification Query
```sql
-- Check for duplicate sends (should return 0 rows)
SELECT lead_id, step_number, COUNT(*) as send_count
FROM email_jobs
WHERE status = 'sent'
GROUP BY lead_id, step_number
HAVING COUNT(*) > 1;

-- Verify job distribution (both workers should have processed some)
SELECT COUNT(*) FROM email_jobs WHERE status = 'sent';
```

---

## Test 3: Provider Exception Handling

**Goal:** Verify exceptions from email provider are caught and retried.

### Setup
1. **Temporarily break** the email provider by setting invalid API key:
   ```env
   RESEND_API_KEY=invalid-token-12345
   ```

2. Restart backend
3. Create and launch a campaign

### Manual Test Execution
1. Watch worker logs for send attempts
2. **Expected Result:**
   - Log shows: `Exception during send for job {id}: <provider error>`
   - Job attempts counter increments
   - Job remains in `PENDING` status for retry
   - Job is NOT stuck forever

### Verification Query
```sql
-- Check job is being retried (attempts > 0, still pending)
SELECT id, attempts, status, last_error, scheduled_at
FROM email_jobs
WHERE status = 'pending' AND attempts > 0
ORDER BY updated_at DESC
LIMIT 5;
```

3. Fix the API key and restart
4. Verify jobs eventually send successfully

---

## Test 4: Missing Resend Inbound Address

**Goal:** Verify app starts without crash when inbound address is missing.

### Setup
1. Clear the inbound address in `.env`:
   ```env
   RESEND_INBOUND_ADDRESS=
   ```

2. Start backend and watch startup logs

### Expected Result
```
WARNING - RESEND_INBOUND_ADDRESS not set - reply detection disabled. 
Set this to enable webhook-based reply detection.
```

3. Send a test email via campaign
4. **Expected Result:**
   - Email sends successfully
   - No `ReplyTo` header is set (check email received)
   - No crash or exception

---

## Test 5: Config Validation Warnings

**Goal:** Verify all config issues are logged at startup.

### Setup
1. Create a minimal `.env` with missing values:
   ```env
   DATABASE_URL=<valid-url>
   SECRET_KEY=test-key
   RESEND_API_KEY=
   RESEND_INBOUND_ADDRESS=
   OPENAI_API_KEY=
   ```

2. Start backend

### Expected Warnings in Logs
```
WARNING - RESEND_API_KEY not set - email sending will fail
WARNING - RESEND_INBOUND_ADDRESS not set - reply detection disabled. Set this to enable webhook-based reply detection.
WARNING - OPENAI_API_KEY not set - AI email generation will fail
INFO - Configuration validation complete
```

**Verification:**
- App still starts (doesn't crash)
- All missing configs are logged
- Feature degradation is clear

---

## Test 6: Max Retry Enforcement

**Goal:** Verify jobs are marked FAILED after max retry attempts.

### Setup
1. Set `MAX_RETRY_ATTEMPTS=3` in config (if not already)
2. Use invalid API key to force failures
3. Create small campaign (1 lead)

### Manual Test Execution
1. Launch campaign
2. Watch worker logs for 3 failed attempts
3. **Expected Result:**
   - Attempt 1: Job scheduled for retry (delay: 1 min)
   - Attempt 2: Job scheduled for retry (delay: 5 min)
   - Attempt 3: Job marked as FAILED

### Verification Query
```sql
-- Check job reached FAILED status
SELECT id, attempts, status, last_error
FROM email_jobs
WHERE status = 'failed'
ORDER BY updated_at DESC
LIMIT 1;

-- Verify lead is also marked failed
SELECT l.id, l.email, l.status
FROM leads l
JOIN email_jobs j ON j.lead_id = l.id
WHERE j.status = 'failed';
```

---

## Test 7: Campaign Pause During Job Execution

**Goal:** Verify paused campaigns don't send pending jobs.

### Setup
1. Create campaign with delayed follow-up (e.g., 1 hour delay)
2. Launch campaign
3. Wait for first email to send

### Manual Test Execution
1. Pause campaign via UI
2. Manually update follow-up job to be due:
   ```sql
   UPDATE email_jobs
   SET scheduled_at = NOW() - INTERVAL '1 minute'
   WHERE campaign_id = '<campaign_id>' AND step_number = 2;
   ```

3. Wait for worker to process (5-10 seconds)

4. **Expected Result:**
   - Log shows: `Job {id} skipped: Campaign is not active: paused`
   - Job status becomes `SKIPPED`
   - Email is NOT sent

---

## Debugging Tips

### Enable Debug Logging
```python
# In app/main.py, change:
logging.basicConfig(level=logging.DEBUG, ...)
```

### Watch Worker Loop in Real-Time
```powershell
# Filter worker logs
uvicorn app.main:app --log-level debug 2>&1 | Select-String "worker|job"
```

### Query Job Lifecycle
```sql
-- See all jobs for a campaign with timeline
SELECT 
    id,
    step_number,
    status,
    attempts,
    scheduled_at,
    sent_at,
    last_error,
    created_at,
    updated_at
FROM email_jobs
WHERE campaign_id = '<campaign_id>'
ORDER BY step_number, created_at;
```

### Check for Race Condition Evidence
```sql
-- Find jobs that were skipped due to terminal state
SELECT id, lead_id, step_number, last_error
FROM email_jobs
WHERE status = 'skipped' 
  AND last_error LIKE '%terminal state%';
```

---

## Success Criteria Summary

| Test | Success Indicator |
|------|------------------|
| **Race Condition** | Follow-up skipped when lead marked replied mid-flight |
| **Concurrent Claims** | Zero duplicate sends in multi-worker scenario |
| **Exception Handling** | Provider errors trigger retry, not permanent stuck state |
| **Missing Config** | App starts with warnings, features gracefully disabled |
| **Config Validation** | All missing values logged clearly at startup |
| **Max Retries** | Jobs transition to FAILED after 3 attempts |
| **Pause Safety** | Paused campaigns don't send pending jobs |

---

## Automated Test Suite

For full coverage including unit tests:

```powershell
# Requires virtual environment with dependencies
cd backend
python test_reliability_fixes.py
```

This runs:
- Atomic job claiming tests
- Reply/send race simulation
- Provider exception handling
- Config validation tests
- Resend inbound guard tests
- Concurrent worker simulation
