-- Fix UserRole enum to add 'parent' value if missing
DO $$ 
BEGIN
    -- Add 'parent' to userrole enum if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'parent' AND enumtypid = 'userrole'::regtype) THEN
        ALTER TYPE userrole ADD VALUE 'parent';
    END IF;
END $$;
