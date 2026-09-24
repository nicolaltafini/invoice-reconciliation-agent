INSERT INTO supplier (vat_number, name) VALUES
    ('01111111111', 'Ferramenta Adige Srl'),
    ('02222222222', 'Imballaggi Veneto Spa'),
    ('03333333333', 'Elettroforniture Mincio Srl')
ON CONFLICT (vat_number) DO NOTHING;

INSERT INTO purchase_order (order_number, supplier_id, order_date)
SELECT v.order_number, s.id, v.order_date::date
FROM (VALUES
    ('PO-2026-001', '01111111111', '2026-09-01'),
    ('PO-2026-002', '02222222222', '2026-09-03'),
    ('PO-2026-003', '03333333333', '2026-09-05'),
    ('PO-2026-004', '01111111111', '2026-09-10')
) AS v(order_number, vat_number, order_date)
JOIN supplier s ON s.vat_number = v.vat_number
ON CONFLICT (order_number) DO NOTHING;

INSERT INTO purchase_order_line (purchase_order_id, line_number, item_code, description, quantity, unit_price)
SELECT po.id, v.line_number, v.item_code, v.description, v.quantity, v.unit_price
FROM (VALUES
    ('PO-2026-001', 1, 'VIT-M8-50', 'Viti M8x50 zincate',            1000, 0.0850),
    ('PO-2026-001', 2, 'DAD-M8',    'Dadi M8 zincati',               1000, 0.0320),
    ('PO-2026-001', 3, 'RON-M8',    'Rondelle M8',                   1000, 0.0150),
    ('PO-2026-002', 1, 'SCA-403030','Scatole cartone 40x30x30',       500, 0.9500),
    ('PO-2026-002', 2, 'NAS-50',    'Nastro adesivo 50mm',            120, 1.8000),
    ('PO-2026-003', 1, 'CAV-3G15',  'Cavo 3G1,5 al metro',            200, 0.7400),
    ('PO-2026-003', 2, 'INT-16A',   'Interruttore magnetotermico 16A', 25, 12.5000),
    ('PO-2026-003', 3, 'QUA-12M',   'Quadro elettrico 12 moduli',       5, 38.0000),
    ('PO-2026-004', 1, 'VIT-M6-30', 'Viti M6x30 inox',               2000, 0.0610),
    ('PO-2026-004', 2, 'TAS-8',     'Tasselli nylon 8mm',            1500, 0.0420)
) AS v(order_number, line_number, item_code, description, quantity, unit_price)
JOIN purchase_order po ON po.order_number = v.order_number
ON CONFLICT (purchase_order_id, line_number) DO NOTHING;