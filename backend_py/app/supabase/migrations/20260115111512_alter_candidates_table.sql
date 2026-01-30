-- Add status field to candidates table
ALTER TABLE candidates
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED'));

-- Add audit trail fields
ALTER TABLE candidates
ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS status_updated_by UUID REFERENCES auth.users(id);

-- Create index on status for faster queries
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);

-- Update existing records to have PENDING status
UPDATE candidates SET status = 'PENDING' WHERE status IS NULL;

