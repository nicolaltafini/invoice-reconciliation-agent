package it.nicolaltafini.reconciliation.order;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import it.nicolaltafini.reconciliation.supplier.Supplier;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;

@Entity
@Table(name = "purchase_order")
public class PurchaseOrder {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "order_number", nullable = false, unique = true, length = 50)
    private String orderNumber;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "supplier_id")
    private Supplier supplier;

    @Column(name = "order_date", nullable = false)
    private LocalDate orderDate;

    @OneToMany(mappedBy = "purchaseOrder", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("lineNumber")
    private List<PurchaseOrderLine> lines = new ArrayList<>();

    protected PurchaseOrder() {
    }

    public PurchaseOrder(String orderNumber, Supplier supplier, LocalDate orderDate) {
        this.orderNumber = orderNumber;
        this.supplier = supplier;
        this.orderDate = orderDate;
    }

    public PurchaseOrderLine addLine(String itemCode, String description,
                                     BigDecimal quantity, BigDecimal unitPrice) {
        PurchaseOrderLine line = new PurchaseOrderLine(
                this, lines.size() + 1, itemCode, description, quantity, unitPrice);
        lines.add(line);
        return line;
    }

    public Long getId() { return id; }
    public String getOrderNumber() { return orderNumber; }
    public Supplier getSupplier() { return supplier; }
    public LocalDate getOrderDate() { return orderDate; }
    public List<PurchaseOrderLine> getLines() { return Collections.unmodifiableList(lines); }
}