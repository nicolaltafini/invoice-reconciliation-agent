"""invoice approval status and audit log"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE invoice
            ADD COLUMN approval_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            ADD COLUMN decision_note   VARCHAR(500),
            ADD COLUMN decided_by      VARCHAR(100),
            ADD COLUMN decided_at      TIMESTAMPTZ,
            ADD CONSTRAINT invoice_approval_status_check
                CHECK (approval_status IN ('PENDING', 'APPROVED', 'BLOCKED'))
    """)
    op.execute("""
        CREATE TABLE audit_log (
            id           BIGSERIAL PRIMARY KEY,
            occurred_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),
            actor        VARCHAR(100)  NOT NULL,
            role         VARCHAR(20)   NOT NULL,
            action       VARCHAR(50)   NOT NULL,
            invoice_id   BIGINT        REFERENCES invoice(id),
            detail       VARCHAR(1000)
        )
    """)


def downgrade() -> None:
    op.drop_table("audit_log")
    op.execute("""
        ALTER TABLE invoice
            DROP CONSTRAINT invoice_approval_status_check,
            DROP COLUMN decided_at,
            DROP COLUMN decided_by,
            DROP COLUMN decision_note,
            DROP COLUMN approval_status
    """)