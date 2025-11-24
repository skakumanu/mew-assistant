-- Allow null passwords for OAuth users
ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;
