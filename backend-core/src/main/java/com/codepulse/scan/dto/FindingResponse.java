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
        Integer startLine,
        Integer endLine,
        String smellType,
        String language,
        String evidenceJson,
        String metricsJson,
        String codeSnippet,
        String contextBefore,
        String contextAfter,
        String recommendation,
        String suggestedRefactoring,
        Double confidence,
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
                finding.getStartLine(),
                finding.getEndLine(),
                finding.getSmellType(),
                finding.getLanguage(),
                finding.getEvidenceJson(),
                finding.getMetricsJson(),
                finding.getCodeSnippet(),
                finding.getContextBefore(),
                finding.getContextAfter(),
                finding.getRecommendation(),
                finding.getSuggestedRefactoring(),
                finding.getConfidence(),
                finding.getCreatedAt());
    }
}
