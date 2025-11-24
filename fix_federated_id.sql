-- Drop primary key first if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'federated_identities_pkey') THEN
        ALTER TABLE federated_identities DROP CONSTRAINT federated_identities_pkey;
    END IF;
END $$;

-- Create a sequence for the ID
CREATE SEQUENCE IF NOT EXISTS federated_identities_id_seq;

-- Set the default value for id column
ALTER TABLE federated_identities ALTER COLUMN id SET DEFAULT nextval('federated_identities_id_seq');

-- Associate the sequence with the column
ALTER SEQUENCE federated_identities_id_seq OWNED BY federated_identities.id;

-- Update existing rows that have null id
UPDATE federated_identities SET id = nextval('federated_identities_id_seq') WHERE id IS NULL;

-- Now make it NOT NULL
ALTER TABLE federated_identities ALTER COLUMN id SET NOT NULL;

-- Add primary key
ALTER TABLE federated_identities ADD PRIMARY KEY (id);
