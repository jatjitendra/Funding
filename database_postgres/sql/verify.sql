-- ApexFund — post-apply verification
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/verify.sql
--
-- Reports anything expected but missing, then raises an exception so the script
-- exits non-zero in CI. Read-only otherwise.

\pset pager off

\echo '== Tables =='
SELECT expected.name AS table_name,
       CASE WHEN to_regclass('public.' || expected.name) IS NULL THEN 'MISSING' ELSE 'ok' END AS state
FROM (VALUES
    ('users'), ('plans'), ('accounts'), ('orders'), ('payouts'), ('contact_messages')
) AS expected(name)
ORDER BY 2 DESC, 1;

\echo '== Views =='
SELECT expected.name AS view_name,
       CASE WHEN to_regclass('public.' || expected.name) IS NULL THEN 'MISSING' ELSE 'ok' END AS state
FROM (VALUES
    ('vw_account_overview'), ('vw_platform_stats'), ('vw_daily_sales')
) AS expected(name)
ORDER BY 2 DESC, 1;

\echo '== Indexes =='
SELECT expected.name AS index_name,
       CASE WHEN i.indexname IS NULL THEN 'MISSING' ELSE 'ok' END AS state
FROM (VALUES
    ('ix_users_email'), ('uq_users_email_lower'), ('ix_plans_active_order'),
    ('uq_plans_single_most_popular'), ('ix_accounts_user_id'), ('ix_accounts_user_created'),
    ('ix_accounts_plan_id'), ('ix_orders_reference'), ('ix_orders_user_id'),
    ('ix_orders_user_created'), ('ix_orders_plan_id'), ('uq_orders_account_id'),
    ('ix_payouts_account_id'), ('ix_payouts_account_date'), ('ix_payouts_paid_amount'),
    ('ix_contact_messages_email'), ('ix_contact_messages_created'),
    ('ix_contact_messages_unhandled')
) AS expected(name)
LEFT JOIN pg_indexes i ON i.indexname = expected.name AND i.schemaname = 'public'
ORDER BY 2 DESC, 1;

\echo '== Foreign keys =='
SELECT conname, conrelid::regclass AS on_table, confrelid::regclass AS references_table,
       CASE confdeltype WHEN 'c' THEN 'CASCADE' WHEN 'n' THEN 'SET NULL' WHEN 'a' THEN 'NO ACTION'
                        WHEN 'r' THEN 'RESTRICT' ELSE confdeltype::text END AS on_delete
FROM pg_constraint
WHERE contype = 'f' AND connamespace = 'public'::regnamespace
ORDER BY 2, 1;

\echo '== Check constraints =='
SELECT conrelid::regclass AS on_table, count(*) AS check_constraints
FROM pg_constraint
WHERE contype = 'c' AND connamespace = 'public'::regnamespace
GROUP BY 1
ORDER BY 1;

\echo '== Seeded plans =='
SELECT id, account_size, original_price, price, profit_split, most_popular, is_active
FROM plans
ORDER BY sort_order;

\echo '== Row counts =='
SELECT 'users' AS table_name, count(*) FROM users
UNION ALL SELECT 'plans', count(*) FROM plans
UNION ALL SELECT 'accounts', count(*) FROM accounts
UNION ALL SELECT 'orders', count(*) FROM orders
UNION ALL SELECT 'payouts', count(*) FROM payouts
UNION ALL SELECT 'contact_messages', count(*) FROM contact_messages
ORDER BY 1;

\echo '== Stats view =='
SELECT * FROM vw_platform_stats;

-- Fail loudly if anything above was missing.
DO $$
DECLARE
    missing text[] := '{}';
    expected_table text;
    expected_view text;
    expected_index text;
BEGIN
    FOREACH expected_table IN ARRAY ARRAY['users', 'plans', 'accounts', 'orders', 'payouts', 'contact_messages']
    LOOP
        IF to_regclass('public.' || expected_table) IS NULL THEN
            missing := missing || ('table ' || expected_table);
        END IF;
    END LOOP;

    FOREACH expected_view IN ARRAY ARRAY['vw_account_overview', 'vw_platform_stats', 'vw_daily_sales']
    LOOP
        IF to_regclass('public.' || expected_view) IS NULL THEN
            missing := missing || ('view ' || expected_view);
        END IF;
    END LOOP;

    FOREACH expected_index IN ARRAY ARRAY['ix_users_email', 'uq_users_email_lower', 'ix_accounts_user_created',
                                          'ix_orders_reference', 'ix_payouts_account_date']
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = expected_index) THEN
            missing := missing || ('index ' || expected_index);
        END IF;
    END LOOP;

    IF (SELECT count(*) FROM plans WHERE is_active) < 3 THEN
        missing := missing || 'seed: fewer than 3 active plans';
    END IF;

    IF array_length(missing, 1) > 0 THEN
        RAISE EXCEPTION 'Schema verification failed: %', array_to_string(missing, ', ');
    END IF;

    RAISE NOTICE 'Schema verification passed.';
END
$$;
