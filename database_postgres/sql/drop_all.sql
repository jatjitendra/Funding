-- ApexFund — tear down every object this folder creates.
--
-- DESTRUCTIVE: drops all ApexFund tables and every row in them.
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/drop_all.sql
--
-- Roles survive on purpose: they are cluster-wide and may own objects in other
-- databases. Drop them by hand if you really mean to.

BEGIN;

DROP VIEW IF EXISTS vw_daily_sales;
DROP VIEW IF EXISTS vw_platform_stats;
DROP VIEW IF EXISTS vw_account_overview;

-- Child tables first; CASCADE also clears the dependent foreign keys.
DROP TABLE IF EXISTS payouts CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS contact_messages CASCADE;
DROP TABLE IF EXISTS plans CASCADE;
DROP TABLE IF EXISTS users CASCADE;

COMMIT;
