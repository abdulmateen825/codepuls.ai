package com.codepulse.scan.dto;

import java.time.Instant;
import java.util.UUID;

import com.codepulse.scan.domain.ScanEntity;

public record ScanDetailResponse(
        UUID id,
        UUID repositoryId,
        String repositoryUrl,
        String repositoryFullName,
        String status,
        Integer qualityScore,
        Integer securityScore,
        Integer maintainabilityScore,
        Instant startedAt,
        Instant completedAt,
        String errorMessage,
        Instant createdAt,
        Instant updatedAt) {

    public static ScanDetailResponse from(ScanEntity scan) {
        return new ScanDetailResponse(
                scan.getId(),
                scan.getRepository().getId(),
                scan.getRepository().getGithubUrl(),
                scan.getRepository().getGithubOwner() + "/" + scan.getRepository().getGithubName(),
                scan.getStatus().name(),
                scan.getQualityScore(),
                scan.getSecurityScore(),
                scan.getMaintainabilityScore(),
                scan.getStartedAt(),
                scan.getCompletedAt(),
                scan.getErrorMessage(),
                scan.getCreatedAt(),
                scan.getUpdatedAt());
    }
}
