-- Fix OAuth role enum issue
-- This script converts the role column to accept proper enum values

-- Step 1: Temporarily convert to VARCHAR to allow any value
ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50);

-- Step 2: Update any existing lowercase roles to uppercase
UPDATE users SET role = UPPER(role) 
WHERE role IN ('parent', 'admin', 'superuser', 'caregiver', 'therapist', 'educator');

-- Step 3: Recreate the enum type with proper values
DROP TYPE IF EXISTS userrole CASCADE;
CREATE TYPE userrole AS ENUM ('SUPERUSER', 'ADMIN', 'PARENT', 'CAREGIVER', 'THERAPIST', 'EDUCATOR');

-- Step 4: Convert the column back to enum type
ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole;

-- Allow null passwords for OAuth users
ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;
