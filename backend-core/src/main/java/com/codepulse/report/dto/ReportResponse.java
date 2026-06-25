package com.codepulse.report.dto;

import java.time.Instant;
import java.util.UUID;

import com.codepulse.report.domain.ReportEntity;

public record ReportResponse(
        UUID id,
        UUID scanId,
        UUID repositoryId,
        String repositoryFullName,
        String fileName,
        String contentType,
        Long sizeBytes,
        Instant createdAt) {

    public static ReportResponse from(ReportEntity report) {
        return new ReportResponse(
                report.getId(),
                report.getScan().getId(),
                report.getScan().getRepository().getId(),
                report.getScan().getRepository().getGithubOwner() + "/" + report.getScan().getRepository().getGithubName(),
                report.getFileName(),
                report.getContentType(),
                report.getSizeBytes(),
                report.getCreatedAt());
    }
}
