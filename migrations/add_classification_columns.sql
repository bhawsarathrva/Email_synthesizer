-- Migration: Add AI classification and Human-in-the-Loop verification columns
-- Target table: "Email_data" (preserves existing table and casing)

DO $$ 
BEGIN
    -- Check if table exists as "Email_data" or "emails"
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'Email_data') THEN
        ALTER TABLE "Email_data" 
            ADD COLUMN IF NOT EXISTS ai_category VARCHAR(50),
            ADD COLUMN IF NOT EXISTS ai_confidence DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS classification_reason TEXT,
            ADD COLUMN IF NOT EXISTS verified_category VARCHAR(50),
            ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS human_feedback TEXT,
            ADD COLUMN IF NOT EXISTS verified_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

        -- Create view 'emails' pointing to 'Email_data' with standardized column aliases if it doesn't already exist
        CREATE OR REPLACE VIEW emails AS
        SELECT 
            id,
            "From" AS sender,
            "To" AS recipient,
            "Subject" AS subject,
            "Body" AS body,
            COALESCE(ai_category, "Category") AS ai_category,
            ai_confidence,
            classification_reason,
            COALESCE(verified_category, "Category") AS verified_category,
            COALESCE(verification_status, CASE WHEN "Verified" IS NOT NULL AND "Verified" != '' THEN 'approved' ELSE 'pending' END) AS verification_status,
            human_feedback,
            verified_by,
            verified_at,
            received_at
        FROM "Email_data";

    ELSIF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'emails') THEN
        ALTER TABLE emails 
            ADD COLUMN IF NOT EXISTS ai_category VARCHAR(50),
            ADD COLUMN IF NOT EXISTS ai_confidence DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS classification_reason TEXT,
            ADD COLUMN IF NOT EXISTS verified_category VARCHAR(50),
            ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) DEFAULT 'pending',
            ADD COLUMN IF NOT EXISTS human_feedback TEXT,
            ADD COLUMN IF NOT EXISTS verified_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE,
            ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;
