-- Create tomorrow's daily partition through the reusable helper function.
-- Safe to run multiple times.

SELECT public.ensure_inspection_records_partition((CURRENT_DATE + INTERVAL '1 day')::DATE);
