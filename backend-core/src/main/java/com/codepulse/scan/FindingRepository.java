package com.codepulse.scan;

import java.util.UUID;
import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.codepulse.scan.domain.FindingEntity;
import com.codepulse.scan.domain.ScanEntity;

public interface FindingRepository extends JpaRepository<FindingEntity, UUID> {

    void deleteByScan(ScanEntity scan);

    List<FindingEntity> findAllByScanOrderByCreatedAtDesc(ScanEntity scan);

    @Query("""
            select finding
            from FindingEntity finding
            where finding.scan = :scan
              and (:severity is null or lower(finding.severity) = lower(:severity))
              and (:category is null or lower(finding.category) = lower(:category))
              and (:ruleId is null or lower(finding.ruleId) = lower(:ruleId))
              and (:smellType is null or lower(finding.smellType) = lower(:smellType))
              and (:language is null or lower(finding.language) = lower(:language))
              and (:filePath is null or lower(finding.filePath) like lower(concat('%', :filePath, '%')))
            order by finding.createdAt desc
            """)
    Page<FindingEntity> findByScanWithFilters(
            ScanEntity scan,
            String severity,
            String category,
            String ruleId,
            String smellType,
            String language,
            String filePath,
            Pageable pageable);
}
