package com.codepulse.scan.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

public record ScanResultFindingRequest(
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

        @NotBlank
        @Size(max = 120)
        String toolName,

        @Size(max = 4000)
        String codeSnippet) {

    public String normalizedRuleId() {
        return toolName.trim() + ":" + title.trim();
    }

    public Integer normalizedLineNumber() {
        return lineNumber == null ? null : Math.max(1, lineNumber);
    }
}
