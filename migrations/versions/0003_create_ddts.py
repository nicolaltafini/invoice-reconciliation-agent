"""create ddts"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE ddt (
            id                BIGSERIAL PRIMARY KEY,
            supplier_id       BIGINT        NOT NULL REFERENCES supplier(id),
            ddt_number        VARCHAR(50)   NOT NULL,
            ddt_date          DATE          NOT NULL,
            order_number      VARCHAR(50),
            source_filename   VARCHAR(255)  NOT NULL,
            extraction_model  VARCHAR(100)  NOT NULL,
            input_tokens      INT           NOT NULL,
            output_tokens     INT           NOT NULL,
            received_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
            UNIQUE (supplier_id, ddt_number)
        )
    """)
    op.execute("""
        CREATE TABLE ddt_line (
            id           BIGSERIAL PRIMARY KEY,
            ddt_id       BIGINT         NOT NULL REFERENCES ddt(id) ON DELETE CASCADE,
            line_number  INT            NOT NULL,
            item_code    VARCHAR(50),
            description  VARCHAR(1000)  NOT NULL,
            quantity     NUMERIC(18,8)  NOT NULL,
            unit         VARCHAR(10),
            UNIQUE (ddt_id, line_number)
        )
    """)


def downgrade() -> None:
    op.drop_table("ddt_line")
    op.drop_table("ddt")