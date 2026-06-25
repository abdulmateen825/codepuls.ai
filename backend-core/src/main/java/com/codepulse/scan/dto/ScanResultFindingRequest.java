package com.codepulse.scan.dto;

import java.util.Map;
import java.util.Set;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public record ScanResultFindingRequest(
        @Size(max = 120)
        String ruleId,

        @NotBlank
        @Size(max = 30)
        String severity,

        @NotBlank
        @Size(max = 50)
        String category,

        @NotBlank
        @Size(max = 300)
        String title,

        @NotBlank
        @Size(max = 2000)
        String description,

        @Size(max = 2000)
        String recommendation,

        @NotBlank
        @Size(max = 1000)
        String filePath,

        @Positive
        Integer lineNumber,

        @Positive
        Integer startLine,

        @Positive
        Integer endLine,

        @Size(max = 80)
        String smellType,

        @Size(max = 40)
        String language,

        Map<String, Object> evidence,

        Map<String, Object> metrics,

        @NotBlank
        @Size(max = 120)
        String toolName,

        @Size(max = 4000)
        String codeSnippet,

        @Size(max = 4000)
        String contextBefore,

        @Size(max = 4000)
        String contextAfter,

        @Size(max = 2000)
        String suggestedRefactoring,

        @DecimalMin("0.0")
        @DecimalMax("1.0")
        Double confidence) {

    private static final Set<String> ALLOWED_SMELL_TYPES = Set.of(
            "LONG_METHOD",
            "LARGE_CLASS",
            "HIGH_CYCLOMATIC_COMPLEXITY",
            "DEEP_NESTING",
            "LONG_PARAMETER_LIST",
            "DUPLICATED_CODE",
            "DEAD_CODE",
            "GOD_OBJECT");

    public ScanResultFindingRequest(
            String severity,
            String category,
            String title,
            String description,
            String recommendation,
            String filePath,
            Integer lineNumber,
            String toolName,
            String codeSnippet) {
        this(
                null,
                severity,
                category,
                title,
                description,
                recommendation,
                filePath,
                lineNumber,
                null,
                null,
                null,
                null,
                null,
                null,
                toolName,
                codeSnippet,
                null,
                null,
                null,
                null);
    }

    public String normalizedRuleId() {
        if (ruleId != null && !ruleId.isBlank()) {
            return ruleId.trim();
        }
        return toolName.trim() + ":" + title.trim();
    }

    public Integer normalizedLineNumber() {
        return lineNumber == null ? null : Math.max(1, lineNumber);
    }

    public Integer normalizedStartLine() {
        return startLine == null ? normalizedLineNumber() : Math.max(1, startLine);
    }

    public Integer normalizedEndLine() {
        Integer start = normalizedStartLine();
        if (endLine == null) {
            return start;
        }
        return Math.max(start == null ? 1 : start, endLine);
    }

    @AssertTrue(message = "Unknown smell type.")
    public boolean isKnownSmellType() {
        return smellType == null || smellType.isBlank() || ALLOWED_SMELL_TYPES.contains(smellType.trim());
    }
}
