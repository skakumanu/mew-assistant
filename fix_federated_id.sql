-- Fix federated_identities table to have auto-generated ID
ALTER TABLE federated_identities ALTER COLUMN id SET DEFAULT nextval('federated_identities_id_seq');

-- Check if sequence exists, if not create it
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'federated_identities_id_seq') THEN
        CREATE SEQUENCE federated_identities_id_seq;
        ALTER TABLE federated_identities ALTER COLUMN id SET DEFAULT nextval('federated_identities_id_seq');
        -- Set sequence to start after current max id
        PERFORM setval('federated_identities_id_seq', COALESCE((SELECT MAX(id) FROM federated_identities), 0) + 1, false);
    END IF;
END $$;
