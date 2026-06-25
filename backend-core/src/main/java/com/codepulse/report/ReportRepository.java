package com.codepulse.report;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

import com.codepulse.report.domain.ReportEntity;

public interface ReportRepository extends JpaRepository<ReportEntity, UUID> {

    List<ReportEntity> findAllByScanRepositoryOwnerIdOrderByCreatedAtDesc(UUID ownerId);
}
