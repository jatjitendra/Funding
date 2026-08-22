-- ApexFund — seed the challenge plans
--
-- These three rows are the source of truth the frontend used to hard-code in
-- js/data.js, and they must stay in step with PLAN_SEED in
-- backend_jitendra/app/seed.py.
--
-- Upserts rather than inserts, so re-running realigns any drifted row without
-- touching the accounts that reference it.

BEGIN;

INSERT INTO plans (
    id, eval_label, eval_steps, account_size,
    original_price, price, profit_split,
    phase1_profit_pct, phase2_profit_pct,
    max_daily_loss_pct, max_total_loss_pct,
    most_popular, is_active, sort_order
)
VALUES
    ('two-step-10000', 'Two-Step Evaluation', 2, 10000, 499, 399, 80, 8, 12, 5, 10, false, true, 1),
    ('two-step-20000', 'Two-Step Evaluation', 2, 20000, 799, 699, 80, 8, 12, 5, 10, true,  true, 2),
    ('two-step-40000', 'Two-Step Evaluation', 2, 40000, 999, 899, 80, 8, 12, 5, 10, false, true, 3)
ON CONFLICT (id) DO UPDATE SET
    eval_label         = EXCLUDED.eval_label,
    eval_steps         = EXCLUDED.eval_steps,
    account_size       = EXCLUDED.account_size,
    original_price     = EXCLUDED.original_price,
    price              = EXCLUDED.price,
    profit_split       = EXCLUDED.profit_split,
    phase1_profit_pct  = EXCLUDED.phase1_profit_pct,
    phase2_profit_pct  = EXCLUDED.phase2_profit_pct,
    max_daily_loss_pct = EXCLUDED.max_daily_loss_pct,
    max_total_loss_pct = EXCLUDED.max_total_loss_pct,
    most_popular       = EXCLUDED.most_popular,
    is_active          = EXCLUDED.is_active,
    sort_order         = EXCLUDED.sort_order;

COMMIT;
