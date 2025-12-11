# Database Cleanup Guide

**Date:** December 11, 2025  
**Purpose:** Remove users created with compromised passwords  
**Related:** SECURITY_INCIDENT.md

---

## Overview

This guide helps you safely remove users that were created with hardcoded passwords exposed in git history, while preserving OAuth federated users.

---

## Step 1: Check Current Users

### SQL Query to List All Users:

```sql
-- Show all users with their authentication method
SELECT 
    u.id,
    u.email,
    u.username,
    u.role,
    u.is_active,
    u.created_at,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM federated_identities fi 
            WHERE fi.user_id = u.id
        ) 
        THEN 'OAuth'
        ELSE 'Password'
    END as auth_type
FROM users u
ORDER BY u.created_at DESC;
```

**Expected Output:**
- OAuth users (Google/Microsoft): **KEEP**
- Password users with compromised credentials: **REMOVE**

---

## Step 2: Identify Users to Remove

### Users Created with Compromised Passwords:

1. **super@mew-assistant.org**
   - Password: `SuperSecure123!` (COMPROMISED)
   - Role: SUPERUSER
   - Action: Remove if no OAuth

2. **admin@mew-assistant.org**
   - Password: `AdminSecure123!` (COMPROMISED)
   - Role: ADMIN
   - Action: Remove if no OAuth

3. **skakumanu@gmail.com** (early password-based version)
   - Password: `Parent@Mew2024` or `Mew@Super2024!` (COMPROMISED)
   - Action: **KEEP** - Now has OAuth (Google)

4. **skakumanu@hotmail.com** (early password-based version)
   - Password: `Mew@Admin2024!` (COMPROMISED)
   - Action: **KEEP** - Now has OAuth (Microsoft)

---

## Step 3: Safe Deletion SQL

### Delete Password-Based Users (Preserve OAuth):

```sql
-- STEP 1: Check which users will be deleted (DRY RUN)
SELECT 
    u.id,
    u.email,
    u.role,
    'Will be DELETED' as action
FROM users u
WHERE u.email IN (
    'super@mew-assistant.org',
    'admin@mew-assistant.org'
)
AND NOT EXISTS (
    SELECT 1 FROM federated_identities fi 
    WHERE fi.user_id = u.id
);

-- STEP 2: Actually delete (ONLY IF dry run looks correct)
BEGIN;

-- Delete federated identities first (if any - shouldn't be for these users)
DELETE FROM federated_identities
WHERE user_id IN (
    SELECT u.id FROM users u
    WHERE u.email IN (
        'super@mew-assistant.org',
        'admin@mew-assistant.org'
    )
    AND NOT EXISTS (
        SELECT 1 FROM federated_identities fi2 
        WHERE fi2.user_id = u.id
    )
);

-- Delete users
DELETE FROM users
WHERE email IN (
    'super@mew-assistant.org',
    'admin@mew-assistant.org'
)
AND NOT EXISTS (
    SELECT 1 FROM federated_identities fi 
    WHERE fi.user_id = users.id
);

-- Check what was deleted
SELECT 
    'Deleted ' || COUNT(*) || ' users' as result
FROM users
WHERE FALSE; -- This will return 0, just for confirmation message

COMMIT;
-- Or ROLLBACK; if something looks wrong
```

---

## Step 4: Verify OAuth Users Are Intact

### SQL to Verify OAuth Users:

```sql
-- Should show your OAuth users
SELECT 
    u.email,
    u.role,
    fi.provider,
    fi.provider_user_id,
    u.created_at
FROM users u
INNER JOIN federated_identities fi ON fi.user_id = u.id
WHERE u.email IN (
    'skakumanu@gmail.com',
    'skakumanu@hotmail.com'
)
ORDER BY u.email;
```

**Expected Result:**
- skakumanu@gmail.com → provider: google
- skakumanu@hotmail.com → provider: microsoft

---

## Step 5: Verify Cleanup Complete

### Final Verification:

```sql
-- Should show NO password-based users with compromised emails
SELECT 
    u.email,
    u.role,
    CASE 
        WHEN EXISTS (SELECT 1 FROM federated_identities fi WHERE fi.user_id = u.id) 
        THEN 'OAuth ✅'
        ELSE 'Password ⚠️'
    END as auth_type
FROM users u
WHERE u.email IN (
    'super@mew-assistant.org',
    'admin@mew-assistant.org',
    'skakumanu@gmail.com',
    'skakumanu@hotmail.com'
);
```

**Expected Result:**
- skakumanu@gmail.com: OAuth ✅
- skakumanu@hotmail.com: OAuth ✅
- super@mew-assistant.org: (not found - deleted)
- admin@mew-assistant.org: (not found - deleted)

---

## How to Connect to Azure Database

### Option 1: Azure Portal Query Editor

1. Go to Azure Portal
2. Navigate to your PostgreSQL database
3. Click "Query editor"
4. Run the SQL queries above

### Option 2: Azure CLI + psql

```bash
# Get database connection details
az postgres flexible-server show \
  --name mew-assistant-db-dev \
  --resource-group mew-assistant-dev-rg

# Connect using psql
az postgres flexible-server connect \
  --name mew-assistant-db-dev \
  --admin-user mewadmin \
  --database-name mew_assistant
```

### Option 3: Container App Shell

```bash
# Connect to running container
az containerapp exec \
  --name mew-assistant-dev \
  --resource-group mew-assistant-dev-rg \
  --command /bin/bash

# Then run Python script inside container
python scripts/cleanup_compromised_users.py --live
```

---

## Safety Checklist

Before running DELETE commands:

- [ ] Backed up database (or can restore if needed)
- [ ] Ran DRY RUN query first
- [ ] Verified OAuth users will be preserved
- [ ] Confirmed only compromised password users will be deleted
- [ ] Ready to commit transaction

---

## Post-Cleanup Actions

After successful cleanup:

1. ✅ Update SECURITY_INCIDENT.md status
2. ✅ Verify OAuth login still works
3. ✅ Monitor for any issues
4. ✅ Document completion date

---

## Rollback Plan

If something goes wrong:

```sql
-- If still in transaction
ROLLBACK;

-- If already committed, you'll need to:
-- 1. Restore from backup, OR
-- 2. Recreate users with OAuth (they'll sign in and recreate)
```

Note: OAuth users will automatically recreate themselves on next login.

---

## Summary

**Safe to Delete:**
- super@mew-assistant.org (password-based)
- admin@mew-assistant.org (password-based)

**Must Preserve:**
- skakumanu@gmail.com (OAuth - Google)
- skakumanu@hotmail.com (OAuth - Microsoft)

**Result:** Compromised passwords removed, OAuth authentication intact.

---

**Created:** December 11, 2025  
**Last Updated:** December 11, 2025
