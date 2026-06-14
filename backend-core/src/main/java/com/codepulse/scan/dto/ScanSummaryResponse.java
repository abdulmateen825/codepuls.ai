package com.codepulse.scan.dto;

import java.time.Instant;
import java.util.UUID;

import com.codepulse.scan.domain.ScanEntity;

public record ScanSummaryResponse(
        UUID id,
        UUID repositoryId,
        String repositoryFullName,
        String status,
        Integer qualityScore,
        Integer securityScore,
        Integer maintainabilityScore,
        Instant startedAt,
        Instant completedAt,
        Instant createdAt) {

    public static ScanSummaryResponse from(ScanEntity scan) {
        return new ScanSummaryResponse(
                scan.getId(),
                scan.getRepository().getId(),
                scan.getRepository().getGithubOwner() + "/" + scan.getRepository().getGithubName(),
                scan.getStatus().name(),
                scan.getQualityScore(),
                scan.getSecurityScore(),
                scan.getMaintainabilityScore(),
                scan.getStartedAt(),
                scan.getCompletedAt(),
                scan.getCreatedAt());
    }
}
