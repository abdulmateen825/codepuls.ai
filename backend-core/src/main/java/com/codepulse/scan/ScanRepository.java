package com.codepulse.scan;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.scan.domain.ScanEntity;

public interface ScanRepository extends JpaRepository<ScanEntity, UUID> {

    List<ScanEntity> findAllByRepositoryOrderByCreatedAtDesc(RepositoryEntity repository);

    @Query("""
            select count(scan)
            from ScanEntity scan
            where scan.repository.owner.id = :ownerId
            """)
    long countByRepositoryOwnerId(UUID ownerId);
}
