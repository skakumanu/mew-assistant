-- Add new roles to UserRole enum
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'superuser';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'kid';
