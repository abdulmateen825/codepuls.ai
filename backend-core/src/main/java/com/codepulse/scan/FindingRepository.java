package com.codepulse.scan;

import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.codepulse.scan.domain.FindingEntity;
import com.codepulse.scan.domain.ScanEntity;

public interface FindingRepository extends JpaRepository<FindingEntity, UUID> {

    void deleteByScan(ScanEntity scan);

    @Query("""
            select finding
            from FindingEntity finding
            where finding.scan = :scan
              and (:severity is null or lower(finding.severity) = lower(:severity))
              and (:category is null or lower(finding.category) = lower(:category))
            order by finding.createdAt desc
            """)
    Page<FindingEntity> findByScanWithFilters(
            ScanEntity scan,
            String severity,
            String category,
            Pageable pageable);
}
