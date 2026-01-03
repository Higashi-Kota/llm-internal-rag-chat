-- RAG Chat Seed Data
-- Idempotent seed: safe to run multiple times

-- Currently no seed data required for this application
-- Add ON CONFLICT DO UPDATE patterns here if needed in the future

-- Example pattern for future use:
-- INSERT INTO some_table (id, name, value)
-- VALUES ('uuid-here', 'name', 'value')
-- ON CONFLICT (id) DO UPDATE SET
--     name = EXCLUDED.name,
--     value = EXCLUDED.value,
--     updated_at = NOW();

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Seed complete: no seed data required';
END $$;
