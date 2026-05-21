SELECT public.ensure_stage1_partition((CURRENT_DATE + INTERVAL '1 day')::DATE);
SELECT public.ensure_stage2_partition((CURRENT_DATE + INTERVAL '1 day')::DATE);

