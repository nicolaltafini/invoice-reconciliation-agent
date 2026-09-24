CREATE TABLE supplier (
    id          BIGSERIAL PRIMARY KEY,
    vat_number  VARCHAR(20)  NOT NULL UNIQUE,
    name        VARCHAR(255) NOT NULL
);

CREATE TABLE purchase_order (
    id            BIGSERIAL PRIMARY KEY,
    order_number  VARCHAR(50) NOT NULL UNIQUE,
    supplier_id   BIGINT      NOT NULL REFERENCES supplier(id),
    order_date    DATE        NOT NULL
);

CREATE TABLE purchase_order_line (
    id                 BIGSERIAL PRIMARY KEY,
    purchase_order_id  BIGINT         NOT NULL REFERENCES purchase_order(id) ON DELETE CASCADE,
    line_number        INT            NOT NULL,
    item_code          VARCHAR(50)    NOT NULL,
    description        VARCHAR(255)   NOT NULL,
    quantity           NUMERIC(12,3)  NOT NULL,
    unit_price         NUMERIC(12,4)  NOT NULL,
    UNIQUE (purchase_order_id, line_number)
);