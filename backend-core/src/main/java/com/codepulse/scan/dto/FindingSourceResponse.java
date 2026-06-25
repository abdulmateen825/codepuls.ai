package com.codepulse.scan.dto;

import java.util.UUID;

import com.codepulse.scan.domain.FindingEntity;

public record FindingSourceResponse(
        UUID findingId,
        String filePath,
        Integer startLine,
        Integer endLine,
        String codeSnippet,
        String contextBefore,
        String contextAfter) {

    public static FindingSourceResponse from(FindingEntity finding) {
        return new FindingSourceResponse(
                finding.getId(),
                finding.getFilePath(),
                finding.getStartLine() == null ? finding.getLineNumber() : finding.getStartLine(),
                finding.getEndLine() == null ? finding.getLineNumber() : finding.getEndLine(),
                finding.getCodeSnippet(),
                finding.getContextBefore(),
                finding.getContextAfter());
    }
}
