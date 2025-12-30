-- reset.sql
DO $$
DECLARE r record;
BEGIN
  -- drop tutte le tabelle dello schema public
  FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public')
  LOOP
    EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE', r.tablename);
  END LOOP;
END $$;