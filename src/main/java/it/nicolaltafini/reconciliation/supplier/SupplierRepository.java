package it.nicolaltafini.reconciliation.supplier;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface SupplierRepository extends JpaRepository<Supplier, Long> {

    Optional<Supplier> findByVatNumber(String vatNumber);
}