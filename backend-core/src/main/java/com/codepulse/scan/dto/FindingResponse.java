package com.codepulse.scan.dto;

import java.time.Instant;
import java.util.UUID;

import com.codepulse.scan.domain.FindingEntity;

public record FindingResponse(
        UUID id,
        UUID scanId,
        String ruleId,
        String category,
        String severity,
        String title,
        String description,
        String filePath,
        Integer lineNumber,
        String codeSnippet,
        String recommendation,
        Instant createdAt) {

    public static FindingResponse from(FindingEntity finding) {
        return new FindingResponse(
                finding.getId(),
                finding.getScan().getId(),
                finding.getRuleId(),
                finding.getCategory(),
                finding.getSeverity(),
                finding.getTitle(),
                finding.getDescription(),
                finding.getFilePath(),
                finding.getLineNumber(),
                finding.getCodeSnippet(),
                finding.getRecommendation(),
                finding.getCreatedAt());
    }
}
