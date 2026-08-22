-- ApexFund — optional demo data (NOT applied by default)
--
--   psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/optional_demo_data.sql
--
-- Creates one trader with a funded account, payout history, a receipt and a
-- contact message, so the dashboard has something to render without going
-- through checkout.
--
--   email:    demo@apexfund.test
--   password: demo1234
--
-- Never load this into anything but a local or throwaway database: the
-- credentials are published in this file.
--
-- Safe to re-run; existing rows are left alone.

BEGIN;

-- The hash below is PBKDF2-SHA256 of 'demo1234', in the format
-- app/security.py produces and verifies.
INSERT INTO users (name, email, password_hash, is_active, created_at)
VALUES (
    'Demo Trader',
    'demo@apexfund.test',
    'pbkdf2_sha256$260000$88b5b72803a874eeb37a0fc19f191730$5e2aeb8c10102d7c3f0dca7a459c689cd4fdd1734025a7e3be9673694c8cb688',
    true,
    now() - interval '45 days'
)
ON CONFLICT (email) DO NOTHING;

-- One account on the most popular plan, opened 40 days ago.
INSERT INTO accounts (user_id, plan_id, eval_label, account_size, profit_split, phase, status, balance, created_at)
SELECT u.id, p.id, p.eval_label, p.account_size, p.profit_split, 'Step 1', 'active', p.account_size, now() - interval '40 days'
FROM users u
CROSS JOIN plans p
WHERE u.email = 'demo@apexfund.test'
  AND p.id = 'two-step-20000'
  AND NOT EXISTS (
      SELECT 1 FROM accounts a WHERE a.user_id = u.id AND a.plan_id = p.id
  );

-- Payout history: 6% and 4% paid, 5% still processing. Matches the schedule in
-- app/services.py (DEMO_PAYOUT_SCHEDULE).
INSERT INTO payouts (account_id, payout_date, amount, status)
SELECT a.id, (a.created_at - interval '30 days')::date, round(a.account_size * 0.06, 2), 'paid'
FROM accounts a
JOIN users u ON u.id = a.user_id
WHERE u.email = 'demo@apexfund.test'
ON CONFLICT (account_id, payout_date) DO NOTHING;

INSERT INTO payouts (account_id, payout_date, amount, status)
SELECT a.id, (a.created_at - interval '14 days')::date, round(a.account_size * 0.04, 2), 'paid'
FROM accounts a
JOIN users u ON u.id = a.user_id
WHERE u.email = 'demo@apexfund.test'
ON CONFLICT (account_id, payout_date) DO NOTHING;

INSERT INTO payouts (account_id, payout_date, amount, status)
SELECT a.id, a.created_at::date, round(a.account_size * 0.05, 2), 'processing'
FROM accounts a
JOIN users u ON u.id = a.user_id
WHERE u.email = 'demo@apexfund.test'
ON CONFLICT (account_id, payout_date) DO NOTHING;

-- The receipt for that purchase.
INSERT INTO orders (reference, user_id, plan_id, account_id, full_name, email, amount, currency, status, card_last4, agreed_rules, created_at)
SELECT 'AF-DEMO00000001', u.id, a.plan_id, a.id, 'Demo Trader', u.email, p.price, 'INR', 'paid', '4242', true, a.created_at
FROM accounts a
JOIN users u ON u.id = a.user_id
JOIN plans p ON p.id = a.plan_id
WHERE u.email = 'demo@apexfund.test'
ON CONFLICT (reference) DO NOTHING;

INSERT INTO contact_messages (name, mobile, email, message, is_handled, created_at)
SELECT 'Demo Trader', '+91 90000 00000', 'demo@apexfund.test',
       'How long do payouts usually take after I hit the minimum?', false, now() - interval '3 days'
WHERE NOT EXISTS (
    SELECT 1 FROM contact_messages WHERE email = 'demo@apexfund.test'
);

COMMIT;

\echo 'Demo data loaded. Log in as demo@apexfund.test / demo1234'
