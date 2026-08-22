-- ApexFund — indexes
--
-- The ix_* names match what SQLAlchemy generates for `index=True` columns, so
-- Alembic autogenerate will not see spurious differences.
--
-- Safe to re-run.

BEGIN;

-- users -----------------------------------------------------------------------

-- users.email is declared unique + indexed in the model, which SQLAlchemy
-- expresses as a single unique index rather than a separate constraint.
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

-- The API compares emails with lower(), and the frontend lowercases on signup.
-- Without this, two rows differing only in case could both be inserted by
-- concurrent requests, since the application's "does this email exist?" check
-- and its INSERT are not atomic. The API turns the resulting unique violation
-- into a 409.
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower ON users (lower(email));

-- plans -----------------------------------------------------------------------

-- Covers the pricing page's "active plans in display order" query.
CREATE INDEX IF NOT EXISTS ix_plans_active_order ON plans (sort_order, account_size)
    WHERE is_active;

-- At most one plan may carry the "Most Popular" badge on the pricing table.
CREATE UNIQUE INDEX IF NOT EXISTS uq_plans_single_most_popular ON plans (most_popular)
    WHERE most_popular;

-- accounts --------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_accounts_user_id ON accounts (user_id);

-- GET /api/accounts/latest orders by created_at desc for one user; this serves
-- both that lookup and the plain per-user listing.
CREATE INDEX IF NOT EXISTS ix_accounts_user_created ON accounts (user_id, created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS ix_accounts_plan_id ON accounts (plan_id);

-- orders ----------------------------------------------------------------------

CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_reference ON orders (reference);
CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id);
CREATE INDEX IF NOT EXISTS ix_orders_user_created ON orders (user_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS ix_orders_plan_id ON orders (plan_id);

-- Unenforced by FK: at most one order should own a given account.
CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_account_id ON orders (account_id)
    WHERE account_id IS NOT NULL;

-- payouts ---------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_payouts_account_id ON payouts (account_id);

-- Matches the payout history ordering, and the stats view's sum over paid rows.
CREATE INDEX IF NOT EXISTS ix_payouts_account_date ON payouts (account_id, payout_date, id);
CREATE INDEX IF NOT EXISTS ix_payouts_paid_amount ON payouts (amount)
    WHERE status = 'paid';

-- contact_messages ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_contact_messages_email ON contact_messages (email);

-- The inbox lists newest first.
CREATE INDEX IF NOT EXISTS ix_contact_messages_created ON contact_messages (created_at DESC, id DESC);

-- Unhandled messages are the working queue and stay a small slice of the table.
CREATE INDEX IF NOT EXISTS ix_contact_messages_unhandled ON contact_messages (created_at DESC)
    WHERE NOT is_handled;

COMMIT;
