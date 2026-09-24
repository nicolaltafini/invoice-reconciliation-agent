package it.nicolaltafini.reconciliation.supplier;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "supplier")
public class Supplier {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "vat_number", nullable = false, unique = true, length = 20)
    private String vatNumber;

    @Column(nullable = false)
    private String name;

    protected Supplier() {
    }

    public Supplier(String vatNumber, String name) {
        this.vatNumber = vatNumber;
        this.name = name;
    }

    public Long getId() { return id; }
    public String getVatNumber() { return vatNumber; }
    public String getName() { return name; }
}