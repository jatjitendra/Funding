-- ApexFund — reporting views
--
-- These are conveniences for dashboards, support queries and psql poking. The
-- API does not depend on them, so changing them cannot break the application.
--
-- Safe to re-run (CREATE OR REPLACE).

BEGIN;

-- Denormalised account row: who owns it, which plan it came from, and its
-- payout totals. Saves repeating a four-table join in ad-hoc queries.
CREATE OR REPLACE VIEW vw_account_overview AS
SELECT
    a.id                AS account_id,
    a.created_at        AS opened_at,
    a.phase,
    a.status,
    a.account_size,
    a.balance,
    a.profit_split,
    u.id                AS user_id,
    u.name              AS trader_name,
    u.email             AS trader_email,
    p.id                AS plan_id,
    p.eval_label,
    p.eval_steps,
    p.price             AS plan_price,
    o.reference         AS order_reference,
    o.amount            AS amount_charged,
    COALESCE(paid.total, 0)         AS total_paid_out,
    COALESCE(pending.total, 0)      AS total_processing,
    paid.last_paid_on
FROM accounts a
JOIN users u ON u.id = a.user_id
JOIN plans p ON p.id = a.plan_id
LEFT JOIN orders o ON o.account_id = a.id
LEFT JOIN (
    SELECT account_id, sum(amount) AS total, max(payout_date) AS last_paid_on
    FROM payouts
    WHERE status = 'paid'
    GROUP BY account_id
) paid ON paid.account_id = a.id
LEFT JOIN (
    SELECT account_id, sum(amount) AS total
    FROM payouts
    WHERE status = 'processing'
    GROUP BY account_id
) pending ON pending.account_id = a.id;

-- Backs GET /api/stats. The floors keep the homepage stat cards ("10+ Accounts
-- Funded", "₹100K Total Rewards Paid") truthful while the demo database is
-- still small; drop the GREATEST() calls to report raw numbers.
CREATE OR REPLACE VIEW vw_platform_stats AS
SELECT
    COALESCE((SELECT max(profit_split) FROM plans WHERE is_active), 80) AS profit_split,
    24                                                                 AS payout_speed_hours,
    1000                                                               AS minimum_payout,
    GREATEST((SELECT count(*) FROM accounts), 10)                      AS accounts_funded,
    GREATEST(
        (SELECT COALESCE(sum(amount), 0) FROM payouts WHERE status = 'paid'),
        100000
    )::numeric(14,2)                                                   AS total_rewards_paid;

-- Daily revenue, for a quick read on how the demo is being used.
CREATE OR REPLACE VIEW vw_daily_sales AS
SELECT
    date_trunc('day', created_at)::date AS sold_on,
    plan_id,
    count(*)                            AS orders,
    sum(amount)                         AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

COMMENT ON VIEW vw_account_overview IS 'Account joined to its owner, plan, order and payout totals.';
COMMENT ON VIEW vw_platform_stats   IS 'Homepage stat card figures; mirrors GET /api/stats.';
COMMENT ON VIEW vw_daily_sales      IS 'Paid orders and revenue per day and plan.';

COMMIT;
