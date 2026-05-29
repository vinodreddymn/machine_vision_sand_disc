SELECT public.ensure_inspection_records_partition((CURRENT_DATE + INTERVAL '1 day')::DATE);
