"""create invoices"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE invoice (
            id               BIGSERIAL PRIMARY KEY,
            supplier_id      BIGINT        NOT NULL REFERENCES supplier(id),
            invoice_number   VARCHAR(50)   NOT NULL,
            invoice_date     DATE          NOT NULL,
            total_amount     NUMERIC(14,2),
            order_number     VARCHAR(50),
            ddt_number       VARCHAR(50),
            source_filename  VARCHAR(255)  NOT NULL,
            received_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),
            UNIQUE (supplier_id, invoice_number)
        )
    """)
    op.execute("""
        CREATE TABLE invoice_line (
            id           BIGSERIAL PRIMARY KEY,
            invoice_id   BIGINT         NOT NULL REFERENCES invoice(id) ON DELETE CASCADE,
            line_number  INT            NOT NULL,
            item_code    VARCHAR(50),
            description  VARCHAR(1000)  NOT NULL,
            quantity     NUMERIC(18,8)  NOT NULL,
            unit_price   NUMERIC(18,8)  NOT NULL,
            line_total   NUMERIC(14,2)  NOT NULL,
            UNIQUE (invoice_id, line_number)
        )
    """)


def downgrade() -> None:
    op.drop_table("invoice_line")
    op.drop_table("invoice")